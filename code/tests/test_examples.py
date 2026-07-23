from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from evaluation_gate import (  # noqa: E402
    EvalResult,
    GateConfig,
    ReleaseStatus,
    evaluate,
)
from enterprise_ai_pipeline import (  # noqa: E402
    EnterpriseAIPipeline,
    InsufficientEvidence,
    RequestEnvelope,
    demo_pipeline,
)
from idempotent_workflow import (  # noqa: E402
    ApprovalContext,
    ApprovalMismatch,
    IdempotencyConflict,
    OutcomeUnknown,
    Status,
    WorkflowStore,
)
from model_router import (  # noqa: E402
    Channel,
    DataClass,
    NoAllowedRoute,
    RouteRequest,
    route,
)
from permission_rag import Document, UserContext, retrieve  # noqa: E402


class RouterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.channels = [
            Channel(
                "cloud",
                DataClass.INTERNAL,
                frozenset({"writing"}),
                cost_rank=1,
                latency_rank=1,
            ),
            Channel(
                "local",
                DataClass.HIGHLY_SENSITIVE,
                frozenset({"writing", "summary"}),
                cost_rank=2,
                latency_rank=2,
            ),
        ]

    def test_sensitive_data_uses_local(self) -> None:
        decision = route(
            RouteRequest("proposal", DataClass.SENSITIVE, "writing"),
            self.channels,
        )
        self.assertEqual(decision.channel, "local")

    def test_no_route_is_blocked(self) -> None:
        with self.assertRaises(NoAllowedRoute):
            route(
                RouteRequest("vision", DataClass.SENSITIVE, "vision"),
                self.channels,
            )


class RetrievalTests(unittest.TestCase):
    def test_unauthorized_document_is_filtered(self) -> None:
        user = UserContext("u1", "sales", frozenset({"p1"}))
        documents = [
            Document("allowed", "项目风险", "项目风险复盘", "project", project_ids=frozenset({"p1"})),
            Document("denied", "合同风险", "项目风险合同", "project", project_ids=frozenset({"p2"})),
        ]
        results = retrieve("项目风险", user, documents)
        self.assertEqual([item.doc_id for item in results], ["allowed"])

    def test_ineffective_document_is_filtered(self) -> None:
        user = UserContext("u1", "sales")
        documents = [Document("old", "旧政策", "折扣政策", effective=False)]
        self.assertEqual(retrieve("折扣政策", user, documents), [])


class WorkflowTests(unittest.TestCase):
    def test_prepare_is_idempotent(self) -> None:
        store = WorkflowStore()
        payload = {"business_object_id": "object-1", "content_version": "v1"}
        first = store.prepare("t1", "same-key", payload)
        second = store.prepare("t2", "same-key", dict(payload))
        self.assertIs(first, second)

    def test_conflicting_payload_is_rejected(self) -> None:
        store = WorkflowStore()
        store.prepare(
            "t1",
            "same-key",
            {"business_object_id": "object-1", "content_version": "v1"},
        )
        with self.assertRaises(IdempotencyConflict):
            store.prepare(
                "t2",
                "same-key",
                {"business_object_id": "object-1", "content_version": "v2"},
            )

    def test_execute_only_once(self) -> None:
        store = WorkflowStore()
        store.prepare(
            "t1",
            "same-key",
            {
                "business_object_id": "object-1",
                "content_version": "v1",
                "value": 1,
            },
        )
        calls: list[int] = []

        def action(payload: dict[str, int]) -> dict[str, int]:
            calls.append(payload["value"])
            return {"ok": 1}

        approval = ApprovalContext("owner", "object-1", "v1")
        first = store.approve_and_execute("same-key", approval, action)
        second = store.approve_and_execute("same-key", approval, action)
        self.assertEqual(first.status, Status.EXECUTED)
        self.assertIs(first, second)
        self.assertEqual(calls, [1])

    def test_approval_is_bound_to_content_version(self) -> None:
        store = WorkflowStore()
        store.prepare(
            "t1",
            "same-key",
            {"business_object_id": "object-1", "content_version": "v2"},
        )
        with self.assertRaises(ApprovalMismatch):
            store.approve_and_execute(
                "same-key",
                ApprovalContext("owner", "object-1", "v1"),
                lambda payload: {"ok": True},
            )

    def test_unknown_outcome_is_reconciled_before_retry(self) -> None:
        store = WorkflowStore()
        store.prepare(
            "t1",
            "same-key",
            {"business_object_id": "object-1", "content_version": "v1"},
        )

        def uncertain_action(payload: dict[str, object]) -> dict[str, object]:
            raise OutcomeUnknown("write timed out after the server accepted it")

        with self.assertRaises(OutcomeUnknown):
            store.approve_and_execute(
                "same-key",
                ApprovalContext("owner", "object-1", "v1"),
                uncertain_action,
            )
        self.assertEqual(store.get("same-key").status, Status.OUTCOME_UNKNOWN)

        reconciled = store.reconcile(
            "same-key",
            lambda payload: {"draft_id": "draft-1", "postcondition": "exists"},
        )
        self.assertEqual(reconciled.status, Status.EXECUTED)


class GateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = GateConfig(0.9, 1_500, 0.2)

    def test_blocker_overrides_average_score(self) -> None:
        decision = evaluate(
            [EvalResult("permission", 1.0, 100, 0.01, "unauthorized access")],
            self.config,
        )
        self.assertEqual(decision.status, ReleaseStatus.BLOCKED)

    def test_non_blocking_miss_is_conditional(self) -> None:
        decision = evaluate(
            [EvalResult("normal", 0.8, 100, 0.01)],
            self.config,
        )
        self.assertEqual(decision.status, ReleaseStatus.CONDITIONAL)

    def test_all_gates_pass(self) -> None:
        decision = evaluate(
            [EvalResult("normal", 0.95, 100, 0.01)],
            self.config,
        )
        self.assertEqual(decision.status, ReleaseStatus.PASS)

    def test_small_sample_p95_uses_nearest_rank(self) -> None:
        decision = evaluate(
            [
                EvalResult("fast", 0.95, 100, 0.01),
                EvalResult("slow", 0.95, 2_000, 0.01),
            ],
            self.config,
        )
        self.assertEqual(decision.status, ReleaseStatus.CONDITIONAL)
        self.assertIn("P95 latency above threshold", decision.reasons)


class IntegratedPipelineTests(unittest.TestCase):
    def test_pipeline_enforces_route_permission_approval_and_idempotency(self) -> None:
        pipeline = demo_pipeline()
        request = RequestEnvelope(
            task_id="proposal-1",
            idempotency_key="opportunity-1:proposal:v1",
            business_object_id="opportunity-1",
            actor=UserContext("u1", "sales", frozenset({"project-a"})),
            query="产品交付和项目风险",
            data_class=DataClass.SENSITIVE,
            required_capability="writing",
        )

        prepared = pipeline.prepare(request)
        repeated = pipeline.prepare(request)

        self.assertIs(prepared, repeated)
        self.assertEqual(prepared.route.channel, "local-service")
        self.assertIn("case-project-a", [item.doc_id for item in prepared.citations])
        self.assertNotIn("case-project-b", [item.doc_id for item in prepared.citations])
        self.assertEqual(prepared.task.status, Status.AWAITING_APPROVAL)

        calls: list[str] = []

        def writer(payload: dict[str, object]) -> dict[str, object]:
            calls.append(str(payload["business_object_id"]))
            return {"draft_id": "draft-1", "postcondition": "draft_exists"}

        first = pipeline.approve_and_commit(prepared, "manager", writer)
        second = pipeline.approve_and_commit(prepared, "manager", writer)

        self.assertIs(first, second)
        self.assertEqual(first.status, Status.EXECUTED)
        self.assertEqual(calls, ["opportunity-1"])
        self.assertEqual(
            [event.name for event in pipeline.audit(request.idempotency_key)],
            [
                "request.accepted",
                "route.selected",
                "knowledge.retrieved",
                "approval.prepared",
                "write.completed",
            ],
        )

    def test_pipeline_rejects_same_key_for_changed_request(self) -> None:
        pipeline = demo_pipeline()
        request = RequestEnvelope(
            task_id="proposal-1",
            idempotency_key="opportunity-1:proposal:v1",
            business_object_id="opportunity-1",
            actor=UserContext("u1", "sales", frozenset({"project-a"})),
            query="产品交付",
            data_class=DataClass.SENSITIVE,
            required_capability="writing",
        )
        pipeline.prepare(request)
        with self.assertRaises(IdempotencyConflict):
            pipeline.prepare(
                RequestEnvelope(
                    task_id="proposal-1",
                    idempotency_key=request.idempotency_key,
                    business_object_id="opportunity-1",
                    actor=request.actor,
                    query="改变后的项目风险请求",
                    data_class=DataClass.SENSITIVE,
                    required_capability="writing",
                )
            )

    def test_pipeline_blocks_when_no_authorized_evidence_exists(self) -> None:
        base = demo_pipeline()
        pipeline = EnterpriseAIPipeline(
            base.channels,
            [
                Document(
                    "other-project",
                    "仅限其他项目",
                    "其他项目资料",
                    "project",
                    project_ids=frozenset({"project-b"}),
                )
            ],
        )
        request = RequestEnvelope(
            task_id="proposal-2",
            idempotency_key="opportunity-2:proposal:v1",
            business_object_id="opportunity-2",
            actor=UserContext("u1", "sales", frozenset({"project-a"})),
            query="其他项目资料",
            data_class=DataClass.SENSITIVE,
            required_capability="writing",
        )

        with self.assertRaises(InsufficientEvidence):
            pipeline.prepare(request)


if __name__ == "__main__":
    unittest.main()

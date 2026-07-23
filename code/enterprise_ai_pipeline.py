"""Integrated enterprise-AI delivery example.

This module composes the companion examples into one deterministic pipeline:
policy-first routing, permission-aware retrieval, evidence-bound drafting,
human approval, idempotent write-back, and an auditable trace.

It intentionally uses no model SDK or external service.  The goal is to make
the system boundaries executable before a reader replaces the deterministic
draft function and in-memory store with production components.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from idempotent_workflow import (
    ApprovalContext,
    IdempotencyConflict,
    Status,
    Task,
    WorkflowStore,
)
from model_router import Channel, DataClass, RouteDecision, RouteRequest, route
from permission_rag import Citation, Document, UserContext, retrieve


class InsufficientEvidence(RuntimeError):
    """Raised when an evidence-required task has no authorized citations."""


@dataclass(frozen=True)
class RequestEnvelope:
    task_id: str
    idempotency_key: str
    business_object_id: str
    actor: UserContext
    query: str
    data_class: DataClass
    required_capability: str
    requires_citations: bool = True
    content_version: str = "v1"


@dataclass(frozen=True)
class TraceEvent:
    name: str
    attributes: dict[str, Any]


@dataclass
class PreparedResult:
    request: RequestEnvelope
    route: RouteDecision
    citations: list[Citation]
    draft: str
    task: Task
    confirmation_card: dict[str, Any]
    trace: list[TraceEvent] = field(default_factory=list)


DraftFunction = Callable[[RequestEnvelope, list[Citation]], str]
WriteFunction = Callable[[dict[str, Any]], dict[str, Any]]


def evidence_bound_draft(
    request: RequestEnvelope,
    citations: list[Citation],
) -> str:
    """Build a deterministic draft whose claims remain visibly sourced."""

    evidence = "；".join(
        f"[{citation.doc_id}] {citation.title}: {citation.excerpt}"
        for citation in citations
    )
    return f"任务：{request.query}\n证据：{evidence}\n状态：待业务负责人确认"


class EnterpriseAIPipeline:
    """A small, inspectable orchestration layer for the book's main pattern."""

    def __init__(
        self,
        channels: list[Channel],
        documents: list[Document],
        draft_function: DraftFunction = evidence_bound_draft,
    ) -> None:
        self.channels = channels
        self.documents = documents
        self.draft_function = draft_function
        self.store = WorkflowStore()
        self._prepared: dict[str, PreparedResult] = {}

    def prepare(self, request: RequestEnvelope) -> PreparedResult:
        """Route, retrieve, draft, and prepare an approval-bound task.

        Repeating the same idempotency key returns the original prepared task;
        it does not re-run retrieval or silently change the business payload.
        """

        existing = self._prepared.get(request.idempotency_key)
        if existing is not None:
            if existing.request != request:
                raise IdempotencyConflict(
                    "the same idempotency key cannot prepare a different request"
                )
            return existing

        trace = [
            TraceEvent(
                "request.accepted",
                {
                    "task_id": request.task_id,
                    "business_object_id": request.business_object_id,
                    "actor": request.actor.user_id,
                    "data_class": request.data_class.name,
                },
            )
        ]

        route_decision = route(
            RouteRequest(
                task=request.task_id,
                data_class=request.data_class,
                required_capability=request.required_capability,
            ),
            self.channels,
        )
        trace.append(
            TraceEvent(
                "route.selected",
                {"channel": route_decision.channel, "reason": route_decision.reason},
            )
        )

        citations = retrieve(request.query, request.actor, self.documents)
        trace.append(
            TraceEvent(
                "knowledge.retrieved",
                {
                    "citation_ids": [item.doc_id for item in citations],
                    "citation_count": len(citations),
                },
            )
        )
        if request.requires_citations and not citations:
            trace.append(TraceEvent("task.blocked", {"reason": "no authorized evidence"}))
            raise InsufficientEvidence(
                f"task={request.task_id!r} has no authorized supporting evidence"
            )

        draft = self.draft_function(request, citations)
        citation_ids = [item.doc_id for item in citations]
        payload = {
            "business_object_id": request.business_object_id,
            "content_version": request.content_version,
            "draft": draft,
            "citation_ids": citation_ids,
            "route_channel": route_decision.channel,
        }
        task = self.store.prepare(
            request.task_id,
            request.idempotency_key,
            payload,
        )
        trace.append(
            TraceEvent(
                "approval.prepared",
                {
                    "status": task.status.value,
                    "idempotency_key": task.idempotency_key,
                },
            )
        )

        confirmation_card = {
            "action": "create_draft",
            "business_object_id": request.business_object_id,
            "content_version": request.content_version,
            "route_channel": route_decision.channel,
            "citation_ids": citation_ids,
            "change_preview": draft,
            "risk_notice": "This creates a draft only; external release is not approved.",
        }
        result = PreparedResult(
            request=request,
            route=route_decision,
            citations=citations,
            draft=draft,
            task=task,
            confirmation_card=confirmation_card,
            trace=trace,
        )
        self._prepared[request.idempotency_key] = result
        return result

    def approve_and_commit(
        self,
        prepared: PreparedResult,
        approver: str,
        writer: WriteFunction,
    ) -> Task:
        """Commit the prepared change once and append control evidence."""

        task = self.store.approve_and_execute(
            prepared.request.idempotency_key,
            ApprovalContext(
                approver=approver,
                business_object_id=prepared.request.business_object_id,
                content_version=prepared.request.content_version,
            ),
            writer,
        )
        if not any(event.name == "write.completed" for event in prepared.trace):
            prepared.trace.append(
                TraceEvent(
                    "write.completed",
                    {
                        "status": task.status.value,
                        "approver": task.approver,
                        "result": task.result,
                    },
                )
            )
        return task

    def audit(self, idempotency_key: str) -> tuple[TraceEvent, ...]:
        prepared = self._prepared[idempotency_key]
        return tuple(prepared.trace)


def demo_pipeline() -> EnterpriseAIPipeline:
    """Return a pipeline with synthetic channels and documents."""

    channels = [
        Channel(
            "approved-cloud",
            DataClass.INTERNAL,
            frozenset({"writing", "research"}),
            cost_rank=1,
            latency_rank=1,
        ),
        Channel(
            "local-service",
            DataClass.HIGHLY_SENSITIVE,
            frozenset({"summary", "writing"}),
            cost_rank=2,
            latency_rank=2,
        ),
    ]
    documents = [
        Document(
            "product-current",
            "当前产品范围",
            "标准交付包含权限配置、知识发布和上线回归。",
            "internal",
        ),
        Document(
            "case-project-a",
            "项目 A 复盘",
            "项目 A 的主要风险是历史资料没有明确版本。",
            "project",
            project_ids=frozenset({"project-a"}),
        ),
        Document(
            "case-project-b",
            "项目 B 合同",
            "项目 B 的合同价格和客户承诺。",
            "project",
            project_ids=frozenset({"project-b"}),
        ),
    ]
    return EnterpriseAIPipeline(channels, documents)


def run_integrated_demo() -> PreparedResult:
    """Run the full example and assert the final state for CLI readers."""

    pipeline = demo_pipeline()
    request = RequestEnvelope(
        task_id="proposal-draft-001",
        idempotency_key="opportunity-42:proposal:v1",
        business_object_id="opportunity-42",
        actor=UserContext("sales-001", "sales", frozenset({"project-a"})),
        query="产品交付和项目风险",
        data_class=DataClass.SENSITIVE,
        required_capability="writing",
    )
    prepared = pipeline.prepare(request)
    task = pipeline.approve_and_commit(
        prepared,
        "sales-manager-01",
        lambda payload: {
            "draft_id": f"draft-{payload['business_object_id']}",
            "postcondition": "draft_exists",
        },
    )
    assert task.status == Status.EXECUTED
    return prepared

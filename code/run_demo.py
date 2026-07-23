"""Run all companion-code examples."""

from evaluation_gate import EvalResult, GateConfig, evaluate
from enterprise_ai_pipeline import run_integrated_demo
from idempotent_workflow import ApprovalContext, WorkflowStore
from model_router import Channel, DataClass, RouteRequest, route
from permission_rag import Document, UserContext, retrieve


def main() -> None:
    channels = [
        Channel(
            name="approved-cloud",
            max_data_class=DataClass.INTERNAL,
            capabilities=frozenset({"writing", "research"}),
            cost_rank=2,
            latency_rank=1,
        ),
        Channel(
            name="local-service",
            max_data_class=DataClass.HIGHLY_SENSITIVE,
            capabilities=frozenset({"summary", "writing"}),
            cost_rank=1,
            latency_rank=2,
        ),
    ]
    decision = route(
        RouteRequest("customer-summary", DataClass.SENSITIVE, "summary"),
        channels,
    )
    print("route:", decision)

    user = UserContext("sales-001", "sales", frozenset({"project-a"}))
    documents = [
        Document("d1", "产品资料", "产品交付范围与能力", "internal"),
        Document(
            "d2",
            "项目复盘",
            "客户项目复盘与风险",
            "project",
            project_ids=frozenset({"project-a"}),
        ),
        Document(
            "d3",
            "其他项目合同",
            "未授权合同价格",
            "project",
            project_ids=frozenset({"project-b"}),
        ),
    ]
    print("citations:", retrieve("客户项目风险", user, documents))

    store = WorkflowStore()
    store.prepare(
        "task-001",
        "opportunity-42:proposal:v1",
        {
            "business_object_id": "opportunity-42",
            "content_version": "v1",
            "opportunity": "42",
        },
    )
    task = store.approve_and_execute(
        "opportunity-42:proposal:v1",
        ApprovalContext("sales-manager", "opportunity-42", "v1"),
        lambda payload: {"crm_draft_id": f"draft-{payload['opportunity']}"},
    )
    print("workflow:", task)

    gate = evaluate(
        [
            EvalResult("normal-1", 0.92, 800, 0.12),
            EvalResult("permission-1", 1.0, 500, 0.04),
        ],
        GateConfig(0.9, 1_500, 0.2),
    )
    print("release gate:", gate)

    integrated = run_integrated_demo()
    print("integrated confirmation card:", integrated.confirmation_card)
    print("integrated trace:", [event.name for event in integrated.trace])


if __name__ == "__main__":
    main()

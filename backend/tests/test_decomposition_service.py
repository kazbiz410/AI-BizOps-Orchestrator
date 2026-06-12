from app.repositories.storage import InMemoryRepository
from app.services.decomposition_service import DecompositionService


def test_decompose_process_uses_gemini_steps_when_available(monkeypatch):
    repository = InMemoryRepository()
    organization = repository.create_organization({"name": "Test Org"})
    tool = repository.create_tool(
        {
            "organization_id": organization["id"],
            "name": "Slack",
            "category": "chat",
            "monthly_cost": 0,
            "ai_enabled": False,
            "vendor": None,
        }
    )
    process = repository.create_process(
        {
            "organization_id": organization["id"],
            "department_id": None,
            "name": "営業報告",
            "process_type": "sales",
            "raw_input_text": "Slackで日報を受け取り、担当者が内容を確認してスプレッドシートに転記する",
            "kpi_summary": None,
            "challenge_summary": None,
        }
    )
    service = DecompositionService(repository)

    monkeypatch.setattr(
        service.gemini,
        "generate_json",
        lambda **_: {
            "steps": [
                "Slackで日報を受け取る",
                "担当者が内容を確認する",
                "スプレッドシートに転記する",
            ]
        },
    )

    _, steps = service.decompose_process(process["id"])

    assert [step["step_name"] for step in steps] == [
        "Slackで日報を受け取る",
        "担当者が内容を確認する",
        "スプレッドシートに転記する",
    ]
    assert steps[0]["tool_ids"] == [tool["id"]]
    assert steps[1]["manual_work"] is True
    assert "review" in steps[1]["issue_tags"]
    assert "data_update" in steps[2]["issue_tags"]


def test_decompose_process_falls_back_to_rule_based_split_when_gemini_unavailable(monkeypatch):
    repository = InMemoryRepository()
    organization = repository.create_organization({"name": "Fallback Org"})
    process = repository.create_process(
        {
            "organization_id": organization["id"],
            "department_id": None,
            "name": "請求処理",
            "process_type": "finance",
            "raw_input_text": "担当者が請求内容を確認する。会議後に記録を更新する。",
            "kpi_summary": None,
            "challenge_summary": None,
        }
    )
    service = DecompositionService(repository)

    monkeypatch.setattr(service.gemini, "generate_json", lambda **_: None)

    _, steps = service.decompose_process(process["id"])

    assert [step["step_name"] for step in steps] == [
        "担当者が請求内容を確認する",
        "会議後に記録を更新する",
    ]
    assert steps[0]["manual_work"] is True
    assert steps[1]["meeting_related"] is True

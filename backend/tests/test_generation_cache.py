from app.repositories.storage import InMemoryRepository
from app.core.config import settings
from app.services.generation_service import GenerationService
from app.services.interview_service import InterviewService


def test_recommendation_generation_uses_saved_content_after_first_call(monkeypatch) -> None:
    repository = InMemoryRepository()
    organization = repository.create_organization(
        {"name": "Cache Corp", "industry": "SaaS", "employee_count": 10}
    )
    organization_id = organization["id"]
    repository.replace_findings_for_organization(
        organization_id,
        [
            {
                "organization_id": organization_id,
                "process_id": None,
                "finding_type": "automation",
                "title": "手作業が多い",
                "description": "更新作業が手動です。",
                "severity": "high",
                "evidence": "シート更新が手作業",
            }
        ],
    )
    repository.replace_recommendations_for_organization(
        organization_id,
        [
            {
                "organization_id": organization_id,
                "process_id": None,
                "type": "automation",
                "title": "更新の自動化",
                "description": "定型更新を自動化する。",
                "priority_score": 90,
                "roi_score": 85,
            }
        ],
    )

    service = GenerationService(repository)
    call_count = {"value": 0}

    def fake_generate_json(*, system_instruction: str, payload: dict) -> dict:
        call_count["value"] += 1
        return {
            "summary": "要約",
            "strengths": ["強み"],
            "issues": ["課題"],
            "proposal": "提案",
            "roi_hypothesis": "ROI仮説",
        }

    monkeypatch.setattr(service.gemini, "generate_json", fake_generate_json)

    first = service.generate_recommendation_content(organization_id)
    second = service.generate_recommendation_content(organization_id)

    assert call_count["value"] == 1
    assert first == second
    assert second["generated_by"] == "gemini"


def test_blueprint_generation_uses_saved_content_after_first_call(monkeypatch) -> None:
    repository = InMemoryRepository()
    organization = repository.create_organization(
        {"name": "Blueprint Corp", "industry": "SaaS", "employee_count": 10}
    )
    organization_id = organization["id"]

    service = GenerationService(repository)
    call_count = {"value": 0}

    def fake_generate_json(*, system_instruction: str, payload: dict) -> dict:
        call_count["value"] += 1
        return {
            "blueprints": [
                {
                    "blueprint_type": "system_mermaid",
                    "title": "System",
                    "content": "flowchart LR\nA-->B",
                },
                {
                    "blueprint_type": "process_mermaid",
                    "title": "Process",
                    "content": "flowchart TD\nStart-->End",
                },
            ],
            "implementation_tasks": [
                {"title": "Task 1", "description": "desc", "priority": "high"}
            ],
        }

    monkeypatch.setattr(service.gemini, "generate_json", fake_generate_json)

    first = service.generate_blueprints(organization_id)
    second = service.generate_blueprints(organization_id)

    assert call_count["value"] == 1
    assert first["generated_by"] == "gemini"
    assert second["generated_by"] == "cached"
    assert len(second["blueprints"]) == 2
    assert len(second["implementation_tasks"]) == 1


def test_n8n_generation_uses_saved_content_after_first_call(monkeypatch) -> None:
    repository = InMemoryRepository()
    organization = repository.create_organization(
        {"name": "n8n Corp", "industry": "SaaS", "employee_count": 10}
    )
    organization_id = organization["id"]

    service = GenerationService(repository)
    call_count = {"value": 0}

    def fake_generate_json(*, system_instruction: str, payload: dict) -> dict:
        call_count["value"] += 1
        return {
            "title": "draft",
            "draft_json": "{\"name\":\"workflow\"}",
        }

    monkeypatch.setattr(service.gemini, "generate_json", fake_generate_json)

    first = service.generate_n8n_draft(organization_id)
    second = service.generate_n8n_draft(organization_id)

    assert call_count["value"] == 1
    assert first == second
    assert second["generated_by"] == "gemini"


def test_question_generation_uses_saved_questions_after_first_call(monkeypatch) -> None:
    repository = InMemoryRepository()
    organization = repository.create_organization(
        {"name": "Interview Corp", "industry": "SaaS", "employee_count": 10}
    )
    organization_id = organization["id"]
    repository.replace_findings_for_organization(
        organization_id,
        [
            {
                "organization_id": organization_id,
                "process_id": None,
                "finding_type": "automation",
                "title": "手作業が多い",
                "description": "更新作業が手動です。",
                "severity": "high",
                "evidence": "シート更新が手作業",
            }
        ],
    )

    service = InterviewService(repository)
    monkeypatch.setattr(settings, "slack_incoming_webhook_url", "")

    first_questions, first_status = service.generate_questions(organization_id)
    second_questions, second_status = service.generate_questions(organization_id)

    assert first_status == "draft_only"
    assert second_status == "cached"
    assert first_questions == second_questions

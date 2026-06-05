from app.repositories.storage import InMemoryRepository
from app.services.diagnosis_service import DiagnosisService


def test_diagnosis_reflects_interview_answers():
    repository = InMemoryRepository()
    organization = repository.create_organization({"name": "Interview Org"})
    process = repository.create_process(
        {
            "organization_id": organization["id"],
            "department_id": None,
            "name": "営業報告",
            "process_type": "sales",
            "raw_input_text": "担当者が手作業で確認し、更新する",
            "kpi_summary": None,
            "challenge_summary": None,
        }
    )
    question = repository.replace_interview_questions_for_organization(
        organization["id"],
        [
            {
                "organization_id": organization["id"],
                "process_id": process["id"],
                "assignee": "現場担当者",
                "question": "手作業で行っている更新や確認には、1回あたりどれくらい時間がかかっていますか？",
                "reason": "ROI確認",
                "slack_message": "dummy",
                "status": "draft",
            }
        ],
    )[0]
    repository.create_interview_answer(
        {
            "question_id": question["id"],
            "answer_text": "毎回1時間ほどかかっています",
            "answered_by": "田中",
        }
    )

    findings, recommendations = DiagnosisService(repository).diagnose_organization(organization["id"])

    assert any(finding["title"] == "回答から手作業コストの大きさが確認された" for finding in findings)
    assert any(recommendation["title"] == "回答ベースで手作業削減の優先度を引き上げる" for recommendation in recommendations)

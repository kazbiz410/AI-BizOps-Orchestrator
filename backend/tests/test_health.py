from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_organization_and_dashboard() -> None:
    create_response = client.post(
        "/organizations",
        json={
            "name": "Example Corp",
            "industry": "Software",
            "employee_count": 42,
        },
    )

    assert create_response.status_code == 200
    assert create_response.json()["name"] == "Example Corp"

    dashboard_response = client.get("/dashboard")

    assert dashboard_response.status_code == 200
    assert dashboard_response.json()["organizations_count"] >= 1


def test_decompose_process_into_steps() -> None:
    organization_response = client.post(
        "/organizations",
        json={"name": "Ops Corp", "industry": "SaaS", "employee_count": 12},
    )
    organization_id = organization_response.json()["id"]

    tool_response = client.post(
        "/tools",
        json={
            "organization_id": organization_id,
            "name": "HubSpot",
            "category": "CRM",
            "monthly_cost": 1200,
            "ai_enabled": False,
            "vendor": "HubSpot",
        },
    )
    assert tool_response.status_code == 200

    process_response = client.post(
        "/processes",
        json={
            "organization_id": organization_id,
            "name": "Daily Reporting",
            "process_type": "reporting",
            "raw_input_text": "HubSpotの数字を目視で確認。手作業でシート更新。会議用ドキュメントにアジェンダをAIに生成。",
        },
    )
    process_id = process_response.json()["id"]

    decompose_response = client.post(f"/processes/{process_id}/decompose")

    assert decompose_response.status_code == 200
    payload = decompose_response.json()
    assert len(payload["steps"]) == 3
    assert payload["steps"][0]["manual_work"] is True
    assert payload["steps"][0]["tool_ids"] == [tool_response.json()["id"]]
    assert payload["steps"][2]["meeting_related"] is True
    assert payload["steps"][2]["ai_candidate"] is True


def test_diagnose_organization_generates_findings_and_recommendations() -> None:
    organization_response = client.post(
        "/organizations",
        json={"name": "Revenue Ops", "industry": "B2B SaaS", "employee_count": 20},
    )
    organization_id = organization_response.json()["id"]

    client.post(
        "/tools",
        json={
            "organization_id": organization_id,
            "name": "HubSpot",
            "category": "CRM",
            "monthly_cost": 1500,
            "ai_enabled": False,
            "vendor": "HubSpot",
        },
    )
    client.post(
        "/tools",
        json={
            "organization_id": organization_id,
            "name": "Zoom",
            "category": "Meeting",
            "monthly_cost": 300,
            "ai_enabled": False,
            "vendor": "Zoom",
        },
    )
    client.post(
        "/tools",
        json={
            "organization_id": organization_id,
            "name": "Google Drive",
            "category": "Storage",
            "monthly_cost": 100,
            "ai_enabled": True,
            "vendor": "Google",
        },
    )
    client.post(
        "/tools",
        json={
            "organization_id": organization_id,
            "name": "Box",
            "category": "Storage",
            "monthly_cost": 80,
            "ai_enabled": False,
            "vendor": "Box",
        },
    )

    process_response = client.post(
        "/processes",
        json={
            "organization_id": organization_id,
            "name": "Meeting Follow-up",
            "process_type": "meeting",
            "raw_input_text": "HubSpotの数字を目視で確認。手作業でシート更新。会議用ドキュメントにアジェンダをAIに生成。次のアクションをチェックリストとして記載。",
        },
    )
    process_id = process_response.json()["id"]
    client.post(f"/processes/{process_id}/decompose")

    diagnose_response = client.post("/diagnose", json={"organization_id": organization_id})

    assert diagnose_response.status_code == 200
    payload = diagnose_response.json()
    finding_types = {item["finding_type"] for item in payload["findings"]}
    recommendation_types = {item["type"] for item in payload["recommendations"]}

    assert "consolidation" in finding_types
    assert "integration" in finding_types
    assert "automation" in finding_types
    assert "approval_gate" in recommendation_types
    assert "post_meeting_automation" in recommendation_types

    saved_response = client.get(f"/diagnosis/{organization_id}")
    assert saved_response.status_code == 200
    assert len(saved_response.json()["findings"]) >= 4


def test_generation_endpoints_return_fallback_content() -> None:
    organization_response = client.post(
        "/organizations",
        json={"name": "AI Ops", "industry": "SaaS", "employee_count": 15},
    )
    organization_id = organization_response.json()["id"]

    client.post(
        "/tools",
        json={
            "organization_id": organization_id,
            "name": "HubSpot",
            "category": "CRM",
            "monthly_cost": 1500,
            "ai_enabled": False,
            "vendor": "HubSpot",
        },
    )
    process_response = client.post(
        "/processes",
        json={
            "organization_id": organization_id,
            "name": "Sales Review",
            "process_type": "reporting",
            "raw_input_text": "HubSpotの数字を目視で確認。手作業でシート更新。",
        },
    )
    process_id = process_response.json()["id"]
    client.post(f"/processes/{process_id}/decompose")
    client.post("/diagnose", json={"organization_id": organization_id})

    recommendation_response = client.post(
        "/generate-recommendations", json={"organization_id": organization_id}
    )
    assert recommendation_response.status_code == 200
    assert recommendation_response.json()["generated_by"] in {"fallback", "gemini"}
    assert recommendation_response.json()["summary"]

    blueprint_response = client.post("/generate-blueprints", json={"organization_id": organization_id})
    assert blueprint_response.status_code == 200
    assert len(blueprint_response.json()["blueprints"]) >= 1
    assert len(blueprint_response.json()["implementation_tasks"]) >= 1

    n8n_response = client.post("/generate-n8n-draft", json={"organization_id": organization_id})
    assert n8n_response.status_code == 200
    assert n8n_response.json()["draft_json"]


def test_generate_questions_and_analyze_answers() -> None:
    organization_response = client.post(
        "/organizations",
        json={"name": "Interview Ops", "industry": "SaaS", "employee_count": 10},
    )
    organization_id = organization_response.json()["id"]

    client.post(
        "/tools",
        json={
            "organization_id": organization_id,
            "name": "HubSpot",
            "category": "CRM",
            "monthly_cost": 1000,
            "ai_enabled": False,
            "vendor": "HubSpot",
        },
    )
    client.post(
        "/tools",
        json={
            "organization_id": organization_id,
            "name": "Zoom",
            "category": "Meeting",
            "monthly_cost": 300,
            "ai_enabled": False,
            "vendor": "Zoom",
        },
    )
    process_response = client.post(
        "/processes",
        json={
            "organization_id": organization_id,
            "name": "Weekly Meeting",
            "process_type": "meeting",
            "raw_input_text": "HubSpotの数字を目視で確認。手作業でシート更新。会議後に次のアクションを記載。",
        },
    )
    process_id = process_response.json()["id"]
    client.post(f"/processes/{process_id}/decompose")
    client.post("/diagnose", json={"organization_id": organization_id})

    question_response = client.post("/generate-questions", json={"organization_id": organization_id})
    assert question_response.status_code == 200
    assert len(question_response.json()["interview_questions"]) >= 2

    first_question_id = question_response.json()["interview_questions"][0]["id"]
    answer_response = client.post(
        f"/analyze-answers?organization_id={organization_id}",
        json=[
            {
                "question_id": first_question_id,
                "answer_text": "手作業更新には毎回20分かかっています。",
                "answered_by": "営業企画",
            }
        ],
    )
    assert answer_response.status_code == 200
    assert answer_response.json()["saved_answers"][0]["answer_text"] == "手作業更新には毎回20分かかっています。"

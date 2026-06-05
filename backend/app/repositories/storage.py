from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import uuid4

try:
    from supabase import Client, create_client
except ImportError:  # pragma: no cover - optional during scaffold stage
    Client = object  # type: ignore[assignment]
    create_client = None

from app.core.config import settings


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class StorageRepository(ABC):
    @abstractmethod
    def create_organization(self, payload: dict) -> dict:
        raise NotImplementedError

    @abstractmethod
    def list_organizations(self) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def create_department(self, payload: dict) -> dict:
        raise NotImplementedError

    @abstractmethod
    def list_departments(self) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def create_tool(self, payload: dict) -> dict:
        raise NotImplementedError

    @abstractmethod
    def list_tools(self) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def create_process(self, payload: dict) -> dict:
        raise NotImplementedError

    @abstractmethod
    def list_processes(self) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def get_process(self, process_id: str) -> Optional[dict]:
        raise NotImplementedError

    @abstractmethod
    def replace_process_steps(self, process_id: str, steps: list[dict]) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def list_process_steps(self, process_id: str) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def replace_findings_for_organization(self, organization_id: str, findings: list[dict]) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def list_findings(self, organization_id: str) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def replace_recommendations_for_organization(
        self, organization_id: str, recommendations: list[dict]
    ) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def list_recommendations(self, organization_id: str) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def replace_blueprints_for_organization(self, organization_id: str, blueprints: list[dict]) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def list_blueprints(self, organization_id: str) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def replace_implementation_tasks_for_organization(
        self, organization_id: str, tasks: list[dict]
    ) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def list_implementation_tasks(self, organization_id: str) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def replace_interview_questions_for_organization(
        self, organization_id: str, questions: list[dict]
    ) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def list_interview_questions(self, organization_id: str) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def update_interview_question_status(self, question_id: str, status: str) -> Optional[dict]:
        raise NotImplementedError

    @abstractmethod
    def create_interview_answer(self, payload: dict) -> dict:
        raise NotImplementedError

    @abstractmethod
    def list_interview_answers(self, organization_id: str) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def save_generated_recommendation_content(self, organization_id: str, payload: dict) -> dict:
        raise NotImplementedError

    @abstractmethod
    def get_generated_recommendation_content(self, organization_id: str) -> Optional[dict]:
        raise NotImplementedError

    @abstractmethod
    def save_generated_n8n_draft(self, organization_id: str, payload: dict) -> dict:
        raise NotImplementedError

    @abstractmethod
    def get_generated_n8n_draft(self, organization_id: str) -> Optional[dict]:
        raise NotImplementedError


class InMemoryRepository(StorageRepository):
    def __init__(self) -> None:
        self._organizations: list[dict] = []
        self._departments: list[dict] = []
        self._tools: list[dict] = []
        self._processes: list[dict] = []
        self._process_steps: list[dict] = []
        self._findings: list[dict] = []
        self._recommendations: list[dict] = []
        self._blueprints: list[dict] = []
        self._implementation_tasks: list[dict] = []
        self._interview_questions: list[dict] = []
        self._interview_answers: list[dict] = []
        self._generated_recommendation_contents: list[dict] = []
        self._generated_n8n_drafts: list[dict] = []

    def _record(self, payload: dict) -> dict:
        timestamp = _now_iso()
        return {
            "id": str(uuid4()),
            "created_at": timestamp,
            "updated_at": timestamp,
            **payload,
        }

    def create_organization(self, payload: dict) -> dict:
        record = self._record(payload)
        self._organizations.append(record)
        return record

    def list_organizations(self) -> list[dict]:
        return list(self._organizations)

    def create_department(self, payload: dict) -> dict:
        record = self._record(payload)
        self._departments.append(record)
        return record

    def list_departments(self) -> list[dict]:
        return list(self._departments)

    def create_tool(self, payload: dict) -> dict:
        normalized = {
            **payload,
            "monthly_cost": str(payload.get("monthly_cost", Decimal("0"))),
        }
        record = self._record(normalized)
        self._tools.append(record)
        return record

    def list_tools(self) -> list[dict]:
        return list(self._tools)

    def create_process(self, payload: dict) -> dict:
        record = self._record(payload)
        self._processes.append(record)
        return record

    def list_processes(self) -> list[dict]:
        return list(self._processes)

    def get_process(self, process_id: str) -> Optional[dict]:
        return next((process for process in self._processes if process["id"] == process_id), None)

    def replace_process_steps(self, process_id: str, steps: list[dict]) -> list[dict]:
        self._process_steps = [
            step for step in self._process_steps if step["process_id"] != process_id
        ]
        records = [self._record(step) for step in steps]
        self._process_steps.extend(records)
        return records

    def list_process_steps(self, process_id: str) -> list[dict]:
        return [step for step in self._process_steps if step["process_id"] == process_id]

    def replace_findings_for_organization(self, organization_id: str, findings: list[dict]) -> list[dict]:
        self._findings = [
            finding for finding in self._findings if finding["organization_id"] != organization_id
        ]
        records = [self._record(finding) for finding in findings]
        self._findings.extend(records)
        return records

    def list_findings(self, organization_id: str) -> list[dict]:
        return [finding for finding in self._findings if finding["organization_id"] == organization_id]

    def replace_recommendations_for_organization(
        self, organization_id: str, recommendations: list[dict]
    ) -> list[dict]:
        self._recommendations = [
            recommendation
            for recommendation in self._recommendations
            if recommendation["organization_id"] != organization_id
        ]
        records = [self._record(recommendation) for recommendation in recommendations]
        self._recommendations.extend(records)
        return records

    def list_recommendations(self, organization_id: str) -> list[dict]:
        return [
            recommendation
            for recommendation in self._recommendations
            if recommendation["organization_id"] == organization_id
        ]

    def replace_blueprints_for_organization(self, organization_id: str, blueprints: list[dict]) -> list[dict]:
        self._blueprints = [
            blueprint for blueprint in self._blueprints if blueprint["organization_id"] != organization_id
        ]
        records = [self._record(blueprint) for blueprint in blueprints]
        self._blueprints.extend(records)
        return records

    def list_blueprints(self, organization_id: str) -> list[dict]:
        return [
            blueprint for blueprint in self._blueprints if blueprint["organization_id"] == organization_id
        ]

    def replace_implementation_tasks_for_organization(
        self, organization_id: str, tasks: list[dict]
    ) -> list[dict]:
        self._implementation_tasks = [
            task for task in self._implementation_tasks if task["organization_id"] != organization_id
        ]
        records = [self._record(task) for task in tasks]
        self._implementation_tasks.extend(records)
        return records

    def list_implementation_tasks(self, organization_id: str) -> list[dict]:
        return [
            task for task in self._implementation_tasks if task["organization_id"] == organization_id
        ]

    def replace_interview_questions_for_organization(
        self, organization_id: str, questions: list[dict]
    ) -> list[dict]:
        self._interview_questions = [
            question
            for question in self._interview_questions
            if question["organization_id"] != organization_id
        ]
        records = [self._record(question) for question in questions]
        self._interview_questions.extend(records)
        return records

    def list_interview_questions(self, organization_id: str) -> list[dict]:
        return [
            question
            for question in self._interview_questions
            if question["organization_id"] == organization_id
        ]

    def update_interview_question_status(self, question_id: str, status: str) -> Optional[dict]:
        for index, question in enumerate(self._interview_questions):
            if question["id"] == question_id:
                updated = {
                    **question,
                    "status": status,
                    "updated_at": _now_iso(),
                }
                self._interview_questions[index] = updated
                return updated
        return None

    def create_interview_answer(self, payload: dict) -> dict:
        record = self._record(payload)
        self._interview_answers.append(record)
        return record

    def list_interview_answers(self, organization_id: str) -> list[dict]:
        question_ids = {
            question["id"]
            for question in self._interview_questions
            if question["organization_id"] == organization_id
        }
        return [
            answer
            for answer in self._interview_answers
            if answer["question_id"] in question_ids
        ]

    def save_generated_recommendation_content(self, organization_id: str, payload: dict) -> dict:
        self._generated_recommendation_contents = [
            item
            for item in self._generated_recommendation_contents
            if item["organization_id"] != organization_id
        ]
        record = self._record({"organization_id": organization_id, **payload})
        self._generated_recommendation_contents.append(record)
        return record

    def get_generated_recommendation_content(self, organization_id: str) -> Optional[dict]:
        return next(
            (
                item
                for item in self._generated_recommendation_contents
                if item["organization_id"] == organization_id
            ),
            None,
        )

    def save_generated_n8n_draft(self, organization_id: str, payload: dict) -> dict:
        self._generated_n8n_drafts = [
            item for item in self._generated_n8n_drafts if item["organization_id"] != organization_id
        ]
        record = self._record({"organization_id": organization_id, **payload})
        self._generated_n8n_drafts.append(record)
        return record

    def get_generated_n8n_draft(self, organization_id: str) -> Optional[dict]:
        return next(
            (item for item in self._generated_n8n_drafts if item["organization_id"] == organization_id),
            None,
        )


class SupabaseRepository(StorageRepository):
    def __init__(self, client: Client) -> None:
        self.client = client

    def _insert_one(self, table: str, payload: dict) -> dict:
        response = self.client.table(table).insert(payload).execute()
        return response.data[0]

    def _list(self, table: str) -> list[dict]:
        response = self.client.table(table).select("*").order("created_at", desc=True).execute()
        return response.data

    def create_organization(self, payload: dict) -> dict:
        return self._insert_one("organizations", payload)

    def list_organizations(self) -> list[dict]:
        return self._list("organizations")

    def create_department(self, payload: dict) -> dict:
        return self._insert_one("departments", payload)

    def list_departments(self) -> list[dict]:
        return self._list("departments")

    def create_tool(self, payload: dict) -> dict:
        normalized = {
            **payload,
            "monthly_cost": str(payload.get("monthly_cost", Decimal("0"))),
        }
        return self._insert_one("tools", normalized)

    def list_tools(self) -> list[dict]:
        return self._list("tools")

    def create_process(self, payload: dict) -> dict:
        return self._insert_one("business_processes", payload)

    def list_processes(self) -> list[dict]:
        return self._list("business_processes")

    def get_process(self, process_id: str) -> Optional[dict]:
        response = (
            self.client.table("business_processes")
            .select("*")
            .eq("id", process_id)
            .limit(1)
            .execute()
        )
        return response.data[0] if response.data else None

    def replace_process_steps(self, process_id: str, steps: list[dict]) -> list[dict]:
        self.client.table("process_steps").delete().eq("process_id", process_id).execute()
        if not steps:
            return []
        response = self.client.table("process_steps").insert(steps).execute()
        return response.data

    def list_process_steps(self, process_id: str) -> list[dict]:
        response = (
            self.client.table("process_steps")
            .select("*")
            .eq("process_id", process_id)
            .order("step_order")
            .execute()
        )
        return response.data

    def replace_findings_for_organization(self, organization_id: str, findings: list[dict]) -> list[dict]:
        self.client.table("findings").delete().eq("organization_id", organization_id).execute()
        if not findings:
            return []
        response = self.client.table("findings").insert(findings).execute()
        return response.data

    def list_findings(self, organization_id: str) -> list[dict]:
        response = (
            self.client.table("findings")
            .select("*")
            .eq("organization_id", organization_id)
            .order("created_at", desc=True)
            .execute()
        )
        return response.data

    def replace_recommendations_for_organization(
        self, organization_id: str, recommendations: list[dict]
    ) -> list[dict]:
        self.client.table("recommendations").delete().eq("organization_id", organization_id).execute()
        if not recommendations:
            return []
        response = self.client.table("recommendations").insert(recommendations).execute()
        return response.data

    def list_recommendations(self, organization_id: str) -> list[dict]:
        response = (
            self.client.table("recommendations")
            .select("*")
            .eq("organization_id", organization_id)
            .order("created_at", desc=True)
            .execute()
        )
        return response.data

    def replace_blueprints_for_organization(self, organization_id: str, blueprints: list[dict]) -> list[dict]:
        self.client.table("blueprints").delete().eq("organization_id", organization_id).execute()
        if not blueprints:
            return []
        response = self.client.table("blueprints").insert(blueprints).execute()
        return response.data

    def list_blueprints(self, organization_id: str) -> list[dict]:
        response = (
            self.client.table("blueprints")
            .select("*")
            .eq("organization_id", organization_id)
            .order("created_at", desc=True)
            .execute()
        )
        return response.data

    def replace_implementation_tasks_for_organization(
        self, organization_id: str, tasks: list[dict]
    ) -> list[dict]:
        self.client.table("implementation_tasks").delete().eq("organization_id", organization_id).execute()
        if not tasks:
            return []
        response = self.client.table("implementation_tasks").insert(tasks).execute()
        return response.data

    def list_implementation_tasks(self, organization_id: str) -> list[dict]:
        response = (
            self.client.table("implementation_tasks")
            .select("*")
            .eq("organization_id", organization_id)
            .order("created_at", desc=True)
            .execute()
        )
        return response.data

    def replace_interview_questions_for_organization(
        self, organization_id: str, questions: list[dict]
    ) -> list[dict]:
        self.client.table("interview_questions").delete().eq("organization_id", organization_id).execute()
        if not questions:
            return []
        response = self.client.table("interview_questions").insert(questions).execute()
        return response.data

    def list_interview_questions(self, organization_id: str) -> list[dict]:
        response = (
            self.client.table("interview_questions")
            .select("*")
            .eq("organization_id", organization_id)
            .order("created_at", desc=True)
            .execute()
        )
        return response.data

    def update_interview_question_status(self, question_id: str, status: str) -> Optional[dict]:
        response = (
            self.client.table("interview_questions")
            .update({"status": status, "updated_at": _now_iso()})
            .eq("id", question_id)
            .execute()
        )
        if not response.data:
            return None
        return response.data[0]

    def create_interview_answer(self, payload: dict) -> dict:
        response = self.client.table("interview_answers").insert(payload).execute()
        return response.data[0]

    def list_interview_answers(self, organization_id: str) -> list[dict]:
        question_response = (
            self.client.table("interview_questions")
            .select("id")
            .eq("organization_id", organization_id)
            .execute()
        )
        question_ids = [item["id"] for item in question_response.data]
        if not question_ids:
            return []
        response = (
            self.client.table("interview_answers")
            .select("*")
            .in_("question_id", question_ids)
            .order("created_at", desc=True)
            .execute()
        )
        return response.data

    def save_generated_recommendation_content(self, organization_id: str, payload: dict) -> dict:
        self.client.table("knowledge_sources").delete().eq("organization_id", organization_id).eq(
            "source_type", "generated_recommendation_content"
        ).execute()
        response = self.client.table("knowledge_sources").insert(
            {
                "organization_id": organization_id,
                "source_type": "generated_recommendation_content",
                "title": "Generated recommendation content",
                "content": payload,
            }
        ).execute()
        return response.data[0]

    def get_generated_recommendation_content(self, organization_id: str) -> Optional[dict]:
        response = (
            self.client.table("knowledge_sources")
            .select("*")
            .eq("organization_id", organization_id)
            .eq("source_type", "generated_recommendation_content")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        return response.data[0] if response.data else None

    def save_generated_n8n_draft(self, organization_id: str, payload: dict) -> dict:
        self.client.table("knowledge_sources").delete().eq("organization_id", organization_id).eq(
            "source_type", "generated_n8n_draft"
        ).execute()
        response = self.client.table("knowledge_sources").insert(
            {
                "organization_id": organization_id,
                "source_type": "generated_n8n_draft",
                "title": payload.get("title", "Generated n8n draft"),
                "content": payload,
            }
        ).execute()
        return response.data[0]

    def get_generated_n8n_draft(self, organization_id: str) -> Optional[dict]:
        response = (
            self.client.table("knowledge_sources")
            .select("*")
            .eq("organization_id", organization_id)
            .eq("source_type", "generated_n8n_draft")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        return response.data[0] if response.data else None


_repository: Optional[StorageRepository] = None


def get_repository() -> StorageRepository:
    global _repository

    if _repository is not None:
        return _repository

    if settings.environment == "test":
        _repository = InMemoryRepository()
    elif settings.supabase_url and settings.supabase_service_role_key and create_client is not None:
        client = create_client(settings.supabase_url, settings.supabase_service_role_key)
        _repository = SupabaseRepository(client)
    else:
        _repository = InMemoryRepository()

    return _repository

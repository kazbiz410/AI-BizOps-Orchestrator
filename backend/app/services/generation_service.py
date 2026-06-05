from __future__ import annotations

import json

from app.repositories.storage import StorageRepository
from app.services.gemini_service import GeminiService


class GenerationService:
    def __init__(self, repository: StorageRepository) -> None:
        self.repository = repository
        self.gemini = GeminiService()

    def generate_recommendation_content(self, organization_id: str) -> dict:
        diagnosis_payload = self._build_generation_context(organization_id)
        gemini_result = self.gemini.generate_json(
            system_instruction=(
                "You are a BizOps strategist. Return JSON with keys: summary, strengths, issues, "
                "proposal, roi_hypothesis. Use concise Japanese."
            ),
            payload=diagnosis_payload,
        )

        if gemini_result:
            normalized = self._normalize_recommendation_content(gemini_result)
            if normalized:
                saved = self.repository.save_generated_recommendation_content(
                    organization_id,
                    {**normalized, "generated_by": "gemini"},
                )
                return self._restore_generated_recommendation_content(saved)

        findings = diagnosis_payload["findings"]
        recommendations = diagnosis_payload["recommendations"]
        fallback_result = {
            "summary": f"{len(findings)}件の課題と{len(recommendations)}件の改善提案が見つかりました。",
            "strengths": self._fallback_strengths(diagnosis_payload),
            "issues": [item["title"] for item in findings[:4]],
            "proposal": "まずは手作業削減と主要ツール連携から着手し、その後にAI中間処理を広げるのが現実的です。",
            "roi_hypothesis": self._fallback_roi_hypothesis(diagnosis_payload),
            "generated_by": "fallback",
        }
        saved = self.repository.save_generated_recommendation_content(organization_id, fallback_result)
        return self._restore_generated_recommendation_content(saved)

    def generate_blueprints(self, organization_id: str) -> dict:
        context = self._build_generation_context(organization_id)
        gemini_result = self.gemini.generate_json(
            system_instruction=(
                "You are a technical architect. Return JSON with keys blueprints and implementation_tasks. "
                "blueprints must contain exactly two items: "
                "{blueprint_type:'system_mermaid',title,content} and "
                "{blueprint_type:'process_mermaid',title,content}. "
                "Each content value must be a valid Mermaid flowchart string starting with 'flowchart'. "
                "implementation_tasks is an array of {title,description,priority}. Use concise Japanese."
            ),
            payload=context,
        )

        normalized_generation = self._normalize_blueprint_generation(gemini_result)
        if normalized_generation:
            blueprints = [
                {
                    "organization_id": organization_id,
                    "process_id": None,
                    "blueprint_type": blueprint["blueprint_type"],
                    "title": blueprint["title"],
                    "content": blueprint["content"],
                }
                for blueprint in normalized_generation["blueprints"]
            ]
            tasks = [
                {
                    "organization_id": organization_id,
                    "process_id": None,
                    "title": task["title"],
                    "description": task["description"],
                    "status": "draft",
                    "priority": task["priority"],
                }
                for task in normalized_generation["implementation_tasks"]
            ]
            saved_blueprints = self.repository.replace_blueprints_for_organization(organization_id, blueprints)
            saved_tasks = self.repository.replace_implementation_tasks_for_organization(organization_id, tasks)
            return {
                "organization_id": organization_id,
                "blueprints": saved_blueprints,
                "implementation_tasks": saved_tasks,
                "generated_by": "gemini",
            }

        fallback_blueprints = self._fallback_blueprints(organization_id, context)
        fallback_tasks = self._fallback_tasks(organization_id, context)
        saved_blueprints = self.repository.replace_blueprints_for_organization(organization_id, fallback_blueprints)
        saved_tasks = self.repository.replace_implementation_tasks_for_organization(organization_id, fallback_tasks)
        return {
            "organization_id": organization_id,
            "blueprints": saved_blueprints,
            "implementation_tasks": saved_tasks,
            "generated_by": "fallback",
        }

    def generate_n8n_draft(self, organization_id: str) -> dict:
        context = self._build_generation_context(organization_id)
        gemini_result = self.gemini.generate_json(
            system_instruction=(
                "Return JSON with keys title and draft_json. draft_json should be a stringified JSON object "
                "representing a simple n8n workflow draft."
            ),
            payload=context,
        )
        normalized_n8n = self._normalize_n8n_draft(gemini_result)
        if normalized_n8n:
            saved = self.repository.save_generated_n8n_draft(
                organization_id,
                {
                    "title": normalized_n8n["title"],
                    "draft_json": normalized_n8n["draft_json"],
                    "generated_by": "gemini",
                },
            )
            return self._restore_generated_n8n_draft(organization_id, saved)

        fallback_result = {
            "title": "n8n draft for business process automation",
            "draft_json": json.dumps(
                {
                    "name": "AI BizOps Orchestrator Draft",
                    "nodes": [
                        {"name": "Trigger", "type": "n8n-nodes-base.manualTrigger"},
                        {"name": "Fetch CRM Data", "type": "n8n-nodes-base.httpRequest"},
                        {"name": "AI Transform", "type": "n8n-nodes-base.code"},
                        {"name": "Update Sheet", "type": "n8n-nodes-base.googleSheets"},
                    ],
                    "connections": {
                        "Trigger": {"main": [[{"node": "Fetch CRM Data"}]]},
                        "Fetch CRM Data": {"main": [[{"node": "AI Transform"}]]},
                        "AI Transform": {"main": [[{"node": "Update Sheet"}]]},
                    },
                },
                ensure_ascii=False,
                indent=2,
            ),
            "generated_by": "fallback",
        }
        saved = self.repository.save_generated_n8n_draft(organization_id, fallback_result)
        return self._restore_generated_n8n_draft(organization_id, saved)

    def _build_generation_context(self, organization_id: str) -> dict:
        findings = self.repository.list_findings(organization_id)
        recommendations = self.repository.list_recommendations(organization_id)
        tools = [tool for tool in self.repository.list_tools() if tool["organization_id"] == organization_id]
        processes = [
            process for process in self.repository.list_processes() if process["organization_id"] == organization_id
        ]
        process_steps = {
            process["id"]: self.repository.list_process_steps(process["id"]) for process in processes
        }
        return {
            "organization_id": organization_id,
            "findings": findings,
            "recommendations": recommendations,
            "tools": [
                {
                    "name": tool["name"],
                    "category": tool["category"],
                    "ai_enabled": tool["ai_enabled"],
                    "monthly_cost": tool["monthly_cost"],
                }
                for tool in tools
            ],
            "processes": [
                {
                    "name": process["name"],
                    "process_type": process.get("process_type"),
                    "steps": process_steps.get(process["id"], []),
                }
                for process in processes
            ],
        }

    def _fallback_strengths(self, context: dict) -> list[str]:
        strengths = []
        if context["processes"]:
            strengths.append("業務プロセスの入力と分解の土台が整っており、改善の議論を始めやすいです。")
        if any(tool["ai_enabled"] for tool in context["tools"]):
            strengths.append("一部ツールではすでにAI活用が始まっており、横展開の起点があります。")
        if not strengths:
            strengths.append("現状把握の材料がそろい始めており、改善の優先順位付けがしやすい状態です。")
        return strengths

    def _fallback_roi_hypothesis(self, context: dict) -> str:
        automation_count = sum(
            1 for recommendation in context["recommendations"] if recommendation["type"] == "automation"
        )
        integration_count = sum(
            1 for recommendation in context["recommendations"] if recommendation["type"] == "integration"
        )
        return (
            f"自動化候補 {automation_count} 件と連携候補 {integration_count} 件を優先実装することで、"
            "手作業時間の削減と転記ミス低減による運用コスト改善が期待できます。"
        )

    def _fallback_blueprints(self, organization_id: str, context: dict) -> list[dict]:
        process_names = [process["name"] for process in context["processes"]] or ["Business Process"]
        system_mermaid = "\n".join(
            [
                "flowchart LR",
                '  CRM["CRM"] --> AI["AI Transform"]',
                '  AI --> Sheet["Spreadsheet"]',
                '  AI --> Slack["Slack"]',
            ]
        )
        process_mermaid = "\n".join(
            [
                "flowchart TD",
                f'  Start["{process_names[0]}"] --> Review["確認"]',
                '  Review --> Update["更新"]',
                '  Update --> Meeting["会議準備/会議後整理"]',
            ]
        )
        return [
            {
                "organization_id": organization_id,
                "process_id": None,
                "blueprint_type": "system_mermaid",
                "title": "システム連携図",
                "content": system_mermaid,
            },
            {
                "organization_id": organization_id,
                "process_id": None,
                "blueprint_type": "process_mermaid",
                "title": "業務フロー図",
                "content": process_mermaid,
            },
        ]

    def _fallback_tasks(self, organization_id: str, context: dict) -> list[dict]:
        return [
            {
                "organization_id": organization_id,
                "process_id": None,
                "title": "主要ツールの連携要件を整理",
                "description": "CRM、会議、スプレッドシートの連携優先順位を決める。",
                "status": "draft",
                "priority": "high",
            },
            {
                "organization_id": organization_id,
                "process_id": None,
                "title": "手作業更新工程の自動化設計",
                "description": "目視確認と手更新をどこまで自動化するかを設計する。",
                "status": "draft",
                "priority": "high",
            },
            {
                "organization_id": organization_id,
                "process_id": None,
                "title": "会議前後自動化の実装候補を洗い出す",
                "description": "アジェンダ生成、議事録化、アクション抽出のフローを固める。",
                "status": "draft",
                "priority": "medium",
            },
        ]

    def _normalize_recommendation_content(self, payload: dict | None) -> dict | None:
        if not isinstance(payload, dict):
            return None

        summary = self._coerce_text(payload.get("summary"))
        strengths = self._coerce_text_list(payload.get("strengths"))
        issues = self._coerce_text_list(payload.get("issues"))
        proposal = self._coerce_text(payload.get("proposal"))
        roi_hypothesis = self._coerce_text(payload.get("roi_hypothesis"))

        if not all([summary, strengths, issues, proposal, roi_hypothesis]):
            return None

        return {
            "summary": summary,
            "strengths": strengths,
            "issues": issues,
            "proposal": proposal,
            "roi_hypothesis": roi_hypothesis,
        }

    def _normalize_blueprint_generation(self, payload: dict | None) -> dict | None:
        if not isinstance(payload, dict):
            return None

        raw_blueprints = payload.get("blueprints")
        raw_tasks = payload.get("implementation_tasks")
        if not isinstance(raw_blueprints, list) or not isinstance(raw_tasks, list):
            return None

        blueprints = []
        for blueprint in raw_blueprints:
            if not isinstance(blueprint, dict):
                continue
            blueprint_type = self._coerce_text(blueprint.get("blueprint_type"))
            title = self._coerce_text(blueprint.get("title"))
            content = self._coerce_text(blueprint.get("content"))
            if (
                blueprint_type in {"system_mermaid", "process_mermaid"}
                and title
                and content
                and content.lstrip().startswith("flowchart")
            ):
                blueprints.append(
                    {
                        "blueprint_type": blueprint_type,
                        "title": title,
                        "content": content,
                    }
                )

        tasks = []
        for task in raw_tasks:
            if not isinstance(task, dict):
                continue
            title = self._coerce_text(task.get("title"))
            description = self._coerce_text(task.get("description"))
            priority = self._coerce_text(task.get("priority"))
            if title and description and priority:
                tasks.append(
                    {
                        "title": title,
                        "description": description,
                        "priority": priority,
                    }
                )

        blueprint_types = {item["blueprint_type"] for item in blueprints}
        if (
            not blueprints
            or not tasks
            or not {"system_mermaid", "process_mermaid"}.issubset(blueprint_types)
        ):
            return None

        return {
            "blueprints": blueprints,
            "implementation_tasks": tasks,
        }

    def _normalize_n8n_draft(self, payload: dict | None) -> dict | None:
        if not isinstance(payload, dict):
            return None

        title = self._coerce_text(payload.get("title"))
        draft_json = payload.get("draft_json")

        if isinstance(draft_json, (dict, list)):
            draft_json = json.dumps(draft_json, ensure_ascii=False, indent=2)
        else:
            draft_json = self._coerce_text(draft_json)

        if not title or not draft_json:
            return None

        return {
            "title": title,
            "draft_json": draft_json,
        }

    def _coerce_text(self, value: object) -> str | None:
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        if isinstance(value, list):
            parts = [item.strip() for item in value if isinstance(item, str) and item.strip()]
            if parts:
                return " ".join(parts)
        return None

    def _coerce_text_list(self, value: object) -> list[str]:
        if isinstance(value, list):
            normalized = [item.strip() for item in value if isinstance(item, str) and item.strip()]
            if normalized:
                return normalized
        text = self._coerce_text(value)
        if text:
            return [segment.strip() for segment in text.split("\n") if segment.strip()] or [text]
        return []

    def _restore_generated_recommendation_content(self, record: dict) -> dict:
        content = record.get("content", record)
        return {
            "summary": content["summary"],
            "strengths": content["strengths"],
            "issues": content["issues"],
            "proposal": content["proposal"],
            "roi_hypothesis": content["roi_hypothesis"],
            "generated_by": content["generated_by"],
        }

    def _restore_generated_n8n_draft(self, organization_id: str, record: dict) -> dict:
        content = record.get("content", record)
        return {
            "organization_id": organization_id,
            "title": content["title"],
            "draft_json": content["draft_json"],
            "generated_by": content["generated_by"],
        }

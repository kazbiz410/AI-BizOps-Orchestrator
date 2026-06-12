from __future__ import annotations

import httpx

from app.core.config import settings
from app.repositories.storage import StorageRepository


class InterviewService:
    """Builds follow-up questions for missing operational context."""

    def __init__(self, repository: StorageRepository) -> None:
        self.repository = repository

    def generate_questions(self, organization_id: str, force_refresh: bool = False) -> tuple[list[dict], str]:
        if not force_refresh:
            saved_questions = self.repository.list_interview_questions(organization_id)
            if saved_questions:
                return saved_questions, "cached"

        findings = self.repository.list_findings(organization_id)
        processes = [
            process for process in self.repository.list_processes() if process["organization_id"] == organization_id
        ]
        tools = [tool for tool in self.repository.list_tools() if tool["organization_id"] == organization_id]

        questions: list[dict] = []

        if any(finding["finding_type"] == "automation" for finding in findings):
            related_process = next((process for process in processes if process.get("raw_input_text")), None)
            questions.append(
                self._build_question(
                    organization_id=organization_id,
                    process_id=related_process["id"] if related_process else None,
                    assignee="現場担当者",
                    question="手作業で行っている更新や確認には、1回あたりどれくらい時間がかかっていますか？",
                    reason="自動化のROI仮説を具体化するには、現在の手作業コストを把握する必要があるためです。",
                )
            )

        if any(finding["finding_type"] == "integration" for finding in findings):
            questions.append(
                self._build_question(
                    organization_id=organization_id,
                    process_id=None,
                    assignee="Ops管理者",
                    question="CRM と Gmail / Google Workspace / Zoom の既存連携状況はどうなっていますか？",
                    reason="連携提案が新規構築なのか既存設定の改善なのかを見極めるためです。",
                )
            )

        if any(finding["finding_type"] in {"approval_gate", "post_meeting_automation"} for finding in findings):
            meeting_process = next(
                (process for process in processes if "会議" in process.get("raw_input_text", "")),
                None,
            )
            questions.append(
                self._build_question(
                    organization_id=organization_id,
                    process_id=meeting_process["id"] if meeting_process else None,
                    assignee="マネージャー",
                    question="会議後のアクション整理やタスク確定は、最終的に誰が承認していますか？",
                    reason="Human in the Loop を残す位置を決めるには、責任者の確認ポイントが必要だからです。",
                )
            )

        if len([tool for tool in tools if tool["category"].lower() == "storage"]) >= 2:
            questions.append(
                self._build_question(
                    organization_id=organization_id,
                    process_id=None,
                    assignee="情報システム担当",
                    question="Google Drive と Box のうち、どちらが正式な保管先で、移行できない理由はありますか？",
                    reason="統廃合の可否は、正式運用先と移行制約の確認が必要だからです。",
                )
            )

        saved_questions = self.repository.replace_interview_questions_for_organization(
            organization_id, questions
        )
        send_status = self._maybe_send_to_slack(saved_questions)
        return saved_questions, send_status

    def analyze_answers(self, answers: list[dict]) -> list[dict]:
        saved_answers = [self.repository.create_interview_answer(answer) for answer in answers]
        for answer in answers:
            self.repository.update_interview_question_status(answer["question_id"], "answered")
        return saved_answers

    def _build_question(
        self,
        *,
        organization_id: str,
        process_id: str | None,
        assignee: str,
        question: str,
        reason: str,
    ) -> dict:
        slack_message = (
            f"確認したいことがあります。\n"
            f"宛先: {assignee}\n"
            f"質問: {question}\n"
            f"理由: {reason}"
        )
        return {
            "organization_id": organization_id,
            "process_id": process_id,
            "assignee": assignee,
            "question": question,
            "reason": reason,
            "slack_message": slack_message,
            "status": "draft",
        }

    def _maybe_send_to_slack(self, questions: list[dict]) -> str:
        if not settings.slack_incoming_webhook_url or not questions:
            return "draft_only"

        payload = {"text": "\n\n".join(question["slack_message"] for question in questions)}
        try:
            response = httpx.post(settings.slack_incoming_webhook_url, json=payload, timeout=10.0)
            response.raise_for_status()
            return "sent"
        except Exception:
            return "send_failed"

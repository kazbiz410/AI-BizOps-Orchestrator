from __future__ import annotations

import re

from app.repositories.storage import StorageRepository
from app.services.gemini_service import GeminiService


class DecompositionService:
    """Converts raw business process text into structured process steps."""

    def __init__(self, repository: StorageRepository) -> None:
        self.repository = repository
        self.gemini = GeminiService()

    def decompose_process(self, process_id: str) -> tuple[dict, list[dict]]:
        process = self.repository.get_process(process_id)
        if process is None:
            raise ValueError("Process not found")

        organization_tools = [
            tool
            for tool in self.repository.list_tools()
            if tool["organization_id"] == process["organization_id"]
        ]
        steps = self._build_steps(process, organization_tools)
        saved_steps = self.repository.replace_process_steps(process_id, steps)
        return process, saved_steps

    def _build_steps(self, process: dict, tools: list[dict]) -> list[dict]:
        sentences = self._build_candidate_sentences(process["raw_input_text"])
        steps: list[dict] = []

        for index, sentence in enumerate(sentences, start=1):
            detected_tools = self._find_tools(sentence, tools)
            tool_ids = [tool["id"] for tool in detected_tools]
            meeting_related = self._contains_any(sentence, ["会議", "商談", "議事録", "録音", "アジェンダ"])
            manual_work = self._contains_any(sentence, ["手作業", "目視", "転記", "確認", "更新", "記載"])
            ai_candidate = self._contains_any(sentence, ["AI", "要約", "生成", "整理", "分析"])
            approval_required = self._contains_any(sentence, ["承認", "確認依頼", "レビュー", "チェック"])
            automation_candidate = manual_work or self._contains_any(
                sentence, ["録音", "通知", "集約", "同期"]
            )
            human_approval_candidate = approval_required or self._contains_any(
                sentence, ["次のアクション", "タスク", "アサイン", "依頼"]
            )
            issue_tags = self._build_issue_tags(
                sentence,
                manual_work=manual_work,
                meeting_related=meeting_related,
                ai_candidate=ai_candidate,
                human_approval_candidate=human_approval_candidate,
            )

            steps.append(
                {
                    "process_id": process["id"],
                    "step_order": index,
                    "step_name": sentence,
                    "actor": "担当者",
                    "input_data": self._infer_input_data(sentence),
                    "output_data": self._infer_output_data(sentence),
                    "tool_ids": tool_ids,
                    "manual_work": manual_work,
                    "approval_required": approval_required,
                    "ai_candidate": ai_candidate,
                    "automation_candidate": automation_candidate,
                    "human_approval_candidate": human_approval_candidate,
                    "issue_tags": issue_tags,
                    "meeting_related": meeting_related,
                }
            )

        return steps

    def _build_candidate_sentences(self, raw_input_text: str) -> list[str]:
        gemini_steps = self._generate_candidate_steps(raw_input_text)
        if gemini_steps:
            return gemini_steps
        return self._split_sentences(raw_input_text)

    def _generate_candidate_steps(self, raw_input_text: str) -> list[str]:
        payload = {
            "raw_input_text": raw_input_text,
        }
        gemini_result = self.gemini.generate_json(
            system_instruction=(
                "You are a business process analyst. "
                "Split the user's Japanese business process description into 3 to 8 concrete steps. "
                "Return JSON with one key: steps. "
                "steps must be an array of short Japanese strings. "
                "Each string should describe one step only. "
                "Do not include numbering, markdown, or explanations."
            ),
            payload=payload,
        )
        if not isinstance(gemini_result, dict):
            return []

        raw_steps = gemini_result.get("steps")
        if not isinstance(raw_steps, list):
            return []

        normalized_steps: list[str] = []
        for item in raw_steps:
            if not isinstance(item, str):
                continue
            step = item.strip(" ・\t\n")
            if not step:
                continue
            step = re.sub(r"^\d+[\.\)]\s*", "", step)
            step = re.sub(r"^[\-*]\s*", "", step)
            if step:
                normalized_steps.append(step)

        if len(normalized_steps) < 2:
            return []

        return normalized_steps[:8]

    def _split_sentences(self, raw_input_text: str) -> list[str]:
        chunks = re.split(r"[。\n]+", raw_input_text)
        return [chunk.strip(" ・\t") for chunk in chunks if chunk.strip(" ・\t")]

    def _find_tools(self, sentence: str, tools: list[dict]) -> list[dict]:
        lowered_sentence = sentence.lower()
        return [tool for tool in tools if tool["name"].lower() in lowered_sentence]

    def _contains_any(self, sentence: str, keywords: list[str]) -> bool:
        return any(keyword.lower() in sentence.lower() for keyword in keywords)

    def _build_issue_tags(
        self,
        sentence: str,
        *,
        manual_work: bool,
        meeting_related: bool,
        ai_candidate: bool,
        human_approval_candidate: bool,
    ) -> list[str]:
        tags: list[str] = []
        if manual_work:
            tags.append("manual_work")
        if meeting_related:
            tags.append("meeting_related")
        if ai_candidate:
            tags.append("ai_candidate")
        if human_approval_candidate:
            tags.append("human_approval_candidate")
        if self._contains_any(sentence, ["更新", "記載", "転記"]):
            tags.append("data_update")
        if self._contains_any(sentence, ["確認", "目視"]):
            tags.append("review")
        return tags

    def _infer_input_data(self, sentence: str) -> str | None:
        if self._contains_any(sentence, ["数字", "成果", "レポート"]):
            return "数値データ"
        if self._contains_any(sentence, ["会議", "アジェンダ"]):
            return "会議情報"
        if self._contains_any(sentence, ["音声", "録音"]):
            return "音声データ"
        return None

    def _infer_output_data(self, sentence: str) -> str | None:
        if self._contains_any(sentence, ["シート", "スプレッドシート"]):
            return "スプレッドシート更新"
        if self._contains_any(sentence, ["ドキュメント", "議事録"]):
            return "ドキュメント"
        if self._contains_any(sentence, ["チェックリスト", "タスク"]):
            return "タスク一覧"
        return None

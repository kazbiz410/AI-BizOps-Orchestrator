from __future__ import annotations

from collections import Counter
import re

from app.repositories.storage import StorageRepository
from app.services.recommendation_service import RecommendationService


class DiagnosisService:
    """Applies rule-based diagnosis to structured process steps and tools."""

    def __init__(self, repository: StorageRepository) -> None:
        self.repository = repository
        self.recommendation_service = RecommendationService()

    def diagnose_organization(self, organization_id: str) -> tuple[list[dict], list[dict]]:
        tools = [tool for tool in self.repository.list_tools() if tool["organization_id"] == organization_id]
        processes = [
            process for process in self.repository.list_processes() if process["organization_id"] == organization_id
        ]
        questions = self.repository.list_interview_questions(organization_id)
        answers = self.repository.list_interview_answers(organization_id)
        process_steps = {
            process["id"]: self.repository.list_process_steps(process["id"]) for process in processes
        }

        findings: list[dict] = []
        recommendations: list[dict] = []

        findings.extend(self._diagnose_tool_consolidation(organization_id, tools, recommendations))
        findings.extend(self._diagnose_missing_integrations(organization_id, tools, recommendations))
        findings.extend(self._diagnose_process_issues(organization_id, processes, process_steps, recommendations))
        findings.extend(self._diagnose_ai_enablement(organization_id, tools, recommendations))
        findings.extend(
            self._diagnose_interview_answers(
                organization_id,
                questions,
                answers,
                recommendations,
            )
        )

        saved_findings = self.repository.replace_findings_for_organization(organization_id, findings)
        indexed_findings = {finding["title"]: finding for finding in saved_findings}

        finalized_recommendations = []
        for recommendation in recommendations:
            linked_title = recommendation.pop("_linked_finding_title", None)
            if linked_title and linked_title in indexed_findings:
                recommendation["finding_id"] = indexed_findings[linked_title]["id"]
            finalized_recommendations.append(recommendation)

        saved_recommendations = self.repository.replace_recommendations_for_organization(
            organization_id, finalized_recommendations
        )
        return saved_findings, saved_recommendations

    def _diagnose_tool_consolidation(
        self, organization_id: str, tools: list[dict], recommendations: list[dict]
    ) -> list[dict]:
        findings: list[dict] = []
        category_counts = Counter(tool["category"].lower() for tool in tools)
        storage_tools = [tool for tool in tools if tool["category"].lower() == "storage"]
        if len(storage_tools) >= 2 or category_counts.get("storage", 0) >= 2:
            title = "ストレージツールの重複"
            findings.append(
                {
                    "organization_id": organization_id,
                    "process_id": None,
                    "title": title,
                    "finding_type": "consolidation",
                    "severity": "medium",
                    "evidence": {"tools": [tool["name"] for tool in storage_tools]},
                    "summary": "同カテゴリのストレージツールが複数あり、統廃合余地があります。",
                }
            )
            monthly_cost = sum(float(tool.get("monthly_cost", 0) or 0) for tool in storage_tools)
            recommendations.append(
                {
                    **self.recommendation_service.build_recommendation(
                        organization_id=organization_id,
                        finding_id=None,
                        recommendation_type="consolidation",
                        title="ストレージツールの統廃合を検討",
                        description="Google Drive や Box など同カテゴリツールの重複利用を整理し、コストと運用負荷を下げます。",
                        priority_score=75,
                        roi_score=min(90, int(monthly_cost // 10) + 40),
                    ),
                    "_linked_finding_title": title,
                }
            )
        return findings

    def _diagnose_interview_answers(
        self,
        organization_id: str,
        questions: list[dict],
        answers: list[dict],
        recommendations: list[dict],
    ) -> list[dict]:
        if not answers:
            return []

        findings: list[dict] = []
        questions_by_id = {question["id"]: question for question in questions}

        for answer in answers:
            question = questions_by_id.get(answer["question_id"])
            if not question:
                continue

            question_text = (question.get("question") or "").lower()
            answer_text = (answer.get("answer_text") or "").strip()
            answer_text_lower = answer_text.lower()
            if not answer_text:
                continue

            if "どれくらい時間" in question_text:
                minutes = self._extract_minutes(answer_text_lower)
                if minutes is not None and minutes >= 30:
                    title = "回答から手作業コストの大きさが確認された"
                    findings.append(
                        {
                            "organization_id": organization_id,
                            "process_id": question.get("process_id"),
                            "title": title,
                            "finding_type": "automation",
                            "severity": "high" if minutes >= 60 else "medium",
                            "evidence": {"answer_text": answer_text, "minutes_per_run": minutes},
                            "summary": "追加回答から、手作業工程の時間負荷が大きいことが確認できました。",
                        }
                    )
                    recommendations.append(
                        {
                            **self.recommendation_service.build_recommendation(
                                organization_id=organization_id,
                                finding_id=None,
                                recommendation_type="automation",
                                title="回答ベースで手作業削減の優先度を引き上げる",
                                description="回答で判明した作業時間を基に、自動化候補の優先度を上げて実装順を見直します。",
                                priority_score=90 if minutes >= 60 else 78,
                                roi_score=88 if minutes >= 60 else 72,
                            ),
                            "_linked_finding_title": title,
                        }
                    )

            if "連携状況" in question_text and any(
                keyword in answer_text_lower for keyword in ["未連携", "連携していない", "手動", "csv", "コピペ"]
            ):
                title = "回答から既存連携ギャップが確認された"
                findings.append(
                    {
                        "organization_id": organization_id,
                        "process_id": question.get("process_id"),
                        "title": title,
                        "finding_type": "integration",
                        "severity": "high",
                        "evidence": {"answer_text": answer_text},
                        "summary": "追加回答から、既存の手動連携や未接続が残っていることが確認できました。",
                    }
                )
                recommendations.append(
                    {
                        **self.recommendation_service.build_recommendation(
                            organization_id=organization_id,
                            finding_id=None,
                            recommendation_type="integration",
                            title="回答ベースで連携改善の優先度を確定",
                            description="手動連携や未接続と分かった経路から、連携設計の対象範囲を確定します。",
                            priority_score=89,
                            roi_score=79,
                        ),
                        "_linked_finding_title": title,
                    }
                )

            if "誰が承認" in question_text and any(
                keyword in answer_text for keyword in ["部長", "マネージャー", "責任者", "承認"]
            ):
                title = "回答から承認責任者が明確になった"
                findings.append(
                    {
                        "organization_id": organization_id,
                        "process_id": question.get("process_id"),
                        "title": title,
                        "finding_type": "approval_gate",
                        "severity": "low",
                        "evidence": {"answer_text": answer_text},
                        "summary": "追加回答により、どこで人の承認を残すべきかが明確になりました。",
                    }
                )
                recommendations.append(
                    {
                        **self.recommendation_service.build_recommendation(
                            organization_id=organization_id,
                            finding_id=None,
                            recommendation_type="approval_gate",
                            title="承認責任者に合わせて Human in the Loop を設計",
                            description="回答で分かった承認者を基準に、自動化前後の確認ポイントを具体化します。",
                            priority_score=64,
                            roi_score=50,
                        ),
                        "_linked_finding_title": title,
                    }
                )

        return findings

    def _extract_minutes(self, answer_text: str) -> int | None:
        hour_match = re.search(r"(\d+)\s*時間", answer_text)
        minute_match = re.search(r"(\d+)\s*分", answer_text)
        total = 0
        if hour_match:
            total += int(hour_match.group(1)) * 60
        if minute_match:
            total += int(minute_match.group(1))
        if total:
            return total
        return None

    def _diagnose_missing_integrations(
        self, organization_id: str, tools: list[dict], recommendations: list[dict]
    ) -> list[dict]:
        findings: list[dict] = []
        tool_names = {tool["name"].lower(): tool for tool in tools}
        has_crm = any(tool["category"].lower() == "crm" for tool in tools)
        has_gmail = any("gmail" in name or "google workspace" in name for name in tool_names)
        has_zoom = any("zoom" in name for name in tool_names)

        if has_crm and not has_gmail:
            title = "CRMとGmail/Google Workspaceが未接続"
            findings.append(
                {
                    "organization_id": organization_id,
                    "process_id": None,
                    "title": title,
                    "finding_type": "integration",
                    "severity": "high",
                    "evidence": {"crm_present": True, "gmail_connected": False},
                    "summary": "CRMはあるのにメール基盤が未接続で、情報連携のロスが起きやすい状態です。",
                }
            )
            recommendations.append(
                {
                    **self.recommendation_service.build_recommendation(
                        organization_id=organization_id,
                        finding_id=None,
                        recommendation_type="integration",
                        title="CRMとGmail/Google Workspaceを連携",
                        description="商談・問い合わせ・顧客コミュニケーションの情報をつなぎ、転記や見落としを減らします。",
                        priority_score=88,
                        roi_score=78,
                    ),
                    "_linked_finding_title": title,
                }
            )

        if has_crm and has_zoom:
            title = "Zoom会議データのCRM連携余地"
            findings.append(
                {
                    "organization_id": organization_id,
                    "process_id": None,
                    "title": title,
                    "finding_type": "integration",
                    "severity": "medium",
                    "evidence": {"crm_present": True, "zoom_present": True},
                    "summary": "会議ログや商談内容をCRMへつなぐ余地があります。",
                }
            )
            recommendations.append(
                {
                    **self.recommendation_service.build_recommendation(
                        organization_id=organization_id,
                        finding_id=None,
                        recommendation_type="integration",
                        title="ZoomとCRMの会議連携を追加",
                        description="会議記録や商談メモをCRMに寄せ、営業活動の入力負荷を下げます。",
                        priority_score=70,
                        roi_score=65,
                    ),
                    "_linked_finding_title": title,
                }
            )
        return findings

    def _diagnose_process_issues(
        self,
        organization_id: str,
        processes: list[dict],
        process_steps: dict[str, list[dict]],
        recommendations: list[dict],
    ) -> list[dict]:
        findings: list[dict] = []
        for process in processes:
            steps = process_steps.get(process["id"], [])
            if not steps:
                continue

            manual_count = sum(1 for step in steps if step.get("manual_work"))
            if manual_count >= 2 or (steps and manual_count / len(steps) >= 0.5):
                title = f"{process['name']} の手作業ボトルネック"
                findings.append(
                    {
                        "organization_id": organization_id,
                        "process_id": process["id"],
                        "title": title,
                        "finding_type": "automation",
                        "severity": "high",
                        "evidence": {"manual_step_count": manual_count, "total_steps": len(steps)},
                        "summary": "手作業が多く、作業時間とミスの両方が増えやすい状態です。",
                    }
                )
                recommendations.append(
                    {
                        **self.recommendation_service.build_recommendation(
                            organization_id=organization_id,
                            finding_id=None,
                            recommendation_type="automation",
                            title=f"{process['name']} の自動化候補",
                            description="手作業更新や目視確認が多い工程を、自動集約や自動同期に置き換えることを検討します。",
                            priority_score=85,
                            roi_score=82,
                        ),
                        "_linked_finding_title": title,
                    }
                )

            has_transform_gap = any(
                step.get("input_data")
                and step.get("output_data")
                and step.get("input_data") != step.get("output_data")
                for step in steps
            )
            if has_transform_gap:
                title = f"{process['name']} のAI中間処理余地"
                findings.append(
                    {
                        "organization_id": organization_id,
                        "process_id": process["id"],
                        "title": title,
                        "finding_type": "ai_transform",
                        "severity": "medium",
                        "evidence": {"transform_steps": True},
                        "summary": "入力と出力の形式差があり、AIによる変換や要約の余地があります。",
                    }
                )
                recommendations.append(
                    {
                        **self.recommendation_service.build_recommendation(
                            organization_id=organization_id,
                            finding_id=None,
                            recommendation_type="ai_transform",
                            title=f"{process['name']} にAI中間処理を導入",
                            description="数値確認、議事録整理、要約生成などの変換工程を AI に任せる候補です。",
                            priority_score=72,
                            roi_score=74,
                        ),
                        "_linked_finding_title": title,
                    }
                )

            meeting_steps = [step for step in steps if step.get("meeting_related")]
            if meeting_steps and any(
                any(keyword in " ".join(step.get("issue_tags", [])) or keyword in step.get("step_name", "")
                    for keyword in ["アジェンダ", "議事録", "録音", "アクション", "チェックリスト"])
                for step in meeting_steps
            ):
                title = f"{process['name']} の会議自動化余地"
                findings.append(
                    {
                        "organization_id": organization_id,
                        "process_id": process["id"],
                        "title": title,
                        "finding_type": "post_meeting_automation",
                        "severity": "medium",
                        "evidence": {"meeting_step_count": len(meeting_steps)},
                        "summary": "会議前準備や議事録整理、次アクション整理の自動化余地があります。",
                    }
                )
                recommendations.append(
                    {
                        **self.recommendation_service.build_recommendation(
                            organization_id=organization_id,
                            finding_id=None,
                            recommendation_type="post_meeting_automation",
                            title=f"{process['name']} の会議前後自動化",
                            description="アジェンダ作成、議事録化、アクション整理を自動化し、会議後の抜け漏れを減らします。",
                            priority_score=76,
                            roi_score=71,
                        ),
                        "_linked_finding_title": title,
                    }
                )

            if any(step.get("human_approval_candidate") for step in steps):
                title = f"{process['name']} の承認ゲート候補"
                findings.append(
                    {
                        "organization_id": organization_id,
                        "process_id": process["id"],
                        "title": title,
                        "finding_type": "approval_gate",
                        "severity": "medium",
                        "evidence": {"approval_candidate": True},
                        "summary": "タスクアサインや次アクション確定の前に、人の確認を残すべきポイントがあります。",
                    }
                )
                recommendations.append(
                    {
                        **self.recommendation_service.build_recommendation(
                            organization_id=organization_id,
                            finding_id=None,
                            recommendation_type="approval_gate",
                            title=f"{process['name']} に承認ゲートを設定",
                            description="自動化の前後で、人が最終確認するポイントを明示して安全性を保ちます。",
                            priority_score=68,
                            roi_score=55,
                        ),
                        "_linked_finding_title": title,
                    }
                )
        return findings

    def _diagnose_ai_enablement(
        self, organization_id: str, tools: list[dict], recommendations: list[dict]
    ) -> list[dict]:
        findings: list[dict] = []
        if tools and sum(1 for tool in tools if not tool.get("ai_enabled")) >= max(2, len(tools) // 2):
            title = "AI未活用ツールが多い"
            findings.append(
                {
                    "organization_id": organization_id,
                    "process_id": None,
                    "title": title,
                    "finding_type": "ai_transform",
                    "severity": "medium",
                    "evidence": {
                        "ai_disabled_tools": [tool["name"] for tool in tools if not tool.get("ai_enabled")]
                    },
                    "summary": "AIを活用していないツールが多く、業務改善余地があります。",
                }
            )
            recommendations.append(
                {
                    **self.recommendation_service.build_recommendation(
                        organization_id=organization_id,
                        finding_id=None,
                        recommendation_type="ai_transform",
                        title="AI活用余地のあるツールを優先棚卸し",
                        description="AI未利用のツール群について、要約・分類・生成などの中間処理導入余地を整理します。",
                        priority_score=60,
                        roi_score=58,
                    ),
                    "_linked_finding_title": title,
                }
            )
        return findings

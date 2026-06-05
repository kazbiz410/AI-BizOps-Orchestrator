from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

from app.schemas.interview import InterviewAnswerRead, InterviewQuestionRead


class OrganizationScopedRequest(BaseModel):
    organization_id: str


class GeneratedRecommendationContent(BaseModel):
    summary: str
    strengths: list[str]
    issues: list[str]
    proposal: str
    roi_hypothesis: str
    generated_by: str


class BlueprintItem(BaseModel):
    blueprint_type: str
    title: str
    content: str


class ImplementationTaskItem(BaseModel):
    title: str
    description: str
    priority: str


class BlueprintGenerationResponse(BaseModel):
    organization_id: str
    blueprints: list[BlueprintItem]
    implementation_tasks: list[ImplementationTaskItem]
    generated_by: str


class N8nDraftResponse(BaseModel):
    organization_id: str
    title: str
    draft_json: str
    generated_by: str


class OutputSnapshotResponse(BaseModel):
    organization_id: str
    recommendation_content: Optional[GeneratedRecommendationContent] = None
    blueprints: list[BlueprintItem]
    implementation_tasks: list[ImplementationTaskItem]
    n8n_draft: Optional[N8nDraftResponse] = None
    interview_questions: list[InterviewQuestionRead]
    interview_answers: list[InterviewAnswerRead]

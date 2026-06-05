from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

from app.schemas.common import TimestampedModel


class InterviewQuestionRead(TimestampedModel):
    organization_id: str
    process_id: Optional[str] = None
    assignee: Optional[str] = None
    question: str
    reason: Optional[str] = None
    slack_message: Optional[str] = None
    status: str


class InterviewAnswerCreate(BaseModel):
    question_id: str
    answer_text: str
    answered_by: Optional[str] = None


class InterviewAnswerRead(TimestampedModel):
    question_id: str
    answer_text: str
    answered_by: Optional[str] = None


class InterviewQuestionGenerationResponse(BaseModel):
    organization_id: str
    interview_questions: list[InterviewQuestionRead]
    generated_by: str


class InterviewAnswerAnalysisResponse(BaseModel):
    organization_id: str
    saved_answers: list[InterviewAnswerRead]
    note: str

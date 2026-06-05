from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

from app.schemas.common import TimestampedModel


class ProcessStepBase(BaseModel):
    process_id: str
    step_order: int
    step_name: str
    actor: Optional[str] = None
    input_data: Optional[str] = None
    output_data: Optional[str] = None
    tool_ids: list[str] = []
    manual_work: bool = False
    approval_required: bool = False
    ai_candidate: bool = False
    automation_candidate: bool = False
    human_approval_candidate: bool = False
    issue_tags: list[str] = []
    meeting_related: bool = False


class ProcessStepRead(TimestampedModel, ProcessStepBase):
    pass


class ProcessDecomposeResponse(BaseModel):
    process: dict
    steps: list[ProcessStepRead]

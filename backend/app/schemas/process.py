from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.common import TimestampedModel


class ProcessCreate(BaseModel):
    organization_id: str
    department_id: Optional[str] = None
    name: str = Field(min_length=1)
    process_type: Optional[str] = None
    raw_input_text: str = Field(min_length=1)
    kpi_summary: Optional[str] = None
    challenge_summary: Optional[str] = None


class ProcessRead(TimestampedModel):
    organization_id: str
    department_id: Optional[str] = None
    name: str
    process_type: Optional[str] = None
    raw_input_text: str
    kpi_summary: Optional[str] = None
    challenge_summary: Optional[str] = None

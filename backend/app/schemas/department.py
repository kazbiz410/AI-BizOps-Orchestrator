from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.common import TimestampedModel


class DepartmentCreate(BaseModel):
    organization_id: str
    name: str = Field(min_length=1)
    lead_name: Optional[str] = None


class DepartmentRead(TimestampedModel):
    organization_id: str
    name: str
    lead_name: Optional[str] = None

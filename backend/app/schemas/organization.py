from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.common import TimestampedModel


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=1)
    industry: Optional[str] = None
    employee_count: Optional[int] = Field(default=None, ge=1)


class OrganizationRead(TimestampedModel):
    name: str
    industry: Optional[str] = None
    employee_count: Optional[int] = None

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.common import TimestampedModel


class ToolCreate(BaseModel):
    organization_id: str
    name: str = Field(min_length=1)
    category: str = Field(min_length=1)
    monthly_cost: Decimal = Field(default=Decimal("0"))
    ai_enabled: bool = False
    vendor: Optional[str] = None


class ToolRead(TimestampedModel):
    organization_id: str
    name: str
    category: str
    monthly_cost: Decimal
    ai_enabled: bool
    vendor: Optional[str] = None

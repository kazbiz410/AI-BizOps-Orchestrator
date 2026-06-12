from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

from app.schemas.common import TimestampedModel


class RecommendationRead(TimestampedModel):
    organization_id: str
    finding_id: Optional[str] = None
    type: str
    title: str
    description: str
    priority_score: int
    roi_score: int


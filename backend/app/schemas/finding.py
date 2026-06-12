from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel

from app.schemas.common import TimestampedModel


class FindingRead(TimestampedModel):
    organization_id: str
    process_id: Optional[str] = None
    title: str
    finding_type: str
    severity: str
    evidence: dict[str, Any]
    summary: Optional[str] = None


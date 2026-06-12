from __future__ import annotations

from pydantic import BaseModel

from app.schemas.finding import FindingRead
from app.schemas.recommendation import RecommendationRead


class DiagnoseRequest(BaseModel):
    organization_id: str


class DiagnosisResponse(BaseModel):
    organization_id: str
    findings: list[FindingRead]
    recommendations: list[RecommendationRead]

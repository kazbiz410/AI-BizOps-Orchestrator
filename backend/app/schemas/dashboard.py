from __future__ import annotations

from pydantic import BaseModel


class DashboardItem(BaseModel):
    id: str
    title: str
    type: str


class DashboardResponse(BaseModel):
    organizations_count: int
    departments_count: int
    tools_count: int
    business_processes_count: int
    latest_findings: list[DashboardItem]
    latest_recommendations: list[DashboardItem]

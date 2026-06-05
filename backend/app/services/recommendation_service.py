from __future__ import annotations


class RecommendationService:
    """Generates prioritized recommendations from diagnosis results."""

    def build_recommendation(
        self,
        *,
        organization_id: str,
        finding_id: str | None,
        recommendation_type: str,
        title: str,
        description: str,
        priority_score: int,
        roi_score: int,
    ) -> dict:
        return {
            "organization_id": organization_id,
            "finding_id": finding_id,
            "type": recommendation_type,
            "title": title,
            "description": description,
            "priority_score": priority_score,
            "roi_score": roi_score,
        }

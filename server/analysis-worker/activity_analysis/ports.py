from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from activity_analysis.models import ActivityWindow, DailySummary, PeriodSummary, RiskScore


@dataclass(frozen=True)
class AnalysisResultBundle:
    daily_summaries: list[DailySummary]
    weekly_summaries: list[PeriodSummary]
    monthly_summaries: list[PeriodSummary]
    risk_scores: list[RiskScore]
    dashboard_summary: dict[str, Any]


class ActivityWindowInputPort(Protocol):
    def load_activity_windows(
        self,
        device_id: str,
        days: int,
        interval_minutes: int,
        regenerate: bool,
        seed: int,
    ) -> list[ActivityWindow]:
        """Return domain activity windows for one device."""


class AnalysisResultOutputPort(Protocol):
    def save_analysis_results(
        self,
        device_id: str,
        results: AnalysisResultBundle,
    ) -> None:
        """Persist all analysis outputs for one device."""


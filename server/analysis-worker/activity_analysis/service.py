from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from activity_analysis.analyzer import (
    build_dashboard_summary,
    calculate_risk_scores,
    summarize_daily,
    summarize_monthly,
    summarize_weekly,
)
from activity_analysis.ports import (
    ActivityWindowInputPort,
    AnalysisResultBundle,
    AnalysisResultOutputPort,
)


@dataclass(frozen=True)
class AnalysisRunReport:
    device_id: str
    input_path: Path | None
    daily_summary_count: int
    weekly_summary_count: int
    monthly_summary_count: int
    latest_risk_score: int
    latest_risk_level: str


class AnalysisWorkerService:
    def __init__(
        self,
        input_port: ActivityWindowInputPort,
        output_port: AnalysisResultOutputPort,
    ) -> None:
        self.input_port = input_port
        self.output_port = output_port

    def analyze_device(
        self,
        device_id: str,
        days: int,
        interval_minutes: int,
        regenerate: bool,
        seed: int,
    ) -> AnalysisRunReport:
        windows = self.input_port.load_activity_windows(
            device_id=device_id,
            days=days,
            interval_minutes=interval_minutes,
            regenerate=regenerate,
            seed=seed,
        )

        daily_summaries = summarize_daily(windows)
        risk_scores = calculate_risk_scores(daily_summaries)
        weekly_summaries = summarize_weekly(daily_summaries, risk_scores)
        monthly_summaries = summarize_monthly(daily_summaries, risk_scores)
        dashboard_summary = build_dashboard_summary(
            daily_summaries=daily_summaries,
            weekly_summaries=weekly_summaries,
            monthly_summaries=monthly_summaries,
            risks=risk_scores,
        )

        self.output_port.save_analysis_results(
            device_id,
            AnalysisResultBundle(
                daily_summaries=daily_summaries,
                weekly_summaries=weekly_summaries,
                monthly_summaries=monthly_summaries,
                risk_scores=risk_scores,
                dashboard_summary=dashboard_summary,
            ),
        )

        latest_risk = risk_scores[-1]
        input_path = None
        if hasattr(self.input_port, "input_path_for"):
            input_path = self.input_port.input_path_for(device_id)

        return AnalysisRunReport(
            device_id=device_id,
            input_path=input_path,
            daily_summary_count=len(daily_summaries),
            weekly_summary_count=len(weekly_summaries),
            monthly_summary_count=len(monthly_summaries),
            latest_risk_score=latest_risk.risk_score,
            latest_risk_level=latest_risk.risk_level,
        )


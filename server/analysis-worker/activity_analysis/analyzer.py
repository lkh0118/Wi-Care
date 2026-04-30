from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from statistics import mean

from activity_analysis.models import ActivityWindow, DailySummary, PeriodSummary, RiskScore


TIME_SLOTS = {
    "morning": range(6, 12),
    "afternoon": range(12, 18),
    "evening": range(18, 22),
    "night": list(range(22, 24)) + list(range(0, 6)),
}


def summarize_daily(windows: list[ActivityWindow]) -> list[DailySummary]:
    grouped: dict[tuple[str, date], list[ActivityWindow]] = defaultdict(list)
    for window in windows:
        grouped[(window.device_id, window.window_start.date())].append(window)

    summaries: list[DailySummary] = []
    for (device_id, target_date), day_windows in sorted(grouped.items(), key=lambda item: item[0]):
        ordered = sorted(day_windows, key=lambda item: item.window_start)
        slot_active_seconds = {slot: 0 for slot in TIME_SLOTS}
        slot_scores: dict[str, list[float]] = {slot: [] for slot in TIME_SLOTS}

        for window in ordered:
            slot = time_slot_for_hour(window.window_start.hour)
            slot_active_seconds[slot] += window.active_seconds
            slot_scores[slot].append(window.avg_movement_score)

        summaries.append(
            DailySummary(
                device_id=device_id,
                date=target_date,
                total_active_seconds=sum(window.active_seconds for window in ordered),
                total_inactive_seconds=sum(window.inactive_seconds for window in ordered),
                movement_events=sum(window.movement_events for window in ordered),
                avg_movement_score=round(mean(window.avg_movement_score for window in ordered), 2),
                max_movement_score=round(max(window.max_movement_score for window in ordered), 2),
                avg_presence_prob=round(mean(window.presence_prob for window in ordered), 3),
                avg_confidence=round(mean(window.confidence for window in ordered), 3),
                avg_signal_quality=round(mean(window.signal_quality for window in ordered), 3),
                longest_inactivity_seconds=calculate_longest_inactivity(ordered),
                time_slot_active_seconds=slot_active_seconds,
                time_slot_movement_score={
                    slot: round(mean(scores), 2) if scores else 0.0
                    for slot, scores in slot_scores.items()
                },
                window_count=len(ordered),
            )
        )

    return summaries


def summarize_weekly(daily_summaries: list[DailySummary], risks: list[RiskScore]) -> list[PeriodSummary]:
    risk_by_day = {(risk.device_id, risk.date): risk.risk_score for risk in risks}
    grouped: dict[tuple[str, date], list[DailySummary]] = defaultdict(list)

    for summary in daily_summaries:
        week_start = summary.date - timedelta(days=summary.date.weekday())
        grouped[(summary.device_id, week_start)].append(summary)

    return [
        _period_summary(
            device_id=device_id,
            period_type="weekly",
            period_start=week_start,
            summaries=sorted(summaries, key=lambda item: item.date),
            risk_by_day=risk_by_day,
        )
        for (device_id, week_start), summaries in sorted(grouped.items(), key=lambda item: item[0])
    ]


def summarize_monthly(daily_summaries: list[DailySummary], risks: list[RiskScore]) -> list[PeriodSummary]:
    risk_by_day = {(risk.device_id, risk.date): risk.risk_score for risk in risks}
    grouped: dict[tuple[str, date], list[DailySummary]] = defaultdict(list)

    for summary in daily_summaries:
        month_start = summary.date.replace(day=1)
        grouped[(summary.device_id, month_start)].append(summary)

    return [
        _period_summary(
            device_id=device_id,
            period_type="monthly",
            period_start=month_start,
            summaries=sorted(summaries, key=lambda item: item.date),
            risk_by_day=risk_by_day,
        )
        for (device_id, month_start), summaries in sorted(grouped.items(), key=lambda item: item[0])
    ]


def calculate_risk_scores(daily_summaries: list[DailySummary], baseline_days: int = 14) -> list[RiskScore]:
    grouped: dict[str, list[DailySummary]] = defaultdict(list)
    for summary in daily_summaries:
        grouped[summary.device_id].append(summary)

    risks: list[RiskScore] = []
    for device_id, summaries in grouped.items():
        ordered = sorted(summaries, key=lambda item: item.date)
        for index, summary in enumerate(ordered):
            baseline = ordered[max(0, index - baseline_days) : index]
            risk = _risk_for_day(summary, baseline)
            risks.append(
                RiskScore(
                    device_id=device_id,
                    date=summary.date,
                    risk_score=risk["risk_score"],
                    risk_level=_risk_level(risk["risk_score"]),
                    long_inactivity_score=risk["long_inactivity_score"],
                    daily_activity_drop_score=risk["daily_activity_drop_score"],
                    time_slot_deviation_score=risk["time_slot_deviation_score"],
                    night_pattern_abnormality_score=risk["night_pattern_abnormality_score"],
                    reasons=risk["reasons"],
                )
            )

    return risks


def build_dashboard_summary(
    daily_summaries: list[DailySummary],
    weekly_summaries: list[PeriodSummary],
    monthly_summaries: list[PeriodSummary],
    risks: list[RiskScore],
) -> dict[str, object]:
    latest_daily = max(daily_summaries, key=lambda item: item.date)
    latest_risk = max(risks, key=lambda item: item.date)
    recent_7_days = sorted(daily_summaries, key=lambda item: item.date)[-7:]

    return {
        "deviceId": latest_daily.device_id,
        "date": latest_daily.date.isoformat(),
        "today": {
            "totalActiveSeconds": latest_daily.total_active_seconds,
            "totalInactiveSeconds": latest_daily.total_inactive_seconds,
            "movementEvents": latest_daily.movement_events,
            "avgMovementScore": latest_daily.avg_movement_score,
            "longestInactivitySeconds": latest_daily.longest_inactivity_seconds,
            "avgSignalQuality": latest_daily.avg_signal_quality,
        },
        "risk": {
            "riskScore": latest_risk.risk_score,
            "riskLevel": latest_risk.risk_level,
            "reasons": latest_risk.reasons,
        },
        "recent7Days": [
            {
                "date": summary.date.isoformat(),
                "activeSeconds": summary.total_active_seconds,
                "movementEvents": summary.movement_events,
                "avgMovementScore": summary.avg_movement_score,
            }
            for summary in recent_7_days
        ],
        "latestWeeklySummary": weekly_summaries[-1] if weekly_summaries else None,
        "latestMonthlySummary": monthly_summaries[-1] if monthly_summaries else None,
    }


def calculate_longest_inactivity(windows: list[ActivityWindow]) -> int:
    longest = 0
    current = 0

    for window in sorted(windows, key=lambda item: item.window_start):
        window_seconds = int((window.window_end - window.window_start).total_seconds())
        inactive_ratio = window.inactive_seconds / max(1, window_seconds)
        if inactive_ratio >= 0.8 and window.presence_prob >= 0.55:
            current += window.inactive_seconds
        else:
            longest = max(longest, current)
            current = 0

    return max(longest, current)


def time_slot_for_hour(hour: int) -> str:
    for slot, hours in TIME_SLOTS.items():
        if hour in hours:
            return slot
    return "night"


def _period_summary(
    device_id: str,
    period_type: str,
    period_start: date,
    summaries: list[DailySummary],
    risk_by_day: dict[tuple[str, date], int],
) -> PeriodSummary:
    risk_values = [
        risk_by_day[(summary.device_id, summary.date)]
        for summary in summaries
        if (summary.device_id, summary.date) in risk_by_day
    ]

    return PeriodSummary(
        device_id=device_id,
        period_type=period_type,
        period_start=period_start,
        period_end=summaries[-1].date,
        total_active_seconds=sum(summary.total_active_seconds for summary in summaries),
        total_inactive_seconds=sum(summary.total_inactive_seconds for summary in summaries),
        movement_events=sum(summary.movement_events for summary in summaries),
        avg_daily_active_seconds=round(mean(summary.total_active_seconds for summary in summaries), 2),
        avg_movement_score=round(mean(summary.avg_movement_score for summary in summaries), 2),
        max_longest_inactivity_seconds=max(summary.longest_inactivity_seconds for summary in summaries),
        avg_risk_score=round(mean(risk_values), 2) if risk_values else None,
    )


def _risk_for_day(summary: DailySummary, baseline: list[DailySummary]) -> dict[str, object]:
    long_inactivity_score = min(100.0, summary.longest_inactivity_seconds / (8 * 60 * 60) * 100)

    if baseline:
        baseline_active = mean(item.total_active_seconds for item in baseline)
        activity_drop_ratio = max(0.0, (baseline_active - summary.total_active_seconds) / max(1, baseline_active))
        daily_activity_drop_score = min(100.0, activity_drop_ratio * 140)
        time_slot_deviation_score = _time_slot_deviation(summary, baseline)
        night_pattern_abnormality_score = _night_abnormality(summary, baseline)
    else:
        daily_activity_drop_score = 0.0
        time_slot_deviation_score = 0.0
        night_pattern_abnormality_score = 0.0

    risk_score = round(
        0.40 * long_inactivity_score
        + 0.25 * daily_activity_drop_score
        + 0.20 * time_slot_deviation_score
        + 0.15 * night_pattern_abnormality_score
    )

    reasons = _risk_reasons(
        long_inactivity_score,
        daily_activity_drop_score,
        time_slot_deviation_score,
        night_pattern_abnormality_score,
    )

    return {
        "risk_score": int(min(100, max(0, risk_score))),
        "long_inactivity_score": round(long_inactivity_score, 2),
        "daily_activity_drop_score": round(daily_activity_drop_score, 2),
        "time_slot_deviation_score": round(time_slot_deviation_score, 2),
        "night_pattern_abnormality_score": round(night_pattern_abnormality_score, 2),
        "reasons": reasons,
    }


def _time_slot_deviation(summary: DailySummary, baseline: list[DailySummary]) -> float:
    total = max(1, summary.total_active_seconds)
    score = 0.0

    for slot in TIME_SLOTS:
        today_ratio = summary.time_slot_active_seconds[slot] / total
        baseline_ratios = [
            item.time_slot_active_seconds[slot] / max(1, item.total_active_seconds)
            for item in baseline
        ]
        score += abs(today_ratio - mean(baseline_ratios))

    return min(100.0, score * 100)


def _night_abnormality(summary: DailySummary, baseline: list[DailySummary]) -> float:
    today_night = summary.time_slot_active_seconds["night"] / max(1, summary.total_active_seconds)
    baseline_night = mean(
        item.time_slot_active_seconds["night"] / max(1, item.total_active_seconds)
        for item in baseline
    )

    if today_night <= baseline_night:
        return 0.0
    return min(100.0, (today_night - baseline_night) * 220)


def _risk_reasons(
    long_inactivity_score: float,
    daily_activity_drop_score: float,
    time_slot_deviation_score: float,
    night_pattern_abnormality_score: float,
) -> list[str]:
    reasons: list[str] = []
    if long_inactivity_score >= 60:
        reasons.append("장시간 무활동 시간이 길다.")
    if daily_activity_drop_score >= 45:
        reasons.append("평소 대비 일일 활동량이 감소했다.")
    if time_slot_deviation_score >= 45:
        reasons.append("평소와 다른 시간대 활동 패턴이 나타났다.")
    if night_pattern_abnormality_score >= 45:
        reasons.append("야간 활동 비중이 평소보다 높다.")
    if not reasons:
        reasons.append("특이 위험 요인이 크지 않다.")
    return reasons


def _risk_level(score: int) -> str:
    if score >= 80:
        return "고위험"
    if score >= 60:
        return "경고"
    if score >= 30:
        return "주의"
    return "정상"


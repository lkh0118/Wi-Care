from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from typing import Any


@dataclass(frozen=True)
class ActivityWindow:
    device_id: str
    window_start: datetime
    window_end: datetime
    movement_score: float
    presence_prob: float
    activity_state: str
    confidence: float
    active_seconds: int
    inactive_seconds: int
    movement_events: int
    avg_movement_score: float
    max_movement_score: float
    min_movement_score: float
    signal_quality: float
    sample_count: int
    source: str
    schema_version: str


@dataclass(frozen=True)
class DailySummary:
    device_id: str
    date: date
    total_active_seconds: int
    total_inactive_seconds: int
    movement_events: int
    avg_movement_score: float
    max_movement_score: float
    avg_presence_prob: float
    avg_confidence: float
    avg_signal_quality: float
    longest_inactivity_seconds: int
    time_slot_active_seconds: dict[str, int]
    time_slot_movement_score: dict[str, float]
    window_count: int


@dataclass(frozen=True)
class PeriodSummary:
    device_id: str
    period_type: str
    period_start: date
    period_end: date
    total_active_seconds: int
    total_inactive_seconds: int
    movement_events: int
    avg_daily_active_seconds: float
    avg_movement_score: float
    max_longest_inactivity_seconds: int
    avg_risk_score: float | None = None


@dataclass(frozen=True)
class RiskScore:
    device_id: str
    date: date
    risk_score: int
    risk_level: str
    long_inactivity_score: float
    daily_activity_drop_score: float
    time_slot_deviation_score: float
    night_pattern_abnormality_score: float
    reasons: list[str] = field(default_factory=list)


def to_json_dict(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        data = asdict(value)
        return {key: to_json_dict(item) for key, item in data.items()}
    if isinstance(value, dict):
        return {key: to_json_dict(item) for key, item in value.items()}
    if isinstance(value, list):
        return [to_json_dict(item) for item in value]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value

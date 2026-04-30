from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone
from typing import Any


KST = timezone(timedelta(hours=9))


def generate_mock_activity_windows(
    device_id: str = "home-001",
    start_date: datetime | None = None,
    days: int = 30,
    interval_minutes: int = 60,
    seed: int = 42,
) -> list[dict[str, Any]]:
    """서버 수신 데이터 형식에 맞는 30일치 활동 구간 데이터를 생성한다."""
    random.seed(seed)

    if start_date is None:
        start_date = datetime(2026, 4, 2, 0, 0, tzinfo=KST)

    windows: list[dict[str, Any]] = []
    total_windows = int(days * 24 * 60 / interval_minutes)

    for index in range(total_windows):
        window_start = start_date + timedelta(minutes=index * interval_minutes)
        window_end = window_start + timedelta(minutes=interval_minutes)
        day_index = (window_start.date() - start_date.date()).days
        hour = window_start.hour

        profile = _profile_for_hour(hour)
        anomaly = _anomaly_for_day(day_index, hour)

        movement_score = _clamp(profile["movement"] + anomaly["movement_delta"] + random.gauss(0, 5), 0, 100)
        presence_prob = _clamp(profile["presence"] + anomaly["presence_delta"] + random.gauss(0, 0.04), 0, 1)
        signal_quality = _clamp(0.92 + anomaly["signal_delta"] + random.gauss(0, 0.03), 0, 1)

        interval_seconds = interval_minutes * 60
        active_ratio = _clamp((movement_score / 100) * presence_prob + anomaly["active_ratio_delta"], 0, 1)
        active_seconds = int(interval_seconds * active_ratio)
        inactive_seconds = interval_seconds - active_seconds
        movement_events = max(0, int(active_seconds / 180 + random.gauss(1, 1)))

        activity_state = _classify_state(movement_score, presence_prob, inactive_seconds, interval_seconds)
        confidence = _clamp(0.55 + signal_quality * 0.35 + presence_prob * 0.08 - anomaly["confidence_penalty"], 0, 1)

        windows.append(
            {
                "deviceId": device_id,
                "windowStart": window_start.isoformat(),
                "windowEnd": window_end.isoformat(),
                "movementScore": round(movement_score, 2),
                "presenceProb": round(presence_prob, 3),
                "activityState": activity_state,
                "confidence": round(confidence, 3),
                "activeSeconds": active_seconds,
                "inactiveSeconds": inactive_seconds,
                "movementEvents": movement_events,
                "avgMovementScore": round(movement_score * random.uniform(0.88, 1.02), 2),
                "maxMovementScore": round(_clamp(movement_score + random.uniform(5, 22), 0, 100), 2),
                "minMovementScore": round(_clamp(movement_score - random.uniform(5, 18), 0, 100), 2),
                "signalQuality": round(signal_quality, 3),
                "sampleCount": max(1, int(interval_seconds / 5)),
                "source": "mock",
                "schemaVersion": "1.0",
            }
        )

    return windows


def _profile_for_hour(hour: int) -> dict[str, float]:
    if 0 <= hour < 6:
        return {"movement": 5, "presence": 0.86}
    if 6 <= hour < 9:
        return {"movement": 42, "presence": 0.92}
    if 9 <= hour < 12:
        return {"movement": 30, "presence": 0.82}
    if 12 <= hour < 18:
        return {"movement": 34, "presence": 0.78}
    if 18 <= hour < 22:
        return {"movement": 48, "presence": 0.91}
    return {"movement": 14, "presence": 0.88}


def _anomaly_for_day(day_index: int, hour: int) -> dict[str, float]:
    anomaly = {
        "movement_delta": 0.0,
        "presence_delta": 0.0,
        "signal_delta": 0.0,
        "active_ratio_delta": 0.0,
        "confidence_penalty": 0.0,
    }

    # 최근 5일은 활동량 저하 상황을 의도적으로 섞는다.
    if day_index >= 25:
        anomaly["movement_delta"] -= 13
        anomaly["active_ratio_delta"] -= 0.12

    # 특정 날짜에는 장시간 무활동을 만든다.
    if day_index in {9, 21, 28} and 10 <= hour < 17:
        anomaly["movement_delta"] -= 28
        anomaly["active_ratio_delta"] -= 0.22

    # 특정 야간에는 평소보다 큰 움직임을 만들어 야간 이상 패턴을 테스트한다.
    if day_index in {14, 27} and 1 <= hour < 4:
        anomaly["movement_delta"] += 40
        anomaly["active_ratio_delta"] += 0.35

    # 신호 품질 저하 상황도 일부 포함한다.
    if day_index in {6, 18} and 13 <= hour < 16:
        anomaly["signal_delta"] -= 0.35
        anomaly["confidence_penalty"] += 0.18

    return anomaly


def _classify_state(
    movement_score: float,
    presence_prob: float,
    inactive_seconds: int,
    interval_seconds: int,
) -> str:
    if presence_prob < 0.35:
        return "empty"
    if inactive_seconds >= interval_seconds * 0.9 and presence_prob >= 0.65:
        return "warning"
    if movement_score >= 35:
        return "moving"
    return "present"


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


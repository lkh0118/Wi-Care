from __future__ import annotations

from typing import Any


def build_dashboard_view_model(
    data: dict[str, Any],
    devices: list[str],
    selected_device_id: str,
    updated_at: str,
) -> dict[str, Any]:
    rows = build_metric_rows(data, updated_at)
    return {
        "status": "ok",
        "deviceId": data.get("deviceId"),
        "devices": devices,
        "selectedDeviceId": selected_device_id,
        "analysisDate": data.get("date"),
        "updatedAt": updated_at,
        "riskReasons": data.get("risk", {}).get("reasons", []),
        "rows": rows,
        "leds": rows,
    }


def build_metric_rows(data: dict[str, Any], updated_at: str) -> list[dict[str, Any]]:
    today = data.get("today", {})
    risk = data.get("risk", {})
    weekly = data.get("latestWeeklySummary") or {}
    monthly = data.get("latestMonthlySummary") or {}

    metrics = [
        {
            "key": "riskScore",
            "name": "위험 점수",
            "value": risk.get("riskScore", 0),
            "unit": "점",
            "direction": "lower",
            "thresholds": [29, 59, 79],
        },
        {
            "key": "totalActiveSeconds",
            "name": "오늘 총 활동 시간",
            "value": today.get("totalActiveSeconds", 0),
            "unit": "시간",
            "direction": "higher",
            "thresholds": [14400, 7200, 3600],
            "formatter": "duration",
        },
        {
            "key": "longestInactivitySeconds",
            "name": "최장 무활동 시간",
            "value": today.get("longestInactivitySeconds", 0),
            "unit": "시간",
            "direction": "lower",
            "thresholds": [7200, 14400, 28800],
            "formatter": "duration",
        },
        {
            "key": "movementEvents",
            "name": "오늘 움직임 이벤트",
            "value": today.get("movementEvents", 0),
            "unit": "회",
            "direction": "higher",
            "thresholds": [100, 60, 30],
        },
        {
            "key": "avgMovementScore",
            "name": "평균 움직임 점수",
            "value": today.get("avgMovementScore", 0),
            "unit": "점",
            "direction": "higher",
            "thresholds": [30, 20, 10],
        },
        {
            "key": "avgSignalQuality",
            "name": "평균 신호 품질",
            "value": today.get("avgSignalQuality", 0),
            "unit": "",
            "direction": "higher",
            "thresholds": [0.85, 0.7, 0.5],
        },
        {
            "key": "weeklyAvgRiskScore",
            "name": "주간 평균 위험 점수",
            "value": weekly.get("avg_risk_score", 0),
            "unit": "점",
            "direction": "lower",
            "thresholds": [29, 59, 79],
        },
        {
            "key": "monthlyAvgRiskScore",
            "name": "월별 평균 위험 점수",
            "value": monthly.get("avg_risk_score", 0),
            "unit": "점",
            "direction": "lower",
            "thresholds": [29, 59, 79],
        },
    ]

    return [_build_metric_row(metric, updated_at) for metric in metrics]


def _build_metric_row(metric: dict[str, Any], updated_at: str) -> dict[str, Any]:
    value = float(metric["value"] or 0)
    level = _classify_level(value, metric["direction"], metric["thresholds"])
    formatter = metric.get("formatter")

    return {
        "key": metric["key"],
        "name": metric["name"],
        "updatedAt": updated_at,
        "rawValue": round(value, 3),
        "displayValue": _format_value(value, metric["unit"], formatter),
        "level": level,
        "levelLabel": _level_label(level),
        "criteria": _criteria_text(metric["direction"], metric["thresholds"], metric["unit"], formatter),
    }


def _classify_level(value: float, direction: str, thresholds: list[float]) -> str:
    normal, caution, warning = thresholds

    if direction == "lower":
        if value <= normal:
            return "normal"
        if value <= caution:
            return "caution"
        if value <= warning:
            return "warning"
        return "danger"

    if value >= normal:
        return "normal"
    if value >= caution:
        return "caution"
    if value >= warning:
        return "warning"
    return "danger"


def _level_label(level: str) -> str:
    return {
        "normal": "정상",
        "caution": "주의",
        "warning": "경고",
        "danger": "위험",
    }[level]


def _format_value(value: float, unit: str, formatter: str | None = None) -> str:
    if formatter == "duration":
        total_seconds = int(value)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return f"{hours}시간 {minutes}분"
    if unit:
        return f"{value:g}{unit}"
    return f"{value:g}"


def _criteria_text(
    direction: str,
    thresholds: list[float],
    unit: str,
    formatter: str | None = None,
) -> dict[str, str]:
    normal, caution, warning = thresholds

    if direction == "lower":
        return {
            "normal": f"{_format_value(normal, unit, formatter)} 이하",
            "caution": f"{_format_value(normal, unit, formatter)} 초과 ~ {_format_value(caution, unit, formatter)}",
            "warning": f"{_format_value(caution, unit, formatter)} 초과 ~ {_format_value(warning, unit, formatter)}",
            "danger": f"{_format_value(warning, unit, formatter)} 초과",
        }

    return {
        "normal": f"{_format_value(normal, unit, formatter)} 이상",
        "caution": f"{_format_value(caution, unit, formatter)} 이상 ~ {_format_value(normal, unit, formatter)} 미만",
        "warning": f"{_format_value(warning, unit, formatter)} 이상 ~ {_format_value(caution, unit, formatter)} 미만",
        "danger": f"{_format_value(warning, unit, formatter)} 미만",
    }


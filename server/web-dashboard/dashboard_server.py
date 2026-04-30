from __future__ import annotations

import json
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
ANALYSIS_OUTPUT_DIR = BASE_DIR.parent / "analysis-worker" / "output"
DEFAULT_DEVICE_ID = "home-001"


class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        path = urlparse(self.path).path

        if path in {"/", "/index.html"}:
            self._send_file(STATIC_DIR / "index.html", "text/html; charset=utf-8")
            return
        if path == "/static/dashboard.css":
            self._send_file(STATIC_DIR / "dashboard.css", "text/css; charset=utf-8")
            return
        if path == "/static/dashboard.js":
            self._send_file(STATIC_DIR / "dashboard.js", "application/javascript; charset=utf-8")
            return
        if path == "/api/dashboard":
            self._send_dashboard_api()
            return

        self.send_error(HTTPStatus.NOT_FOUND, "요청한 경로를 찾을 수 없습니다.")

    def log_message(self, format: str, *args: object) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {self.address_string()} {format % args}")

    def _send_file(self, path: Path, content_type: str) -> None:
        if not path.exists():
            self.send_error(HTTPStatus.NOT_FOUND, "파일을 찾을 수 없습니다.")
            return

        body = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_dashboard_api(self) -> None:
        devices = list_available_devices()
        if not devices:
            self._send_json(
                {
                    "status": "error",
                    "message": "분석 결과 폴더가 없습니다. server/analysis-worker/run_analysis.py를 먼저 실행하세요.",
                    "devices": [],
                    "rows": [],
                    "leds": [],
                },
                status=HTTPStatus.NOT_FOUND,
            )
            return

        query = parse_qs(urlparse(self.path).query)
        requested_device_id = query.get("deviceId", [DEFAULT_DEVICE_ID])[0]
        device_id = requested_device_id if requested_device_id in devices else devices[0]
        analysis_output = ANALYSIS_OUTPUT_DIR / device_id / "dashboard_summary.json"

        if not analysis_output.exists():
            self._send_json(
                {
                    "status": "error",
                    "message": f"{device_id} 분석 결과 파일이 없습니다.",
                    "devices": devices,
                    "selectedDeviceId": device_id,
                    "rows": [],
                    "leds": [],
                },
                status=HTTPStatus.NOT_FOUND,
            )
            return

        raw = json.loads(analysis_output.read_text(encoding="utf-8"))
        modified_at = datetime.fromtimestamp(analysis_output.stat().st_mtime).astimezone()
        rows = build_metric_rows(raw, modified_at.isoformat(timespec="seconds"))
        response = {
            "status": "ok",
            "deviceId": raw.get("deviceId"),
            "devices": devices,
            "selectedDeviceId": device_id,
            "analysisDate": raw.get("date"),
            "updatedAt": modified_at.isoformat(timespec="seconds"),
            "riskReasons": raw.get("risk", {}).get("reasons", []),
            "rows": rows,
            "leds": rows,
        }
        self._send_json(response)

    def _send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


def list_available_devices() -> list[str]:
    if not ANALYSIS_OUTPUT_DIR.exists():
        return []

    devices = [
        path.name
        for path in ANALYSIS_OUTPUT_DIR.iterdir()
        if path.is_dir() and (path / "dashboard_summary.json").exists()
    ]
    return sorted(devices)


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

    return [build_metric_row(metric, updated_at) for metric in metrics]


def build_metric_row(metric: dict[str, Any], updated_at: str) -> dict[str, Any]:
    value = float(metric["value"] or 0)
    level = classify_level(value, metric["direction"], metric["thresholds"])
    formatter = metric.get("formatter")

    return {
        "key": metric["key"],
        "name": metric["name"],
        "updatedAt": updated_at,
        "rawValue": round(value, 3),
        "displayValue": format_value(value, metric["unit"], formatter),
        "level": level,
        "levelLabel": level_label(level),
        "criteria": criteria_text(metric["direction"], metric["thresholds"], metric["unit"], formatter),
    }


def classify_level(value: float, direction: str, thresholds: list[float]) -> str:
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


def level_label(level: str) -> str:
    return {
        "normal": "정상",
        "caution": "주의",
        "warning": "경고",
        "danger": "위험",
    }[level]


def format_value(value: float, unit: str, formatter: str | None = None) -> str:
    if formatter == "duration":
        total_seconds = int(value)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return f"{hours}시간 {minutes}분"
    if unit:
        return f"{value:g}{unit}"
    return f"{value:g}"


def criteria_text(direction: str, thresholds: list[float], unit: str, formatter: str | None = None) -> dict[str, str]:
    normal, caution, warning = thresholds

    if direction == "lower":
        return {
            "normal": f"{format_value(normal, unit, formatter)} 이하",
            "caution": f"{format_value(normal, unit, formatter)} 초과 ~ {format_value(caution, unit, formatter)}",
            "warning": f"{format_value(caution, unit, formatter)} 초과 ~ {format_value(warning, unit, formatter)}",
            "danger": f"{format_value(warning, unit, formatter)} 초과",
        }

    return {
        "normal": f"{format_value(normal, unit, formatter)} 이상",
        "caution": f"{format_value(caution, unit, formatter)} 이상 ~ {format_value(normal, unit, formatter)} 미만",
        "warning": f"{format_value(warning, unit, formatter)} 이상 ~ {format_value(caution, unit, formatter)} 미만",
        "danger": f"{format_value(warning, unit, formatter)} 미만",
    }


def main() -> None:
    host = "127.0.0.1"
    port = 8080
    startup_log = BASE_DIR / "dashboard_startup.log"
    try:
        server = ThreadingHTTPServer((host, port), DashboardHandler)
        startup_log.write_text(f"대시보드 시작 완료: http://{host}:{port}\n", encoding="utf-8")
        print(f"Wi-Care 대시보드 실행 중: http://{host}:{port}", flush=True)
        print("종료하려면 Ctrl+C를 누르세요.", flush=True)
        server.serve_forever()
    except Exception as exc:
        startup_log.write_text(f"대시보드 시작 실패: {exc}\n", encoding="utf-8")
        raise


if __name__ == "__main__":
    main()

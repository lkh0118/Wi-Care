from __future__ import annotations

import json
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from dashboard_view_model import build_dashboard_view_model


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

        data = json.loads(analysis_output.read_text(encoding="utf-8"))
        updated_at = datetime.fromtimestamp(analysis_output.stat().st_mtime).astimezone().isoformat(timespec="seconds")
        self._send_json(build_dashboard_view_model(data, devices, device_id, updated_at))

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

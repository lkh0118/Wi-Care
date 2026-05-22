from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from activity_analysis.mock_data_generator import generate_mock_activity_windows
from activity_analysis.models import ActivityWindow, to_json_dict
from activity_analysis.ports import AnalysisResultBundle


class MockActivityWindowFileAdapter:
    def __init__(self, sample_data_dir: Path) -> None:
        self.sample_data_dir = sample_data_dir

    def load_activity_windows(
        self,
        device_id: str,
        days: int,
        interval_minutes: int,
        regenerate: bool,
        seed: int,
    ) -> list[ActivityWindow]:
        device_sample_dir = self.sample_data_dir / device_id
        device_sample_dir.mkdir(parents=True, exist_ok=True)

        input_path = device_sample_dir / "activity_windows_30d.json"
        if regenerate or not input_path.exists():
            payload = generate_mock_activity_windows(
                device_id=device_id,
                days=days,
                interval_minutes=interval_minutes,
                seed=seed,
            )
            self._write_json(input_path, payload)
        else:
            payload = self._read_json(input_path)

        return [_activity_window_from_payload(item) for item in payload]

    def input_path_for(self, device_id: str) -> Path:
        return self.sample_data_dir / device_id / "activity_windows_30d.json"

    @staticmethod
    def _read_json(path: Path) -> list[dict[str, Any]]:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)

    @staticmethod
    def _write_json(path: Path, data: Any) -> None:
        with path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
            file.write("\n")


class JsonAnalysisResultFileAdapter:
    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir

    def save_analysis_results(self, device_id: str, results: AnalysisResultBundle) -> None:
        device_output_dir = self.output_dir / device_id
        device_output_dir.mkdir(parents=True, exist_ok=True)

        self._write_json(device_output_dir / "daily_summaries.json", to_json_dict(results.daily_summaries))
        self._write_json(device_output_dir / "weekly_summaries.json", to_json_dict(results.weekly_summaries))
        self._write_json(device_output_dir / "monthly_summary.json", to_json_dict(results.monthly_summaries))
        self._write_json(device_output_dir / "risk_scores.json", to_json_dict(results.risk_scores))
        self._write_json(device_output_dir / "dashboard_summary.json", to_json_dict(results.dashboard_summary))

    @staticmethod
    def _write_json(path: Path, data: Any) -> None:
        with path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
            file.write("\n")


def _activity_window_from_payload(payload: dict[str, Any]) -> ActivityWindow:
    return ActivityWindow(
        device_id=str(payload["deviceId"]),
        window_start=datetime.fromisoformat(payload["windowStart"]),
        window_end=datetime.fromisoformat(payload["windowEnd"]),
        movement_score=float(payload["movementScore"]),
        presence_prob=float(payload["presenceProb"]),
        activity_state=str(payload["activityState"]),
        confidence=float(payload["confidence"]),
        active_seconds=int(payload["activeSeconds"]),
        inactive_seconds=int(payload["inactiveSeconds"]),
        movement_events=int(payload["movementEvents"]),
        avg_movement_score=float(payload.get("avgMovementScore", payload["movementScore"])),
        max_movement_score=float(payload.get("maxMovementScore", payload["movementScore"])),
        min_movement_score=float(payload.get("minMovementScore", payload["movementScore"])),
        signal_quality=float(payload["signalQuality"]),
        sample_count=int(payload.get("sampleCount", 0)),
        source=str(payload.get("source", "unknown")),
        schema_version=str(payload["schemaVersion"]),
    )


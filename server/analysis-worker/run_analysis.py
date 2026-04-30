from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from activity_analysis.analyzer import (
    build_dashboard_summary,
    calculate_risk_scores,
    summarize_daily,
    summarize_monthly,
    summarize_weekly,
)
from activity_analysis.mock_data_generator import generate_mock_activity_windows
from activity_analysis.models import ActivityWindow, to_json_dict


BASE_DIR = Path(__file__).resolve().parent
SAMPLE_DATA_DIR = BASE_DIR / "sample-data"
OUTPUT_DIR = BASE_DIR / "output"
DEFAULT_DEVICE_IDS = ["home-001", "home-002"]


def main() -> None:
    args = parse_args()
    SAMPLE_DATA_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)

    for index, device_id in enumerate(args.device_ids):
        analyze_device(
            device_id=device_id,
            days=args.days,
            interval_minutes=args.interval_minutes,
            regenerate=args.regenerate,
            seed=args.seed + index,
        )


def analyze_device(
    device_id: str,
    days: int,
    interval_minutes: int,
    regenerate: bool,
    seed: int,
) -> None:
    device_sample_dir = SAMPLE_DATA_DIR / device_id
    device_output_dir = OUTPUT_DIR / device_id
    device_sample_dir.mkdir(parents=True, exist_ok=True)
    device_output_dir.mkdir(parents=True, exist_ok=True)

    input_path = device_sample_dir / "activity_windows_30d.json"
    if regenerate or not input_path.exists():
        windows_payload = generate_mock_activity_windows(
            device_id=device_id,
            days=days,
            interval_minutes=interval_minutes,
            seed=seed,
        )
        write_json(input_path, windows_payload)
    else:
        windows_payload = read_json(input_path)

    windows = [ActivityWindow.from_api_payload(item) for item in windows_payload]
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

    write_json(device_output_dir / "daily_summaries.json", to_json_dict(daily_summaries))
    write_json(device_output_dir / "weekly_summaries.json", to_json_dict(weekly_summaries))
    write_json(device_output_dir / "monthly_summary.json", to_json_dict(monthly_summaries))
    write_json(device_output_dir / "risk_scores.json", to_json_dict(risk_scores))
    write_json(device_output_dir / "dashboard_summary.json", to_json_dict(dashboard_summary))

    latest_risk = risk_scores[-1]
    print(f"[{device_id}] Mock 입력 데이터: {input_path}")
    print(f"일일 요약 개수: {len(daily_summaries)}")
    print(f"주간 요약 개수: {len(weekly_summaries)}")
    print(f"월별 요약 개수: {len(monthly_summaries)}")
    print(f"최근 위험 점수: {latest_risk.risk_score} / {latest_risk.risk_level}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Wi-Care 서버 활동 패턴 분석 프로토타입")
    parser.add_argument(
        "--device-id",
        dest="device_ids",
        action="append",
        default=None,
        help="분석할 장치 ID. 여러 번 지정할 수 있으며 기본값은 home-001, home-002",
    )
    parser.add_argument("--days", type=int, default=30, help="생성할 Mock 데이터 일수")
    parser.add_argument("--interval-minutes", type=int, default=60, help="Mock 활동 구간 길이")
    parser.add_argument("--seed", type=int, default=42, help="Mock 데이터 생성 시드")
    parser.add_argument("--regenerate", action="store_true", help="기존 샘플 데이터를 무시하고 다시 생성")
    args = parser.parse_args()
    if args.device_ids is None:
        args.device_ids = DEFAULT_DEVICE_IDS
    return args


def read_json(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def write_json(path: Path, data: Any) -> None:
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
        file.write("\n")


if __name__ == "__main__":
    main()

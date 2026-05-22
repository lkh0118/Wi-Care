from __future__ import annotations

import argparse
from pathlib import Path

from activity_analysis.adapters import JsonAnalysisResultFileAdapter, MockActivityWindowFileAdapter
from activity_analysis.service import AnalysisWorkerService


BASE_DIR = Path(__file__).resolve().parent
SAMPLE_DATA_DIR = BASE_DIR / "sample-data"
OUTPUT_DIR = BASE_DIR / "output"
DEFAULT_DEVICE_IDS = ["home-001", "home-002"]


def main() -> None:
    args = parse_args()
    SAMPLE_DATA_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)

    service = AnalysisWorkerService(
        input_port=MockActivityWindowFileAdapter(SAMPLE_DATA_DIR),
        output_port=JsonAnalysisResultFileAdapter(OUTPUT_DIR),
    )

    for index, device_id in enumerate(args.device_ids):
        report = service.analyze_device(
            device_id=device_id,
            days=args.days,
            interval_minutes=args.interval_minutes,
            regenerate=args.regenerate,
            seed=args.seed + index,
        )
        print(f"[{report.device_id}] Mock 입력 데이터: {report.input_path}")
        print(f"일일 요약 개수: {report.daily_summary_count}")
        print(f"주간 요약 개수: {report.weekly_summary_count}")
        print(f"월별 요약 개수: {report.monthly_summary_count}")
        print(f"최근 위험 점수: {report.latest_risk_score} / {report.latest_risk_level}")


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


if __name__ == "__main__":
    main()

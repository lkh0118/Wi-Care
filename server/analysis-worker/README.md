# 서버 분석 Worker 프로토타입

이 폴더는 서버가 수신한 `activity_windows` 데이터를 기반으로 일일, 주간, 월별 활동 요약과 위험 점수를 계산하는 Python 프로토타입이다.

현재 구현은 PostgreSQL 연결 전 단계이므로 JSON 파일을 입력으로 사용한다.

## 실행 방법

```powershell
cd server/analysis-worker
python run_analysis.py
```

기본 실행 시 다음 작업을 수행한다.

1. `home-001`, `home-002`의 30일치 Mock `activity_windows` 데이터 생성
2. 일일 요약 계산
3. 주간 요약 계산
4. 월별 요약 계산
5. 위험 점수 계산
6. 결과 JSON 파일 저장

## 생성 파일

```text
sample-data/{deviceId}/activity_windows_30d.json
output/{deviceId}/daily_summaries.json
output/{deviceId}/weekly_summaries.json
output/{deviceId}/monthly_summary.json
output/{deviceId}/risk_scores.json
output/{deviceId}/dashboard_summary.json
```

## 현재 기준

- Mock 데이터는 1시간 구간 단위로 생성한다.
- 사람/기기별 데이터는 `{deviceId}` 폴더로 분리해 저장한다.
- 실제 서버 API에서는 1분 단위 수신을 우선 고려하지만, 분석 로직은 구간 길이에 의존하지 않도록 `activeSeconds`, `inactiveSeconds`, `movementEvents`를 사용한다.
- 서버는 Raw CSI가 아니라 PC Python 분석 프로그램의 요약 분석 데이터를 입력으로 받는다.

## 특정 장치만 생성하기

```powershell
python run_analysis.py --regenerate --device-id home-003
```

여러 장치를 생성하려면 `--device-id`를 반복해서 사용한다.

```powershell
python run_analysis.py --regenerate --device-id home-001 --device-id home-002
```

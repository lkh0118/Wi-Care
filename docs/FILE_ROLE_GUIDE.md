# 파일 역할 정리

이 문서는 현재 Wi-Care 프로젝트에 존재하는 주요 파일과 폴더가 어떤 역할을 하는지 정리한다.

현재 구현된 범위는 서버 분석 Worker 프로토타입과 웹 대시보드 프로토타입이다. ESP32-C5 펌웨어, PC Python 분석기 본 구현, WPF UI, FastAPI 서버, PostgreSQL 연동은 아직 본격 구현 전이다.

## 전체 실행 흐름

현재 프로토타입의 흐름은 다음과 같다.

```text
server/analysis-worker/run_analysis.py
  ↓
30일 Mock activity_windows 생성
  ↓
일일/주간/월별 요약 및 위험 점수 계산
  ↓
server/analysis-worker/output/{deviceId}/dashboard_summary.json 저장
  ↓
server/web-dashboard/dashboard_server.py 실행
  ↓
브라우저에서 http://127.0.0.1:8080 접속
  ↓
드롭다운에서 home-001 또는 home-002 선택
  ↓
표와 LED 상태가 2초마다 자동 갱신
```

## 루트 파일

| 파일 | 역할 |
| --- | --- |
| `README.md` | 프로젝트 전체 개요, 역할 분담, 실행 방법, 서버 분석 Worker와 웹 대시보드 사용법을 설명한다. |
| `PROJECT_STATUS.md` | 프로젝트 변경 사항을 날짜별로 기록하는 작업 로그다. 기능 추가, 수정 파일, 남은 작업, 문제점, 인터페이스 변경 여부를 기록한다. |
| `.gitignore` | Python 캐시, 가상환경, 환경변수 파일, 로그 파일이 Git에 들어가지 않도록 제외한다. |

## docs 폴더

| 파일 | 역할 |
| --- | --- |
| `docs/INTERFACES.md` | ESP32-C5, PC Python 분석기, WPF UI, 외부 서버, 웹 대시보드 사이의 인터페이스 초안을 정리한다. |
| `docs/MOCK_DATA_PLAN.md` | ESP32-C5 실제 데이터 없이 개발하기 위한 Mock 데이터 전략과 Python 분석기 구조 초안을 설명한다. |
| `docs/SERVER_INPUT_DATA.md` | 서버가 PC Python 분석기로부터 받아야 하는 데이터 형식, API 후보, 필수 필드, PostgreSQL 테이블 초안을 정리한다. |
| `docs/DEVELOPMENT_TODO.md` | 프로젝트 개발 단계를 체크리스트로 정리한다. |
| `docs/FILE_ROLE_GUIDE.md` | 현재 파일과 폴더의 역할을 설명하는 이 문서다. |

## 서버 분석 Worker

경로: `server/analysis-worker/`

서버 분석 Worker는 서버가 수신했다고 가정하는 `activity_windows` 데이터를 기반으로 활동 패턴을 분석한다. 현재는 PostgreSQL 대신 JSON 파일을 입력과 출력으로 사용한다.

### 실행 파일

| 파일 | 역할 |
| --- | --- |
| `server/analysis-worker/run_analysis.py` | 분석 Worker의 실행 진입점이다. `home-001`, `home-002`의 30일 Mock 데이터를 생성하고, 일일/주간/월별 요약과 위험 점수를 계산한 뒤 JSON 파일로 저장한다. |
| `server/analysis-worker/README.md` | 분석 Worker 실행 방법과 생성 파일 구조를 설명한다. |

### 분석 패키지

경로: `server/analysis-worker/activity_analysis/`

| 파일 | 역할 |
| --- | --- |
| `activity_analysis/__init__.py` | `activity_analysis` 폴더를 Python 패키지로 인식시키는 파일이다. |
| `activity_analysis/models.py` | `ActivityWindow`, `DailySummary`, `PeriodSummary`, `RiskScore` 데이터 모델을 정의한다. JSON 직렬화를 위한 `to_json_dict()`도 포함한다. |
| `activity_analysis/mock_data_generator.py` | `home-001`, `home-002` 같은 장치별 30일 Mock `activity_windows` 데이터를 생성한다. 일반 활동, 장시간 무활동, 활동량 저하, 야간 이상 활동, 신호 품질 저하 상황을 일부 포함한다. |
| `activity_analysis/analyzer.py` | 일일 요약, 주간 요약, 월별 요약, 위험 점수 계산, 대시보드 요약 생성 로직을 담당한다. |

### Mock 입력 데이터

경로: `server/analysis-worker/sample-data/{deviceId}/`

| 파일 | 역할 |
| --- | --- |
| `sample-data/home-001/activity_windows_30d.json` | `home-001`의 30일 Mock 활동 구간 데이터다. 서버가 실제로 받을 `POST /api/activity/windows` 요청 데이터를 흉내 낸다. |
| `sample-data/home-002/activity_windows_30d.json` | `home-002`의 30일 Mock 활동 구간 데이터다. 다중 사람/기기 선택 테스트를 위해 사용한다. |

현재 파일 저장 표준은 다음과 같다.

```text
sample-data/{deviceId}/activity_windows_30d.json
```

### 분석 결과 데이터

경로: `server/analysis-worker/output/{deviceId}/`

각 장치별 분석 결과는 장치 폴더 안에 따로 저장한다.

| 파일 | 역할 |
| --- | --- |
| `output/{deviceId}/daily_summaries.json` | 30일치 일일 요약 결과다. 하루 총 활동 시간, 무활동 시간, 움직임 이벤트 수, 평균 움직임 점수, 최장 무활동 시간 등이 들어 있다. |
| `output/{deviceId}/weekly_summaries.json` | 주간 단위 요약 결과다. 주간 총 활동 시간, 주간 움직임 이벤트 수, 평균 위험 점수 등을 저장한다. |
| `output/{deviceId}/monthly_summary.json` | 월별 요약 결과다. 현재 30일 Mock 데이터가 4월과 5월에 걸쳐 있어 월별 항목이 나뉠 수 있다. |
| `output/{deviceId}/risk_scores.json` | 날짜별 위험 점수와 위험 단계, 위험 사유를 저장한다. |
| `output/{deviceId}/dashboard_summary.json` | 웹 대시보드가 직접 읽는 최종 요약 파일이다. 오늘 요약, 위험 점수, 최근 7일 데이터, 최신 주간/월별 요약이 들어 있다. |

현재 파일 저장 표준은 다음과 같다.

```text
output/{deviceId}/daily_summaries.json
output/{deviceId}/weekly_summaries.json
output/{deviceId}/monthly_summary.json
output/{deviceId}/risk_scores.json
output/{deviceId}/dashboard_summary.json
```

## 웹 대시보드

경로: `server/web-dashboard/`

웹 대시보드는 분석 Worker가 생성한 `output/{deviceId}/dashboard_summary.json`을 읽어서 브라우저에 표시한다. 현재는 FastAPI가 아니라 Python 표준 라이브러리의 `http.server` 기반 프로토타입이다.

### 서버 파일

| 파일 | 역할 |
| --- | --- |
| `server/web-dashboard/dashboard_server.py` | 웹 대시보드 로컬 서버다. HTML/CSS/JS 정적 파일을 제공하고, `/api/dashboard?deviceId=...` 요청을 처리한다. `output/` 폴더에서 장치 목록을 읽어 드롭다운 목록으로 내려준다. |
| `server/web-dashboard/README.md` | 대시보드 실행 방법과 표시 방식을 설명한다. |

### 화면 파일

경로: `server/web-dashboard/static/`

| 파일 | 역할 |
| --- | --- |
| `static/index.html` | 대시보드 화면의 HTML 구조다. 상단 사람/기기 선택 드롭다운, 분석 데이터 표, LED 상태 영역을 포함한다. |
| `static/dashboard.css` | 대시보드 화면 스타일을 담당한다. 표, 기준치 배지, LED 색상, 반응형 레이아웃을 정의한다. |
| `static/dashboard.js` | 브라우저 동작을 담당한다. 2초마다 `/api/dashboard?deviceId=...`를 호출하고, 선택한 장치의 표와 LED 상태를 갱신한다. 드롭다운 선택값은 브라우저 `localStorage`에 저장한다. |

## 대시보드 API 프로토타입

현재 임시 API는 `dashboard_server.py` 안에 구현되어 있다.

```text
GET /api/dashboard?deviceId=home-001
GET /api/dashboard?deviceId=home-002
```

응답에는 다음 정보가 포함된다.

| 필드 | 역할 |
| --- | --- |
| `devices` | 선택 가능한 장치 ID 목록이다. 현재는 `output/{deviceId}` 폴더를 기준으로 생성한다. |
| `selectedDeviceId` | 현재 선택된 장치 ID다. |
| `deviceId` | 분석 결과 파일에 들어 있는 장치 ID다. |
| `analysisDate` | 분석 기준 날짜다. |
| `updatedAt` | `dashboard_summary.json` 파일의 최신 수정 시각이다. |
| `rows` | 표에 표시할 데이터 행 목록이다. |
| `leds` | LED 영역에 표시할 데이터 목록이다. 현재는 `rows`와 같은 데이터를 사용한다. |
| `riskReasons` | 위험 점수 산정 사유다. |

## 현재 화면에 표시되는 데이터

대시보드는 현재 다음 데이터를 표시한다.

| 데이터 이름 | 원본 필드 | 기준 방향 |
| --- | --- | --- |
| 위험 점수 | `risk.riskScore` | 낮을수록 좋음 |
| 오늘 총 활동 시간 | `today.totalActiveSeconds` | 높을수록 좋음 |
| 최장 무활동 시간 | `today.longestInactivitySeconds` | 낮을수록 좋음 |
| 오늘 움직임 이벤트 | `today.movementEvents` | 높을수록 좋음 |
| 평균 움직임 점수 | `today.avgMovementScore` | 높을수록 좋음 |
| 평균 신호 품질 | `today.avgSignalQuality` | 높을수록 좋음 |
| 주간 평균 위험 점수 | `latestWeeklySummary.avg_risk_score` | 낮을수록 좋음 |
| 월별 평균 위험 점수 | `latestMonthlySummary.avg_risk_score` | 낮을수록 좋음 |

각 데이터는 `정상`, `주의`, `경고`, `위험` 4단계로 분류되고, 표와 LED에 동시에 표시된다.

## 미구현 또는 자리표시자 폴더

다음 폴더는 전체 프로젝트 구조와 역할 분담을 위해 만들어 둔 자리표시자다. 아직 실제 코드는 들어 있지 않다.

| 폴더 | 예정 역할 |
| --- | --- |
| `esp32-c5/` | 팀원이 담당하는 ESP32-C5 펌웨어와 CSI 수집 관련 자료를 둘 영역이다. |
| `pc-analyzer/python-analyzer/` | PC Python 분석 프로그램을 구현할 영역이다. ESP32-C5 데이터 입력, Parser, 분석, 서버 전송, WPF 출력 기능이 들어갈 예정이다. |
| `pc-analyzer/wpf-ui/` | 팀원이 담당하는 C# WPF UI 프로젝트 영역이다. |
| `server/api-server/` | 추후 FastAPI 기반 서버 API를 구현할 영역이다. |
| `server/database/` | PostgreSQL 스키마, 마이그레이션 SQL, 초기 데이터 파일을 둘 영역이다. |

## 앞으로 바뀔 가능성이 큰 부분

현재 프로토타입은 JSON 파일 기반이다. 실제 서버 구현 단계에서는 다음 부분이 바뀔 수 있다.

| 현재 | 향후 |
| --- | --- |
| `sample-data/{deviceId}/activity_windows_30d.json` | PostgreSQL `activity_windows` 테이블 |
| `output/{deviceId}/dashboard_summary.json` | FastAPI 대시보드 조회 API 응답 |
| 파일 시스템 기반 장치 목록 | PostgreSQL `devices` 테이블 |
| `dashboard_server.py` 내부 임시 API | `server/api-server/`의 FastAPI API |
| 장치 ID만 표시 | 사람 이름과 장치 ID를 매핑해 표시 |


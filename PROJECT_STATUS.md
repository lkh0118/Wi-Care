# PROJECT_STATUS.md

## 2026-05-01

### 작업 내용

- Wi-Care 프로젝트 기본 폴더 구조 생성
- README 초안 작성
- 프로젝트 역할 분담 문서화
- ESP32-C5와 WPF가 팀원 담당 영역이며 변경 가능성이 있음을 명시
- Python 분석 프로그램과 외부 서버 PC 구현 중심의 개발 계획 정리
- Mock 데이터 기반 개발 시작 전략 정리
- 인터페이스 및 Mock 데이터 설계 문서 초안 작성

### 수정한 파일

- 없음

### 추가한 파일

- `README.md`
- `PROJECT_STATUS.md`
- `docs/INTERFACES.md`
- `docs/MOCK_DATA_PLAN.md`
- `docs/DEVELOPMENT_TODO.md`
- `esp32-c5/.gitkeep`
- `pc-analyzer/python-analyzer/input/.gitkeep`
- `pc-analyzer/python-analyzer/parsers/.gitkeep`
- `pc-analyzer/python-analyzer/analysis/.gitkeep`
- `pc-analyzer/python-analyzer/output/.gitkeep`
- `pc-analyzer/python-analyzer/transports/.gitkeep`
- `pc-analyzer/wpf-ui/.gitkeep`
- `server/api-server/.gitkeep`
- `server/analysis-worker/.gitkeep`
- `server/web-dashboard/.gitkeep`
- `server/database/.gitkeep`

### 삭제한 파일

- 없음

### 현재 상태

- 실제 코드는 아직 작성하지 않았다.
- 전체 구조와 역할 분담을 먼저 고정했다.
- Python 분석 프로그램은 Mock 입력기부터 개발할 수 있도록 폴더를 분리했다.
- 외부 서버는 FastAPI, PostgreSQL, 분석 Worker, 웹 대시보드 영역으로 분리했다.

### 남은 작업

- Python Mock 입력기 구현
- Parser 인터페이스 구현
- 내부 표준 데이터 모델 정의
- 분석 결과 DTO 정의
- WPF 연동용 출력 방식 확정
- FastAPI 서버 기본 코드 작성
- PostgreSQL 스키마 초안 작성
- 서버 분석 Worker 설계 및 구현
- 웹 대시보드 기술 스택 결정

### 문제점

- ESP32-C5 실제 데이터 포맷이 아직 확정되지 않았다.
- ESP32-C5의 초기 통신 방식은 USB Serial을 우선 고려하지만, UDP/TCP로 변경될 수 있다.
- WPF 연동 방식은 로컬 HTTP API, WebSocket, JSON 파일 출력 중 아직 확정되지 않았다.

### 다음 작업

- `pc-analyzer/python-analyzer/`에 Mock 입력기와 Parser 인터페이스 초안 작성
- 분석 결과 JSON 모델 정의
- `server/database/`에 PostgreSQL 스키마 초안 작성
- `server/api-server/`에 FastAPI 기본 프로젝트 구성

### 역할 및 인터페이스 변경 사항

- ESP32-C5 담당: 팀원
- WPF UI 담당: 팀원
- Python 분석 프로그램 담당: 나
- 외부 서버 PC 전체 구현 담당: 나
- ESP32-C5 데이터 포맷 변경 여부: 아직 확정 전
- WPF 연동 방식 변경 여부: 아직 확정 전
- 서버 API 변경 여부: 아직 구현 전

## 2026-05-01 추가 작업

### 작업 내용

- 서버 PC가 받아야 하는 분석 가중치 데이터 구조 문서화
- 활동 구간 데이터, 이벤트 데이터, 장치 상태 데이터로 수신 데이터를 분리
- 서버 분석 Worker와 웹 대시보드 구현에 필요한 최소 필드 정리
- 서버 API 후보와 PostgreSQL 저장 테이블 초안 정리

### 수정한 파일

- `README.md`
- `PROJECT_STATUS.md`

### 추가한 파일

- `docs/SERVER_INPUT_DATA.md`

### 삭제한 파일

- 없음

### 현재 상태

- 서버 프로토타입 개발에 필요한 입력 데이터 구조가 문서화되었다.
- 첫 구현 우선순위는 `POST /api/activity/windows`로 정리했다.
- 서버는 Raw CSI가 아니라 PC Python 분석 프로그램의 요약 분석 데이터를 받는 구조로 유지한다.

### 남은 작업

- `POST /api/activity/windows` 요청 DTO 구현
- `activity_windows` PostgreSQL 스키마 작성
- Mock 데이터 기반 서버 저장 흐름 구현
- 대시보드 요약 API 구현

### 문제점

- 실제 Python 분석 결과 산출 방식은 아직 구현 전이다.
- ESP32-C5 실제 데이터 포맷은 아직 확정되지 않았다.

### 다음 작업

- 서버 API 프로토타입 구현 전 `docs/SERVER_INPUT_DATA.md`를 기준으로 DTO와 DB 스키마를 작성한다.

### 역할 및 인터페이스 변경 사항

- ESP32-C5 담당: 팀원
- WPF UI 담당: 팀원
- Python 분석 프로그램 담당: 나
- 외부 서버 PC 전체 구현 담당: 나
- ESP32-C5 데이터 포맷 변경 여부: 아직 확정 전
- WPF 연동 방식 변경 여부: 아직 확정 전
- 서버 API 변경 여부: 서버 수신 데이터 후보를 문서로 정리했으며 구현은 아직 전

## 2026-05-01 서버 분석 Worker 프로토타입

### 작업 내용

- 30일치 Mock `activity_windows` 데이터 생성 로직 구현
- Mock 데이터를 기반으로 일일 요약 계산 로직 구현
- 주간 요약 계산 로직 구현
- 월별 요약 계산 로직 구현
- 위험 점수 계산 로직 구현
- 대시보드용 요약 JSON 생성 로직 구현
- 서버 분석 Worker 실행 방법 문서화

### 수정한 파일

- `README.md`
- `PROJECT_STATUS.md`
- `docs/DEVELOPMENT_TODO.md`

### 추가한 파일

- `.gitignore`
- `server/analysis-worker/README.md`
- `server/analysis-worker/run_analysis.py`
- `server/analysis-worker/activity_analysis/__init__.py`
- `server/analysis-worker/activity_analysis/models.py`
- `server/analysis-worker/activity_analysis/mock_data_generator.py`
- `server/analysis-worker/activity_analysis/analyzer.py`
- `server/analysis-worker/sample-data/activity_windows_30d.json`
- `server/analysis-worker/output/daily_summaries.json`
- `server/analysis-worker/output/weekly_summaries.json`
- `server/analysis-worker/output/monthly_summary.json`
- `server/analysis-worker/output/risk_scores.json`
- `server/analysis-worker/output/dashboard_summary.json`

### 삭제한 파일

- 없음

### 현재 상태

- 서버 분석 Worker는 JSON 파일 기반으로 실행 가능하다.
- `python run_analysis.py --regenerate` 명령으로 30일 Mock 데이터를 생성하고 분석 결과 JSON을 만들 수 있다.
- 최근 샘플 기준 일일 요약 30개, 주간 요약 5개, 월별 요약 2개가 생성되었다.
- 최근 날짜 위험 점수는 `73 / 경고`로 계산되었다.

### 남은 작업

- PostgreSQL의 `activity_windows` 테이블에서 데이터를 읽는 입력부 구현
- FastAPI 서버와 분석 Worker 결과 연결
- 웹 대시보드에서 `dashboard_summary.json` 또는 API 응답 표시
- 실제 운영 기준에 맞게 위험 점수 가중치 조정
- baseline profile 테이블 설계 및 저장 구현

### 문제점

- 현재 Mock 데이터는 1시간 구간 단위이며, 실제 서버 수신 데이터의 1분 단위와 다를 수 있다.
- 위험 점수 기준은 초기 규칙 기반이므로 실제 데이터 확보 후 보정이 필요하다.
- PostgreSQL 연동은 아직 구현하지 않았다.

### 다음 작업

- FastAPI API 서버 프로토타입을 만들고 `POST /api/activity/windows`로 Mock 데이터를 저장한다.
- 저장된 데이터를 분석 Worker가 읽을 수 있도록 DB 조회 계층을 추가한다.

### 역할 및 인터페이스 변경 사항

- ESP32-C5 담당: 팀원
- WPF UI 담당: 팀원
- Python 분석 프로그램 담당: 나
- 외부 서버 PC 전체 구현 담당: 나
- ESP32-C5 데이터 포맷 변경 여부: 아직 확정 전
- WPF 연동 방식 변경 여부: 아직 확정 전
- 서버 API 변경 여부: 없음. 문서화된 `activity_windows` 형식을 기준으로 Mock 데이터를 생성함

## 2026-05-01 웹 대시보드 프로토타입

### 작업 내용

- 서버 분석 Worker의 `dashboard_summary.json`을 읽는 웹 대시보드 서버 구현
- 데이터 이름, 최신 수정 시각, 데이터 값, 현재 단계를 표로 표시
- 데이터별 정상/주의/경고/위험 기준치 표시
- 데이터별 4단계 LED 상태 표시 구현
- 브라우저에서 2초마다 `/api/dashboard`를 호출하는 자동 갱신 구현
- 대시보드 실행 방법 문서화

### 수정한 파일

- `.gitignore`
- `README.md`
- `PROJECT_STATUS.md`
- `docs/DEVELOPMENT_TODO.md`

### 추가한 파일

- `server/web-dashboard/README.md`
- `server/web-dashboard/dashboard_server.py`
- `server/web-dashboard/static/index.html`
- `server/web-dashboard/static/dashboard.css`
- `server/web-dashboard/static/dashboard.js`

### 삭제한 파일

- 없음

### 현재 상태

- `python dashboard_server.py` 실행 시 `http://127.0.0.1:8080`에서 대시보드를 볼 수 있다.
- 대시보드는 분석 Worker가 생성한 `dashboard_summary.json`의 수정 시각과 값을 기준으로 표시된다.
- 화면은 2초마다 최신 분석 결과를 다시 요청한다.
- 현재 구현은 Python 표준 라이브러리 기반 프로토타입이며 FastAPI/PostgreSQL 통합 전 단계다.

### 남은 작업

- FastAPI 서버와 대시보드 API 통합
- PostgreSQL 저장 데이터 기반 실시간 조회 연결
- 최근 7일/30일 그래프 추가
- 이벤트 로그 표시 추가
- 기준치와 위험 점수 가중치를 실제 데이터 기준으로 보정

### 문제점

- 현재 실시간성은 `dashboard_summary.json` 파일 갱신을 2초마다 반영하는 방식이다.
- 아직 실제 서버 API와 DB에서 직접 읽는 구조는 아니다.

### 다음 작업

- `POST /api/activity/windows` 저장 API를 구현하고, 저장된 데이터를 대시보드 API에서 직접 조회하도록 변경한다.

### 역할 및 인터페이스 변경 사항

- ESP32-C5 담당: 팀원
- WPF UI 담당: 팀원
- Python 분석 프로그램 담당: 나
- 외부 서버 PC 전체 구현 담당: 나
- ESP32-C5 데이터 포맷 변경 여부: 아직 확정 전
- WPF 연동 방식 변경 여부: 아직 확정 전
- 서버 API 변경 여부: 대시보드 조회용 임시 API `/api/dashboard` 추가

## 2026-05-01 다중 사람/기기 대시보드 전환

### 작업 내용

- Mock 분석 데이터를 사람/기기별 폴더에 저장하도록 표준화
- `home-001`, `home-002` 각각 30일 Mock 데이터 생성
- 분석 결과 파일을 `output/{deviceId}/` 아래에 분리 저장하도록 변경
- 웹 대시보드에 사람/기기 선택 드롭다운 추가
- 드롭다운 선택값에 따라 `/api/dashboard?deviceId=...`로 다른 장치 데이터를 표시하도록 변경

### 수정한 파일

- `README.md`
- `PROJECT_STATUS.md`
- `server/analysis-worker/README.md`
- `server/analysis-worker/run_analysis.py`
- `server/web-dashboard/README.md`
- `server/web-dashboard/dashboard_server.py`
- `server/web-dashboard/static/index.html`
- `server/web-dashboard/static/dashboard.css`
- `server/web-dashboard/static/dashboard.js`

### 추가한 파일

- `server/analysis-worker/sample-data/home-001/activity_windows_30d.json`
- `server/analysis-worker/sample-data/home-002/activity_windows_30d.json`
- `server/analysis-worker/output/home-001/daily_summaries.json`
- `server/analysis-worker/output/home-001/weekly_summaries.json`
- `server/analysis-worker/output/home-001/monthly_summary.json`
- `server/analysis-worker/output/home-001/risk_scores.json`
- `server/analysis-worker/output/home-001/dashboard_summary.json`
- `server/analysis-worker/output/home-002/daily_summaries.json`
- `server/analysis-worker/output/home-002/weekly_summaries.json`
- `server/analysis-worker/output/home-002/monthly_summary.json`
- `server/analysis-worker/output/home-002/risk_scores.json`
- `server/analysis-worker/output/home-002/dashboard_summary.json`

### 삭제한 파일

- `server/analysis-worker/sample-data/activity_windows_30d.json`
- `server/analysis-worker/output/daily_summaries.json`
- `server/analysis-worker/output/weekly_summaries.json`
- `server/analysis-worker/output/monthly_summary.json`
- `server/analysis-worker/output/risk_scores.json`
- `server/analysis-worker/output/dashboard_summary.json`

### 현재 상태

- 기본 분석 실행 시 `home-001`, `home-002` 데이터가 모두 생성된다.
- 파일 저장 표준은 `sample-data/{deviceId}/...`, `output/{deviceId}/...` 방식이다.
- 대시보드는 `output/` 아래의 장치 폴더를 읽어 드롭다운 목록을 만든다.
- `home-001` 최근 위험 점수는 `73 / 경고`, `home-002` 최근 위험 점수는 `69 / 경고`로 계산되었다.

### 남은 작업

- 실제 DB 도입 시 `deviceId` 기준 조회 API로 동일 동작 연결
- 사람 이름과 장치 ID를 매핑하는 `devices` 테이블 설계
- 대시보드 드롭다운에 장치 ID 대신 표시 이름을 보여주는 기능 추가

### 문제점

- 현재 사람/기기 목록은 파일 시스템의 `output/{deviceId}` 폴더 기준으로 생성된다.
- 아직 사용자 친화적인 표시 이름은 없고 `home-001`, `home-002` 같은 장치 ID만 표시된다.

### 다음 작업

- FastAPI와 PostgreSQL 도입 시 `GET /api/devices`와 `GET /api/dashboard?deviceId=...` 형태로 정식 API를 분리한다.

### 역할 및 인터페이스 변경 사항

- ESP32-C5 담당: 팀원
- WPF UI 담당: 팀원
- Python 분석 프로그램 담당: 나
- 외부 서버 PC 전체 구현 담당: 나
- ESP32-C5 데이터 포맷 변경 여부: 없음
- WPF 연동 방식 변경 여부: 없음
- 서버 API 변경 여부: 임시 대시보드 API에 `deviceId` 쿼리 파라미터와 `devices` 응답 필드 추가

## 2026-05-01 파일 역할 문서화

### 작업 내용

- 현재 프로젝트에 존재하는 파일과 폴더의 역할을 문서화
- 서버 분석 Worker, Mock 데이터, 분석 결과, 웹 대시보드 파일을 구분해 정리
- 현재 JSON 파일 기반 구조와 향후 FastAPI/PostgreSQL 구조로 바뀔 부분을 정리

### 수정한 파일

- `README.md`
- `PROJECT_STATUS.md`

### 추가한 파일

- `docs/FILE_ROLE_GUIDE.md`

### 삭제한 파일

- 없음

### 현재 상태

- 현재까지 구현된 파일이 어떤 역할을 하는지 `docs/FILE_ROLE_GUIDE.md`에서 확인할 수 있다.

### 남은 작업

- FastAPI 서버와 PostgreSQL 구현이 추가되면 파일 역할 문서를 함께 갱신한다.

### 문제점

- 없음

### 다음 작업

- 서버 API 구현 단계로 넘어갈 경우 `server/api-server/`와 `server/database/`의 파일 역할을 추가한다.

### 역할 및 인터페이스 변경 사항

- 역할 변경 없음
- ESP32-C5 데이터 포맷 변경 없음
- WPF 연동 방식 변경 없음
- 서버 API 변경 없음

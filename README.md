# Wi-Care

Wi-Care는 ESP32-C5로 실내 Wi-Fi 전파 데이터(CSI)를 수집하고, 분석 PC의 Python 프로그램에서 움직임 분석 가중치를 계산한 뒤, C# WPF UI와 외부 서버 웹 대시보드에 상태를 제공하는 비접촉 실내 활동 감지 프로토타입이다.

목표는 독거노인 또는 돌봄이 필요한 사람의 실내 활동 상태를 비접촉 방식으로 감지하고, 장시간 무활동, 활동량 저하, 이상 징후를 조기에 파악할 수 있는 기본 시스템을 구축하는 것이다.

## 프로젝트 구조

```text
Wi-Care/
├─ esp32-c5/
├─ pc-analyzer/
│  ├─ python-analyzer/
│  │  ├─ input/
│  │  ├─ parsers/
│  │  ├─ analysis/
│  │  ├─ output/
│  │  └─ transports/
│  └─ wpf-ui/
├─ server/
│  ├─ api-server/
│  ├─ analysis-worker/
│  ├─ web-dashboard/
│  └─ database/
├─ docs/
├─ README.md
└─ PROJECT_STATUS.md
```

## 폴더 역할

| 경로 | 역할 | 주 담당 |
| --- | --- | --- |
| `esp32-c5/` | ESP32-C5 펌웨어, CSI 수집, PC 전송 관련 자료를 보관한다. 실제 구현은 팀원 담당이며 포맷과 통신 방식은 변경될 수 있다. | 팀원 |
| `pc-analyzer/python-analyzer/` | ESP32-C5 또는 Mock 입력을 받아 움직임 분석 가중치를 계산하고 서버/WPF용 결과를 생성한다. | 나 |
| `pc-analyzer/python-analyzer/input/` | Serial, UDP, TCP, Mock 입력기를 교체 가능한 구조로 둔다. | 나 |
| `pc-analyzer/python-analyzer/parsers/` | ESP32-C5 데이터 포맷 변경에 대응하는 Parser 인터페이스와 구현체를 둔다. | 나 |
| `pc-analyzer/python-analyzer/analysis/` | `movementScore`, `presenceProb`, `inactivitySeconds`, `activityState`, `confidence` 계산 로직을 둔다. | 나 |
| `pc-analyzer/python-analyzer/output/` | WPF UI가 사용할 로컬 HTTP API, WebSocket, JSON 파일 출력 구현을 둔다. | 나 |
| `pc-analyzer/python-analyzer/transports/` | 외부 서버 REST API 전송 로직을 둔다. | 나 |
| `pc-analyzer/wpf-ui/` | C# WPF UI 프로젝트 영역이다. 구현은 팀원 담당이며 Python 출력 포맷에 맞춰 연동한다. | 팀원 |
| `server/api-server/` | FastAPI 기반 JSON 수신 API와 조회 API를 둔다. | 나 |
| `server/analysis-worker/` | 일/주/월 단위 활동 패턴 분석과 위험 점수 계산 작업을 둔다. | 나 |
| `server/web-dashboard/` | 웹 대시보드 화면을 둔다. | 나 |
| `server/database/` | PostgreSQL 스키마, 마이그레이션 SQL, 초기 데이터 관련 파일을 둔다. | 나 |
| `docs/` | 인터페이스, 데이터 포맷, 개발 계획, 팀원 연동 문서를 둔다. | 공동 참고 |

## 역할 분담

### 팀원 담당 영역

- ESP32-C5 보드 제어 및 CSI 수집 펌웨어 구현
- ESP32-C5에서 PC로 데이터를 전송하는 방식 구현
- C# WPF UI 구현
- WPF 화면에서 현재 상태, 활동 그래프, 서버 연결 상태, 알림 로그 표시

ESP32-C5의 데이터 포맷과 통신 방식은 프로젝트 진행 중 언제든지 변경될 수 있다. WPF UI의 화면 구성과 연동 방식도 팀원 구현 상황에 따라 변경될 수 있다.

### 내 담당 영역

- Python 기반 분석 프로그램 전체 구조 설계 및 구현
- ESP32-C5 데이터 입력부, Parser, 분석부, 전송부 모듈화
- Mock 데이터 기반 개발 환경 구성
- WPF가 사용할 분석 결과 출력 포맷 제공
- 외부 서버 PC 전체 구현
- FastAPI 서버, PostgreSQL 저장 구조, 서버 분석 Worker, 웹 대시보드 구현
- 일/주/월 단위 활동 패턴 분석과 위험 점수 계산

## 분석 결과 기본 포맷

Python 분석 프로그램은 최소한 다음 값을 생성한다.

```json
{
  "deviceId": "home-001",
  "timestamp": "2026-05-01T10:00:00+09:00",
  "movementScore": 42.7,
  "presenceProb": 0.88,
  "inactivitySeconds": 180,
  "activityState": "moving",
  "confidence": 0.84
}
```

`activityState`의 초기 후보 값은 다음과 같다.

- `empty`: 사람이 없다고 추정되는 상태
- `present`: 사람이 있으나 움직임이 약한 상태
- `moving`: 움직임이 감지되는 상태
- `warning`: 장시간 무활동 또는 이상 징후 상태

## Mock 데이터 기반 시작 전략

ESP32-C5 실제 데이터가 아직 없어도 개발을 시작할 수 있도록 Python 분석 프로그램은 Mock 입력기를 먼저 사용한다.

초기 Mock 입력기는 다음 상황을 흉내 낸다.

- 빈 공간 상태
- 사람이 있지만 거의 움직이지 않는 상태
- 일반적인 움직임 상태
- 장시간 무활동 상태
- 신호 품질 저하 상태

Mock 데이터는 실제 ESP32-C5 포맷이 확정되기 전까지 분석 파이프라인, 서버 전송, WPF 출력 포맷을 먼저 검증하는 용도로 사용한다.

## 서버 분석 방향

서버는 Raw CSI를 직접 분석하지 않는다. 서버는 분석 PC의 Python 프로그램이 전송한 요약 데이터와 분석 가중치를 저장하고, 일/주/월 단위 패턴 분석을 수행한다.

주요 분석 항목은 다음과 같다.

- 하루 총 활동 시간
- 하루 총 움직임 이벤트 수
- 최장 무활동 시간
- 오전/오후/저녁/야간 활동 점수
- 최근 7일 활동량 변화
- 최근 30일 활동 패턴 변화
- 평소 대비 활동량 감소 여부
- 장시간 무활동 발생 횟수
- 위험 점수

위험도 계산의 초기 기준은 다음 수식을 사용한다.

```text
RiskScore
= 0.40 * LongInactivityScore
+ 0.25 * DailyActivityDropScore
+ 0.20 * TimeSlotDeviationScore
+ 0.15 * NightPatternAbnormalityScore
```

위험도 단계는 `정상`, `주의`, `경고`, `고위험`으로 구분한다.

## 서버 분석 Worker 프로토타입

현재 `server/analysis-worker/`에는 30일치 Mock 활동 구간 데이터를 생성하고, 일일/주간/월별 요약과 위험 점수를 계산하는 Python 프로토타입이 있다.

실행 방법은 다음과 같다.

```powershell
cd server/analysis-worker
python run_analysis.py --regenerate
```

생성되는 주요 파일은 다음과 같다.

- `sample-data/{deviceId}/activity_windows_30d.json`
- `output/{deviceId}/daily_summaries.json`
- `output/{deviceId}/weekly_summaries.json`
- `output/{deviceId}/monthly_summary.json`
- `output/{deviceId}/risk_scores.json`
- `output/{deviceId}/dashboard_summary.json`

## 웹 대시보드 프로토타입

현재 `server/web-dashboard/`에는 분석 Worker 결과를 표와 LED 상태 표시로 보여주는 웹 대시보드 프로토타입이 있다.

실행 방법은 다음과 같다.

```powershell
cd server/web-dashboard
python dashboard_server.py
```

브라우저 접속 주소는 다음과 같다.

```text
http://127.0.0.1:8080
```

현재 화면 구성은 다음과 같다.

- 사람/기기 선택 드롭다운
- 데이터 이름, 최신 수정 시각, 데이터 값, 현재 단계 표기
- 데이터별 정상/주의/경고/위험 기준치 표기
- 데이터별 4단계 LED 상태 표시
- 2초 주기 자동 갱신

## 개발 순서 TODO

1. 프로젝트 기본 폴더 구조와 문서 정리
2. Mock 데이터 입력기 설계
3. Parser 인터페이스 설계
4. Mock Parser 및 내부 표준 데이터 모델 정의
5. Python 분석 파이프라인 초안 작성
6. 분석 결과 JSON 포맷 확정
7. WPF 연동용 출력 방식 결정
8. 서버 API 요청/응답 DTO 설계
9. PostgreSQL 기본 스키마 작성
10. FastAPI 수신 API 구현
11. Python 분석 프로그램에서 서버 전송 구현
12. 일 단위 요약 분석 Worker 구현
13. 주/월 단위 패턴 분석 구현
14. 위험 점수 계산 구현
15. 웹 대시보드 기본 화면 구현
16. WPF 담당자와 로컬 연동 방식 검증
17. ESP32-C5 실제 데이터 포맷 반영

## 개발 규칙

- 변경 사항이 생길 때마다 `PROJECT_STATUS.md`를 갱신한다.
- Python 코드는 입력부, 파싱부, 분석부, 출력부, 서버 전송부를 분리한다.
- ESP32-C5 데이터 포맷 변경 가능성을 고려해 Parser 인터페이스를 유지한다.
- WPF는 분석 로직을 포함하지 않고 Python 분석 결과만 사용한다.
- 서버는 Raw CSI가 아닌 분석 요약 데이터를 저장하고 장기 패턴을 분석한다.
- 설정값은 `.env` 또는 별도 설정 파일로 분리한다.
- 데이터베이스 스키마 변경 시 `server/database/`에 SQL 또는 마이그레이션 파일을 남긴다.

## 관련 문서

- `docs/INTERFACES.md`: 시스템 간 인터페이스 초안
- `docs/MOCK_DATA_PLAN.md`: Mock 데이터 기반 개발 계획
- `docs/SERVER_INPUT_DATA.md`: 서버가 수신해야 하는 분석 가중치 데이터 설계
- `docs/DEVELOPMENT_TODO.md`: 단계별 개발 TODO
- `docs/FILE_ROLE_GUIDE.md`: 현재 파일과 폴더별 역할 정리

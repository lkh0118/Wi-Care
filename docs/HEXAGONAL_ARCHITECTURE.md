# 헥사고날 아키텍처 + MVVM

Wi-Care는 비즈니스 핵심 분석 모델을 외부 기술로부터 분리하기 위해 작은 범위의 헥사고날 아키텍처를 사용한다. 대시보드 화면 표현은 이해하기 쉽게 MVVM 방식으로 분리한다.

## 두 패턴을 함께 사용하는 이유

- 헥사고날 아키텍처는 분석 코어가 JSON 파일, 향후 PostgreSQL 저장소, HTTP API, Serial, UDP 같은 외부 기술에 직접 의존하지 않게 한다.
- MVVM은 대시보드 표시 규칙을 HTTP 서버 코드와 HTML 렌더링 코드에서 분리한다.
- 프로젝트 전체를 과하게 복잡하게 만들지 않으면서도, 핵심 비즈니스 모델을 테스트하기 쉽고 외부 구현을 교체하기 쉬운 구조로 유지한다.

## 분석 Worker 구조

```text
run_analysis.py
  -> AnalysisWorkerService
      -> ActivityWindowInputPort
          -> MockActivityWindowFileAdapter
              -> ActivityWindow
      -> analyzer.py
      -> AnalysisResultOutputPort
          -> JsonAnalysisResultFileAdapter
```

| 역할 | 파일 | 책임 |
| --- | --- | --- |
| Model | `activity_analysis/models.py` | `ActivityWindow`, `DailySummary`, `RiskScore` 같은 비즈니스 데이터 모델을 정의한다. |
| Core Logic | `activity_analysis/analyzer.py` | 일일, 주간, 월별 요약과 위험 점수 계산을 담당한다. |
| Ports | `activity_analysis/ports.py` | 애플리케이션 코어가 의존하는 입력/출력 인터페이스를 정의한다. |
| Application Service | `activity_analysis/service.py` | JSON, HTTP, DB 세부 구현을 모른 채 하나의 분석 유스케이스를 조율한다. |
| Adapters | `activity_analysis/adapters.py` | 외부 JSON payload를 모델로 변환하고 분석 결과를 JSON 파일로 저장한다. |
| Composition Root | `run_analysis.py` | 실제 어댑터를 서비스에 연결하고 CLI 옵션을 처리한다. |

중요한 경계는 `AnalysisWorkerService`가 입력 포트로부터 원시 JSON dictionary가 아니라 `ActivityWindow` 모델을 받는다는 점이다. 따라서 분석 서비스와 분석 로직은 외부 데이터 형식에 직접 묶이지 않는다.

## 대시보드 MVVM 구조

```text
dashboard_server.py
  -> dashboard_summary.json
  -> dashboard_view_model.py
  -> /api/dashboard JSON
  -> static/dashboard.js
  -> static/index.html
```

| MVVM 구성 | 파일 | 책임 |
| --- | --- | --- |
| Model | `dashboard_summary.json`, 분석 결과 데이터 | 분석 Worker가 생성한 원본 결과 데이터이다. |
| ViewModel | `server/web-dashboard/dashboard_view_model.py` | 분석 데이터를 표 row, LED 상태, 라벨, 기준값, 표시 문자열로 변환한다. |
| View | `server/web-dashboard/static/index.html`, `dashboard.js`, `dashboard.css` | 이미 준비된 ViewModel 데이터를 화면에 렌더링한다. |

`dashboard_server.py`는 HTTP 라우팅, 정적 파일 제공, 장치 선택, JSON 응답만 담당한다. 대시보드 표시 규칙은 `dashboard_view_model.py`가 담당한다.

## 확장 지점

- `MockActivityWindowFileAdapter`를 Serial, UDP, HTTP, PostgreSQL 입력 어댑터로 교체할 수 있다.
- `JsonAnalysisResultFileAdapter`를 PostgreSQL 저장 어댑터나 FastAPI 전송 어댑터로 교체할 수 있다.
- 새 대시보드 지표는 분석 규칙을 바꾸지 않고 `dashboard_view_model.py`에 추가할 수 있다.
- `analyzer.py`는 파일 경로, HTTP 요청 데이터, 데이터베이스 코드, UI 라벨을 몰라야 한다.

## 현재 적용 범위

- 현재 헥사고날 아키텍처 적용 범위는 `server/analysis-worker/` 중심이다.
- 현재 MVVM 적용 범위는 `server/web-dashboard/` 중심이다.
- 향후 FastAPI와 PostgreSQL이 추가되면 기존 코어를 수정하기보다 새 어댑터를 추가하는 방식으로 확장한다.

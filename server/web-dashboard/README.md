# Wi-Care 웹 대시보드 프로토타입

이 폴더는 서버 분석 Worker가 생성한 JSON 결과를 웹페이지로 표시하는 대시보드 프로토타입이다.

현재 구현은 외부 패키지 없이 Python 표준 라이브러리만 사용한다. 이후 FastAPI 서버와 PostgreSQL이 붙으면 동일 화면을 API 기반으로 옮길 수 있다.

## 실행 방법

분석 결과 JSON이 없으면 먼저 서버 분석 Worker를 실행한다.

```powershell
cd server/analysis-worker
python run_analysis.py --regenerate
```

대시보드를 실행한다.

```powershell
cd server/web-dashboard
python dashboard_server.py
```

브라우저에서 다음 주소로 접속한다.

```text
http://127.0.0.1:8080
```

## 표시 방식

- 사람/기기 선택 드롭다운으로 표시할 장치를 바꾼다.
- 상단 표: 데이터 이름, 최신 수정 시각, 데이터 값, 기준치
- 우측 기준치: 정상, 주의, 경고, 위험 구간
- 하단 LED 패널: 각 데이터의 현재 상태를 4단계 색상으로 표시
- 실시간 갱신: 브라우저가 2초마다 `/api/dashboard`를 호출해 최신 JSON을 반영

## 현재 데이터 원본

```text
../analysis-worker/output/{deviceId}/dashboard_summary.json
```

대시보드는 `../analysis-worker/output/` 아래의 장치 폴더를 읽어 드롭다운 목록을 만든다.

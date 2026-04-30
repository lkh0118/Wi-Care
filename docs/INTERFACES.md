# 인터페이스 설계 초안

이 문서는 Wi-Care의 주요 연동 지점을 정리한다. ESP32-C5와 WPF 영역은 팀원 담당이며, 실제 구현 상황에 따라 인터페이스가 변경될 수 있다.

## 1. ESP32-C5 → PC Python

초기 통신 방식은 USB Serial을 우선 고려한다. 이후 UDP 또는 TCP 입력으로 확장할 수 있도록 Python 입력부를 분리한다.

Python 쪽 구조는 다음 계층으로 나눈다.

```text
InputSource → Parser → StandardSample → Analyzer → AnalysisResult
```

- `InputSource`: Serial, UDP, TCP, Mock 입력을 담당한다.
- `Parser`: ESP32-C5 원본 메시지를 내부 표준 데이터로 변환한다.
- `StandardSample`: 분석 로직이 사용하는 내부 표준 샘플이다.
- `Analyzer`: 움직임 점수, 존재 확률, 무활동 시간, 신뢰도를 계산한다.
- `AnalysisResult`: 서버와 WPF에 전달할 결과 데이터다.

## 2. Python 분석 프로그램 → WPF UI

WPF는 분석 로직을 포함하지 않는다. WPF는 Python 분석 프로그램이 생성한 현재 상태값을 받아 화면에 표시한다.

초기 후보 방식은 다음과 같다.

| 방식 | 장점 | 단점 |
| --- | --- | --- |
| 로컬 HTTP API | 구현과 테스트가 쉽고 WPF에서 호출하기 쉽다. | 실시간성이 WebSocket보다 낮다. |
| WebSocket | 실시간 상태 표시가 자연스럽다. | 구현 복잡도가 조금 높다. |
| JSON 파일 출력 | 가장 단순하다. | 파일 잠금, 갱신 주기, 오류 처리가 필요하다. |

초기 추천은 로컬 HTTP API다.

예상 엔드포인트는 다음과 같다.

```text
GET http://127.0.0.1:8765/status/current
GET http://127.0.0.1:8765/status/recent
```

현재 상태 응답 예시는 다음과 같다.

```json
{
  "deviceId": "home-001",
  "timestamp": "2026-05-01T10:00:00+09:00",
  "movementScore": 42.7,
  "presenceProb": 0.88,
  "inactivitySeconds": 180,
  "activityState": "moving",
  "confidence": 0.84,
  "serverConnected": true
}
```

## 3. PC Python → 외부 서버

기본 통신 방식은 HTTPS REST API와 JSON Body 전송이다.

초기 API 후보는 다음과 같다.

```text
POST /api/activity/windows
POST /api/activity/events
POST /api/activity/daily
```

`/api/activity/windows` 요청 예시는 다음과 같다.

```json
{
  "deviceId": "home-001",
  "windowStart": "2026-05-01T10:00:00+09:00",
  "windowEnd": "2026-05-01T10:05:00+09:00",
  "movementScore": 42.7,
  "presenceProb": 0.88,
  "activeSeconds": 130,
  "inactiveSeconds": 170,
  "movementEvents": 8,
  "avgMovementScore": 31.4,
  "maxMovementScore": 76.2,
  "signalQuality": 0.91,
  "confidence": 0.84,
  "activityState": "moving"
}
```

## 4. 외부 서버 → 웹 대시보드

웹 대시보드는 서버 DB에 저장된 활동 요약과 위험 점수를 조회해 표시한다.

초기 화면 항목은 다음과 같다.

- 오늘 상태
- 최근 활동 시각
- 오늘 총 활동 시간
- 최장 무활동 시간
- 최근 7일 활동량 그래프
- 최근 30일 활동 패턴 그래프
- 위험 점수와 위험 단계
- 이벤트 로그


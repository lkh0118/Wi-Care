# 서버 수신 데이터 설계

이 문서는 서버 PC가 PC Python 분석 프로그램으로부터 받아야 하는 분석 가중치 데이터와 API 입력 구조를 정리한다.

서버는 Raw CSI 데이터를 직접 받거나 분석하지 않는다. 서버는 PC Python 분석 프로그램이 계산한 요약 데이터와 분석 가중치를 저장하고, 이를 기반으로 일/주/월 활동 패턴 분석과 웹 대시보드 표시를 수행한다.

## 설계 원칙

- 서버는 Raw CSI가 아니라 분석 요약 데이터를 받는다.
- ESP32-C5 데이터 포맷 변경은 PC Python의 Parser 계층에서 흡수한다.
- 서버 API는 Python 분석 결과 DTO를 기준으로 안정적으로 유지한다.
- 모든 수신 데이터에는 `deviceId`, 시간 정보, `schemaVersion`을 포함한다.
- 원본 JSON은 PostgreSQL `JSONB` 컬럼에 저장하고, 자주 조회하는 값은 일반 컬럼으로 분리한다.
- 서버 분석 Worker는 `activity_windows` 데이터를 기본 단위로 사용한다.

## 서버가 받을 데이터 종류

서버는 초기 프로토타입에서 다음 3종류 데이터를 받는 구조로 설계한다.

| 데이터 종류 | API 후보 | 목적 | 우선순위 |
| --- | --- | --- | --- |
| 활동 구간 데이터 | `POST /api/activity/windows` | 일정 시간 구간의 움직임, 존재 확률, 활동/무활동 시간을 저장한다. | 필수 |
| 이벤트 데이터 | `POST /api/activity/events` | 장시간 무활동, 활동량 저하, 신호 품질 저하 같은 주요 사건을 기록한다. | 권장 |
| 장치 상태 데이터 | `POST /api/devices/status` | 분석기, ESP32-C5 연결, 서버 업로드 상태를 기록한다. | 권장 |

프로토타입의 첫 구현은 `POST /api/activity/windows`부터 시작한다.

## 1. 활동 구간 데이터

활동 구간 데이터는 서버 분석의 가장 중요한 입력이다. Python 분석 프로그램은 5초, 10초, 30초, 1분, 5분 중 하나의 고정된 시간 창으로 데이터를 요약해 서버로 보낸다.

초기 추천 구간은 `1분`이다. 실시간성은 조금 낮지만 서버 저장량과 분석 안정성의 균형이 좋다.

### 요청 예시

```json
{
  "deviceId": "home-001",
  "windowStart": "2026-05-01T10:00:00+09:00",
  "windowEnd": "2026-05-01T10:01:00+09:00",
  "movementScore": 42.7,
  "presenceProb": 0.88,
  "activityState": "moving",
  "confidence": 0.84,
  "activeSeconds": 35,
  "inactiveSeconds": 25,
  "movementEvents": 4,
  "avgMovementScore": 31.4,
  "maxMovementScore": 76.2,
  "minMovementScore": 3.1,
  "signalQuality": 0.91,
  "sampleCount": 60,
  "source": "python-analyzer",
  "schemaVersion": "1.0"
}
```

### 필수 필드

| 필드 | 타입 | 설명 | 서버 활용 |
| --- | --- | --- | --- |
| `deviceId` | string | 장치 또는 가구 식별자 | 장치별 데이터 분리 |
| `windowStart` | datetime string | 분석 구간 시작 시각 | 일/주/월 집계 기준 |
| `windowEnd` | datetime string | 분석 구간 종료 시각 | 구간 길이 계산 |
| `movementScore` | number | 해당 구간 대표 움직임 점수 | 활동량 그래프, 위험 점수 |
| `presenceProb` | number | 사람 존재 확률, 0.0~1.0 | 재실 여부 판단 |
| `activityState` | string | 현재 활동 상태 | 대시보드 상태 표시 |
| `confidence` | number | 분석 신뢰도, 0.0~1.0 | 낮은 신뢰도 데이터 보정 |
| `activeSeconds` | integer | 구간 내 활동 시간 | 하루 총 활동 시간 계산 |
| `inactiveSeconds` | integer | 구간 내 무활동 시간 | 무활동 분석 |
| `movementEvents` | integer | 구간 내 움직임 이벤트 수 | 활동 빈도 분석 |
| `signalQuality` | number | 신호 품질, 0.0~1.0 | 데이터 품질 판단 |
| `schemaVersion` | string | 데이터 스키마 버전 | 포맷 변경 대응 |

### 권장 필드

| 필드 | 타입 | 설명 | 서버 활용 |
| --- | --- | --- | --- |
| `avgMovementScore` | number | 구간 평균 움직임 점수 | 시간대별 평균 활동량 |
| `maxMovementScore` | number | 구간 최대 움직임 점수 | 급격한 움직임 감지 |
| `minMovementScore` | number | 구간 최소 움직임 점수 | 정적 상태 판단 보조 |
| `sampleCount` | integer | 구간 분석에 사용한 샘플 수 | 데이터 누락 판단 |
| `source` | string | `mock`, `serial`, `udp`, `tcp`, `python-analyzer` 등 | 입력 출처 추적 |

### activityState 후보

| 값 | 의미 |
| --- | --- |
| `empty` | 사람이 없다고 추정되는 상태 |
| `present` | 사람이 있으나 움직임이 약한 상태 |
| `moving` | 움직임이 감지되는 상태 |
| `warning` | 장시간 무활동 또는 이상 징후 상태 |

## 2. 이벤트 데이터

이벤트 데이터는 특정 조건이 발생했을 때 별도로 서버에 보낸다. 웹 대시보드의 알림 로그, 위험 이력, 이상 징후 목록에 사용한다.

### 요청 예시

```json
{
  "deviceId": "home-001",
  "timestamp": "2026-05-01T14:30:00+09:00",
  "eventType": "long_inactivity",
  "severity": "warning",
  "message": "장시간 무활동이 감지되었습니다.",
  "durationSeconds": 7200,
  "movementScore": 2.4,
  "presenceProb": 0.81,
  "confidence": 0.79,
  "schemaVersion": "1.0"
}
```

### 필드 설명

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `deviceId` | string | 장치 또는 가구 식별자 |
| `timestamp` | datetime string | 이벤트 발생 시각 |
| `eventType` | string | 이벤트 종류 |
| `severity` | string | 이벤트 심각도 |
| `message` | string | 사람이 읽을 수 있는 설명 |
| `durationSeconds` | integer 또는 null | 이벤트 지속 시간 |
| `movementScore` | number 또는 null | 이벤트 시점 움직임 점수 |
| `presenceProb` | number 또는 null | 이벤트 시점 존재 확률 |
| `confidence` | number | 이벤트 판단 신뢰도 |
| `schemaVersion` | string | 데이터 스키마 버전 |

### eventType 후보

| 값 | 의미 |
| --- | --- |
| `movement_detected` | 움직임 감지 |
| `presence_detected` | 사람 존재 추정 |
| `absence_detected` | 사람 없음 추정 |
| `long_inactivity` | 장시간 무활동 |
| `activity_drop` | 평소 대비 활동량 저하 |
| `low_confidence` | 분석 신뢰도 낮음 |
| `poor_signal_quality` | 신호 품질 낮음 |

### severity 후보

| 값 | 의미 |
| --- | --- |
| `info` | 정보성 이벤트 |
| `notice` | 확인이 필요한 이벤트 |
| `warning` | 주의가 필요한 이벤트 |
| `critical` | 즉시 확인이 필요한 이벤트 |

## 3. 장치 상태 데이터

장치 상태 데이터는 활동이 없는 상황과 장치 또는 분석기 장애를 구분하기 위해 사용한다.

### 요청 예시

```json
{
  "deviceId": "home-001",
  "timestamp": "2026-05-01T10:00:00+09:00",
  "analyzerStatus": "running",
  "esp32Connected": true,
  "serverUploadStatus": "ok",
  "inputSource": "mock",
  "signalQuality": 0.91,
  "lastSampleAt": "2026-05-01T09:59:59+09:00",
  "schemaVersion": "1.0"
}
```

### 필드 설명

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `deviceId` | string | 장치 또는 가구 식별자 |
| `timestamp` | datetime string | 상태 보고 시각 |
| `analyzerStatus` | string | Python 분석기 상태 |
| `esp32Connected` | boolean | ESP32-C5 연결 여부 |
| `serverUploadStatus` | string | 서버 전송 상태 |
| `inputSource` | string | 현재 입력 방식 |
| `signalQuality` | number | 신호 품질 |
| `lastSampleAt` | datetime string 또는 null | 마지막 샘플 수신 시각 |
| `schemaVersion` | string | 데이터 스키마 버전 |

## 서버 분석에 필요한 최소 데이터

프로토타입에서 반드시 받아야 하는 최소 요청 본문은 다음과 같다.

```json
{
  "deviceId": "home-001",
  "windowStart": "2026-05-01T10:00:00+09:00",
  "windowEnd": "2026-05-01T10:01:00+09:00",
  "movementScore": 42.7,
  "presenceProb": 0.88,
  "activityState": "moving",
  "confidence": 0.84,
  "activeSeconds": 35,
  "inactiveSeconds": 25,
  "movementEvents": 4,
  "signalQuality": 0.91,
  "schemaVersion": "1.0"
}
```

이 최소 데이터만 있으면 서버는 다음 분석을 시작할 수 있다.

- 하루 총 활동 시간
- 하루 총 움직임 이벤트 수
- 최장 무활동 시간
- 시간대별 활동량
- 최근 7일 활동량 변화
- 최근 30일 활동 패턴 변화
- 위험 점수
- 대시보드 요약 카드와 그래프

## 서버 저장 테이블 초안

초기 PostgreSQL 테이블은 다음 방향으로 설계한다.

### activity_windows

| 컬럼 | 설명 |
| --- | --- |
| `id` | 내부 PK |
| `device_id` | 장치 식별자 |
| `window_start` | 구간 시작 시각 |
| `window_end` | 구간 종료 시각 |
| `movement_score` | 대표 움직임 점수 |
| `presence_prob` | 존재 확률 |
| `activity_state` | 활동 상태 |
| `confidence` | 분석 신뢰도 |
| `active_seconds` | 활동 시간 |
| `inactive_seconds` | 무활동 시간 |
| `movement_events` | 움직임 이벤트 수 |
| `signal_quality` | 신호 품질 |
| `raw_payload` | 수신 원본 JSONB |
| `created_at` | 서버 저장 시각 |

### activity_events

| 컬럼 | 설명 |
| --- | --- |
| `id` | 내부 PK |
| `device_id` | 장치 식별자 |
| `event_time` | 이벤트 발생 시각 |
| `event_type` | 이벤트 종류 |
| `severity` | 심각도 |
| `message` | 이벤트 설명 |
| `duration_seconds` | 지속 시간 |
| `movement_score` | 이벤트 시점 움직임 점수 |
| `presence_prob` | 이벤트 시점 존재 확률 |
| `confidence` | 판단 신뢰도 |
| `raw_payload` | 수신 원본 JSONB |
| `created_at` | 서버 저장 시각 |

### device_status_logs

| 컬럼 | 설명 |
| --- | --- |
| `id` | 내부 PK |
| `device_id` | 장치 식별자 |
| `reported_at` | 상태 보고 시각 |
| `analyzer_status` | Python 분석기 상태 |
| `esp32_connected` | ESP32-C5 연결 여부 |
| `server_upload_status` | 서버 전송 상태 |
| `input_source` | 입력 방식 |
| `signal_quality` | 신호 품질 |
| `last_sample_at` | 마지막 샘플 수신 시각 |
| `raw_payload` | 수신 원본 JSONB |
| `created_at` | 서버 저장 시각 |

## 추천 API 구조

초기 서버 API는 다음과 같이 잡는다.

```text
POST /api/activity/windows
POST /api/activity/events
POST /api/devices/status

GET /api/dashboard/summary
GET /api/dashboard/daily
GET /api/dashboard/weekly
GET /api/dashboard/events
```

## 구현 우선순위

1. `POST /api/activity/windows` 요청 DTO 정의
2. `activity_windows` 테이블 스키마 작성
3. Mock 데이터로 활동 구간 데이터 저장
4. 오늘 활동 요약 API 작성
5. 최근 7일 활동량 조회 API 작성
6. `POST /api/activity/events` 추가
7. 이벤트 로그 화면 연동
8. `POST /api/devices/status` 추가
9. 장치 상태 표시 화면 연동


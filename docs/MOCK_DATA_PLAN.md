# Mock 데이터 기반 개발 계획

ESP32-C5 실제 데이터 포맷이 확정되기 전까지 Mock 데이터로 Python 분석 프로그램과 서버 연동을 먼저 개발한다.

## 목표

- ESP32-C5 없이 Python 분석 파이프라인을 실행할 수 있게 한다.
- WPF 담당자가 사용할 결과 포맷을 조기에 확인할 수 있게 한다.
- 외부 서버 API와 PostgreSQL 저장 구조를 실제 센서 없이 검증한다.
- 데이터 포맷 변경 시 Parser만 교체하면 되도록 구조를 유지한다.

## Mock 입력 시나리오

| 시나리오 | 설명 | 예상 상태 |
| --- | --- | --- |
| `empty_room` | 사람이 없는 상태를 가정한다. | `empty` |
| `present_still` | 사람이 있지만 움직임이 거의 없는 상태를 가정한다. | `present` |
| `normal_moving` | 일반적인 실내 움직임을 가정한다. | `moving` |
| `long_inactivity` | 장시간 무활동 상황을 가정한다. | `warning` |
| `low_signal_quality` | 신호 품질 저하 상황을 가정한다. | `present` 또는 `warning` |

## 내부 표준 샘플 초안

Mock 데이터와 실제 ESP32-C5 데이터는 Parser를 통과한 뒤 다음 내부 표준 형태로 맞춘다.

```json
{
  "deviceId": "home-001",
  "timestamp": "2026-05-01T10:00:00+09:00",
  "source": "mock",
  "amplitudeValues": [0.12, 0.15, 0.13],
  "phaseValues": [0.02, 0.01, 0.03],
  "rssi": -48,
  "noiseFloor": -92,
  "signalQuality": 0.91
}
```

실제 ESP32-C5 포맷이 확정되면 Parser 구현체만 추가하고, 분석부는 `StandardSample`만 사용하도록 유지한다.

## 분석 결과 초안

분석 결과는 서버 전송과 WPF 출력에서 공통으로 사용할 수 있는 형태를 우선 정의한다.

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

## 구현 예정 파일

```text
pc-analyzer/python-analyzer/
├─ main.py
├─ config.py
├─ models.py
├─ input/
│  ├─ base.py
│  ├─ mock_input.py
│  ├─ serial_input.py
│  ├─ udp_input.py
│  └─ tcp_input.py
├─ parsers/
│  ├─ base.py
│  ├─ mock_parser.py
│  └─ esp32_csi_parser.py
├─ analysis/
│  ├─ analyzer.py
│  ├─ preprocessing.py
│  └─ state_classifier.py
├─ output/
│  ├─ local_api.py
│  └─ json_file_output.py
└─ transports/
   └─ server_client.py
```


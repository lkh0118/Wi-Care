# 개발 TODO

## 1단계: 구조와 문서

- [x] 프로젝트 기본 폴더 구조 생성
- [x] README 초안 작성
- [x] PROJECT_STATUS 초안 작성
- [x] 인터페이스 초안 작성
- [x] Mock 데이터 개발 계획 작성

## 2단계: Python 분석 프로그램 기초

- [ ] Python 실행 환경 정의
- [ ] `requirements.txt` 작성
- [ ] 내부 표준 데이터 모델 정의
- [ ] Mock 입력기 구현
- [ ] Parser 인터페이스 구현
- [ ] Mock Parser 구현
- [ ] 기본 분석 파이프라인 작성

## 3단계: 분석 결과 제공

- [ ] 분석 결과 JSON DTO 정의
- [ ] WPF 연동용 로컬 HTTP API 초안 구현
- [ ] JSON 파일 출력 옵션 구현
- [ ] 서버 전송 클라이언트 초안 구현
- [ ] WPF 담당자용 연동 문서 보강

## 4단계: 외부 서버 API

- [ ] FastAPI 프로젝트 생성
- [ ] API 요청/응답 DTO 정의
- [ ] PostgreSQL 연결 설정
- [ ] `devices` 테이블 스키마 작성
- [ ] `activity_windows` 테이블 스키마 작성
- [ ] `activity_events` 테이블 스키마 작성
- [ ] JSONB 원본 저장 구조 작성

## 5단계: 서버 분석 Worker

- [x] Mock 데이터 기반 일 단위 요약 생성
- [x] Mock 데이터 기반 최근 7일 활동 변화 분석
- [x] Mock 데이터 기반 최근 30일 패턴 분석
- [ ] baseline profile 생성 및 갱신
- [x] 위험 점수 계산 프로토타입
- [ ] PostgreSQL 저장 데이터 기반 Worker 연결

## 6단계: 웹 대시보드

- [x] 대시보드 기술 스택 결정
- [x] 분석 데이터 표 화면 구현
- [x] 정상/주의/경고/위험 기준치 표시
- [x] 데이터별 4단계 LED 상태 표시
- [x] 위험 점수 표시
- [ ] 최근 7일 그래프 구현
- [ ] 최근 30일 그래프 구현
- [ ] 이벤트 로그 표시
- [ ] FastAPI 기반 서버 API와 통합

## 7단계: 실제 장비 연동

- [ ] ESP32-C5 실제 데이터 포맷 수령
- [ ] 실제 Parser 구현
- [ ] Serial 입력기 검증
- [ ] UDP/TCP 확장 필요 여부 결정
- [ ] Mock 데이터와 실제 데이터 분석 결과 비교

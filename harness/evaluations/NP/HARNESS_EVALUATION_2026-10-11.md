
> **문서 성격: 평가 보고서(READ-ONLY 기록).**
> 이 문서는 범용 하네스 지침이나 새 에이전트 실행 지시가 아니다.
> 새 하네스는 HARNESS.md와 HARNESS_GUIDE.md를 먼저 읽고, NP 작업일 때만 harness/NP_ADAPTER.md와 harness/NP_WORKERS.md를 추가로 읽는다.

# 하네스 총괄 검증·평가·보완 보고서

## 검증 범위

- 총괄 컨트롤러의 단일 실행 경로와 lease
- 워커 등록·호출·완료 산출물 계약
- 상태 전이·재시도·고아 워커 복구
- 실패 상태의 heartbeat·웹앱 전파
- 1개 워커와 5개 에이전트 역할 분담
- 현재 두 NP run의 실제 상태

## 검증 결과

| 항목 | 결과 |
|---|---|
| 하네스 문법 검사 | 통과 |
| 하네스 회귀 테스트 | 16/16 통과 |
| 대시보드 테스트 | 23/23 통과 |
| 단일 워커 smoke test | 통과 |
| 5개 에이전트 분담 | 5개 작업 DONE |
| 중복 컨트롤러 차단 | 통과 |
| orphan recovery | 통과 |
| artifact 없는 DONE 거부 | 통과 |
| 잘못된 상태 전이 거부 | 통과 |
| 실패 상태 heartbeat 전파 | 보완 완료 |

## 현재 실제 상태

두 NP run 모두 `initial_ppi`를 자동 재시도했고, 3회 한도에 도달했습니다. 실패 원인은 UniProt 매핑 코드 자체가 아니라 실행 프로세스의 외부 네트워크 권한 오류(`WinError 10013`)입니다. 현재는 `FAILED`와 HIGH alert가 기록되어 무한 재시도를 하지 않습니다.

## 평가

기존 문제는 총괄이 실패를 감지하지 못한 것이 아니라, 재시도 가능 오류가 `WAITING_EXTERNAL`로 잘못 변환되어 호출 대상에서 제외된 점과 heartbeat가 `IDLE`을 표시한 점이었습니다. 재시도 계약과 실패 전파를 보완했습니다.

외부 API 전송은 보안 승인 후 별도 실행해야 하며, 승인 없이 로컬 하네스가 임의로 전송하지 않도록 유지합니다.

## 남은 작업

1. UniProt API 외부 전송 승인 후 매핑 재실행
2. 매핑 성공 시 PPI·독립 QC·원고 워커 재개
3. 외부 connector 통합 테스트와 장기 watchdog 설치


## 외부자료 이벤트 보완

- `EXTERNAL_EVENT_CONTRACT.md`와 `NP_EXTERNAL_DATA.md` 추가
- `incoming/` 업로드 자동 감지·SHA-256·provider 분류·event log 기록 추가
- 동일 파일 재수신 중복 기록 방지 테스트 추가
- 하네스 회귀 테스트: 17/17 통과

## 30분 supervisor 보완

- `supervisor.py` 추가: heartbeat·실패·무진척 점검
- 재수행 가능한 실패는 bounded requeue
- CAPTCHA·승인·보안·네트워크 권한 오류는 반복하지 않고 supervisor alert 생성
- 실제 NP 두 run에 one-shot 검증: 네트워크 권한 오류를 자동 재시도하지 않고 alert로 승격
- `run_supervisor.ps1 -IntervalSeconds 1800` 백그라운드 실행 확인

- supervisor 기본 감시 주기: 30분에서 10분으로 조정(모델 토큰 미사용)


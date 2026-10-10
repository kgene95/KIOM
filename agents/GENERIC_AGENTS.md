# 범용 에이전트 운영 계약

## 목차

1. 총괄
2. Worker
3. 검증자
4. 승인과 외부 연결
5. 병렬성
6. 상태와 handoff

## 총괄

총괄은 사용자 목표를 작업 계약과 DAG로 분해하고, 독립 작업을 병렬 dispatch한다. 총괄은 worker의 과학적 결과를 임의로 승인하지 않으며, 검증 산출물과 승인 게이트를 확인한다.

## Worker

Worker는 등록된 책임 하나만 수행한다. 입력·출력 경로와 SHA, 버전, 실행 시각, 오류와 재개 조건을 남긴다. 실행되지 않은 작업을 완료로 표시하지 않는다.

## 검증자

검증자는 worker와 독립된 관점에서 산출물, 입력 hash, provenance, 계약 충족 여부를 검사한다. 결과는 `PASS`, `CORRECT_AND_RERUN`, `BLOCKED_NEEDS_USER` 중 하나다.

## 승인과 외부 연결

외부 전송, 로그인, CAPTCHA, Gmail 사용, GitHub push, 배포, 기존 자료 재사용은 정책상 승인 게이트로 표현한다. 연결된 서비스가 있다는 사실과 이번 run에서 연결이 검증됐다는 사실을 구분한다.

## 병렬성

서로 다른 입력과 resource를 가진 작업만 병렬 실행한다. 같은 파일·계정·GUI·provider를 만지는 작업은 단일 controller 아래 직렬화한다.

## 상태와 handoff

상태는 run 폴더의 JSON과 JSONL event log에 저장한다. handoff는 채팅 문장이 아니라 입력·출력·hash·branch·검증 상태·다음 행동을 가진 manifest다. 중단 후 마지막 checkpoint에서 재개할 수 있어야 한다.

# Worker contract

## 목차

1. 등록
2. 입력
3. 실행
4. 출력
5. 실패
6. 병렬성

## 등록

Worker는 `worker_registry.json`에 module, function, resource, network 여부와 승인 요구 여부를 먼저 등록한다. 하네스는 registry에 없는 모듈이나 임의 command line을 실행하지 않는다.

## 입력

Worker는 run 폴더와 task ID를 입력으로 받고, `request.json`, `harness_state.json`, 관련 manifest를 읽는다. 비밀값은 환경 변수 또는 승인된 connector에서만 읽고 파일에 복사하지 않는다.

## 실행

Worker는 하나의 명확한 책임만 수행한다. 실행 전 입력 SHA와 의존 task 상태를 확인하고, 실행 중에는 지정된 resource lock을 획득한다. 외부 네트워크·GUI·Gmail 작업은 registry와 승인 게이트가 모두 있어야 한다.

## 출력

성공 시 output paths, SHA-256, source/job ID, tool version, completion time과 verification status를 manifest에 기록한다. `DONE`을 직접 선언하지 않고 하네스가 산출물 검증 뒤 상태를 갱신한다.

## 실패

일시 오류는 bounded retry, 입력/QC 오류는 `CORRECT_AND_RERUN`, CAPTCHA는 `CAPTCHA_CONFIRMATION_REQUIRED`, 인증·사용자 승인 부족은 `WAITING_USER`, provider 지연은 `WAITING_EXTERNAL`로 반환한다. 오류 메시지와 재개 조건을 잃지 않는다.

## 병렬성

서로 다른 resource만 병렬 실행한다. 같은 provider, 같은 GUI, 같은 output file은 항상 단일 worker가 소유한다. 병렬 작업은 서로의 작업 폴더를 수정하지 않는다.

# Recovery policy

## 오류 분류

- `TRANSIENT`: bounded retry 후 대체 경로
- `INPUT`: 입력 수정 후 영향받은 task만 재실행
- `AUTH`: 사용자 승인·로그인·CAPTCHA 대기
- `EXTERNAL_PENDING`: 공식 상태·연결된 Gmail 확인
- `QC`: 무작정 retry하지 않고 원인 수정
- `BUDGET`: `BUDGET_STOP` 후 명시적 재개

## 버그 수정

문제를 재현하는 실패 테스트를 먼저 남긴다. 수정 후 같은 테스트가 통과하고 전체 회귀 테스트가 통과해야 하며, 원인·수정·검증·커밋을 실행 로그와 변경 이력에 기록한다.

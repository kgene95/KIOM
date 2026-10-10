# Validation gates

1. 요구사항과 성공 기준 고정
2. 계획·worktree·baseline test 확인
3. 입력과 artifact contract 검증
4. 단위·통합·회귀 테스트
5. provenance·SHA·로그 검증
6. reviewer/verifier verdict
7. commit 전 검증
8. merge 후 전체 검증
9. completion record와 CHANGELOG 갱신

어느 게이트라도 실패하면 `COMPLETE`로 전환하지 않는다.

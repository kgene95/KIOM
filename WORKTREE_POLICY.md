# Worktree policy

1. workflow와 worktree를 같은 개념으로 취급하지 않는다.
2. 구현 전 기준 branch와 baseline test를 확인한다.
3. task별 branch/worktree 경로와 소유 resource를 기록한다.
4. 같은 파일·GUI·provider는 여러 worker가 동시에 조작하지 않는다.
5. worktree에서 검증한 뒤에만 commit과 merge를 수행한다.
6. merge 후 기준 branch에서 전체 검증을 다시 실행한다.
7. worktree를 제거하기 전에 checkpoint와 Git 기록을 보존한다.

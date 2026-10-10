# Domain adapter guide

adapter는 범용 하네스의 lifecycle을 복사하지 않고 다음만 제공한다.

- domain task 목록과 의존성
- 입력·출력·artifact contract
- 분야별 Skill과 tool
- 외부 connector event
- 분야별 QC와 완료 조건
- 위험한 작업과 승인 요구

현재 NP adapter는 `harness/NP_ADAPTER.md`와 `skills/run-network-pharmacology/`를 사용한다. Docking·MD·문헌·웹앱은 같은 계약으로 추가한다.

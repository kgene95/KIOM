# Evaluation guide

하네스와 adapter는 다음을 검증한다.

- dry-run이 외부 부작용 없이 계획을 만드는가
- 독립 task가 병렬화되고 resource 충돌은 직렬화되는가
- 중단 후 checkpoint에서 재개되는가
- 반복 질문을 결정 기록으로 막는가
- 오류가 bounded retry와 올바른 상태로 전환되는가
- 실패→수정→통과 회귀 테스트가 남는가
- worker가 artifact 없는 DONE을 만들 수 없는가
- commit·merge·completion이 증거를 요구하는가
- 모델 호출과 비용이 상한을 넘지 않는가

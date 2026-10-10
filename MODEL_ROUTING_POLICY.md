# Model routing policy

- deterministic: 파일 검사, 해시, 정규화, polling, schema 검증
- low: 형식 변환, 간단한 요약, 상태 분류
- standard: 계획, 일반 구현, routine debugging
- high: identity ambiguity, 충돌하는 증거, mapping anomaly, 최종 후보·기전 판단, 독립 QC 이견

각 workflow는 `max_model_calls`, `max_wall_minutes`, `max_retry_attempts`를 기록한다. 같은 오류를 반복하거나 모델을 고사양으로 승격하는 대신 `BUDGET_STOP`과 사용자 행동을 기록한다.

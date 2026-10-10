# Skill Evaluation

## 목차

1. 테스트 유형
2. 승격 기준
3. 회귀 기준
4. 현재 평가 대상

## 테스트 유형

- 정적: 목차, entrypoint, 입력·출력 계약, 금지 규칙
- dry-run: 외부 부작용 없이 DAG와 게이트 판정
- fault injection: 네트워크 오류, 손상 SHA, 누락 manifest, 중단 후 재시작
- provenance: raw archive, lineage, input/output hash
- scientific: mapping, species, branch, QC와 completion validator
- cost: 무한 retry, 모델 호출 상한, 대기 중 불필요한 모델 호출

## 승격 기준

Skill/plugin은 테스트와 검증 manifest를 통과하기 전까지 `AVAILABLE_UNVERIFIED`다. 실패하면 원인을 기록하고 같은 change set의 문서·코드·테스트를 함께 수정한다.

## 회귀 기준

새 버전은 기존 frozen branch의 결과를 조용히 바꾸지 않는다. 입력 또는 방법이 바뀌면 새 branch와 변경 이유를 기록하고, 영향을 받는 downstream만 다시 평가한다.

## 현재 평가 대상

NP 과학 규칙은 `run-network-pharmacology`, 메모리와 handoff는 `research-project-memory`, 실행 제어는 `harness`가 소유한다. Agents SDK·OpenAI plugin format·Awesome Copilot·Anthropic Skills·Superpowers는 통합 전 reference-only로 평가한다.

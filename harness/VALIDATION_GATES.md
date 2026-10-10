# NP Workflow Validation Gates

## 목차

1. 입력 게이트
2. 자료 게이트
3. 분석 게이트
4. QC 게이트
5. 원고·handoff 게이트
6. 실패 시 전이

## 입력 게이트

화합물 identity, CID/SMILES/InChIKey, 질환 ontology, 종, 분석 범위와 기존 자료 재사용 여부가 기록되어야 한다. 모호하면 `WAITING_USER`다.

## 자료 게이트

원본 파일, source URL, job ID, retrieval time, SHA-256, native score와 provenance가 있어야 한다. 기존 자료는 명시적 승인 전까지 primary branch에 들어가지 않는다.

## 분석 게이트

stable ID·species mapping QC 후 overlap을 계산한다. STRING PPI, OmniPath overlay, topology, GO/KEGG는 각각 입력 hash와 버전을 남긴다. 자료가 하나 늦어도 독립 branch는 계속하되, 최종 merge는 모든 필수 게이트 이후다.

## QC 게이트

Agent 4가 `PASS`하지 않은 결과는 최종 결과가 아니다. 새 입력 hash가 생기면 영향을 받는 하류만 `INVALIDATED`하고 재실행한다. 실패한 QC를 단순 재시도로 덮지 않는다.

## 원고·handoff 게이트

최종 Methods/Results, figure legend, docking-ready handoff는 독립 QC와 manifest 검증 이후에만 만든다. docking은 실행하지 않고 `DOCKING_NOT_STARTED`를 기록한다.

## 실패 시 전이

일시 오류는 bounded retry, 입력 오류는 `CORRECT_AND_RERUN`, 외부 승인 부족은 `WAITING_USER`, provider 지연은 `WAITING_EXTERNAL`, 반복 한도 초과는 `BLOCKED` 또는 `BUDGET_STOP`으로 전이한다.

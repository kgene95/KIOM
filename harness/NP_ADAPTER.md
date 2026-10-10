# NP Harness Adapter

## 목적

이 문서는 범용 하네스를 현재 Network Pharmacology workflow에 연결하는 adapter 계약이다. NP의 과학 규칙은 `skills/run-network-pharmacology/`에 남기고, 이 파일은 task mapping·artifact contract·외부 provider event만 정의한다.

영역별 worker와 구현 상태는 [NP_WORKERS.md](NP_WORKERS.md)와
[worker_registry.json](worker_registry.json)을 기준으로 한다. 계획된 worker는
모듈 연결과 contract test가 통과하기 전까지 dispatcher가 실행하지 않는다.

## 작업 매핑

| 범용 단계 | NP 작업 |
|---|---|
| intake / identity | compound identity, CID, SMILES, disease ontology, species |
| source audit | 기존 SEA·PharmMapper·질환 자료 감사와 재사용 승인 |
| external provider | SEA·PharmMapper 제출·job status·Gmail 결과 수신 |
| normalize | UniProt/HGNC/species/mapping QC |
| analysis | overlap, STRING, PPI, topology, GO/KEGG, OmniPath |
| independent validation | Agent 4 PASS 또는 CORRECT_AND_RERUN |
| manuscript handoff | frozen manifest 기반 Methods/Results와 docking-ready handoff |

## 연결된 외부 자산

사용자가 이미 연결해 둔 Gmail·SEA·PharmMapper 자동화는 기존 provider adapter 자산으로 간주한다. 하네스는 이를 새로 대체하지 않고, 다음 이벤트를 받아 상태와 downstream 작업만 조정한다.

- 제출 응답과 job ID
- 공식 job 상태 변경
- Gmail의 provider/job ID 일치 완료 알림
- raw 결과 저장 및 SHA 검증
- 결과 QC 통과 또는 수정 요청

연결 상태는 `connector_status`와 `verification_status`로 기록하며, 단순히 문서에 이름이 있다는 이유로 연결 완료라고 판정하지 않는다.

## 신규 실행과 과거 실행의 구분

과거 실행에서 SEA와 PharmMapper를 직접 제출하고, 작업 완료를 기다린 뒤 결과 원본을 다운로드한 기록이 있을 수 있다. 이 기록은 `historical evidence`로 보존하며, 새 run의 결과로 자동 승격하지 않는다.

새 run이 `reuse_existing: false`로 시작되면 다음을 적용한다.

1. 과거 job ID·결과 파일·SHA-256은 참고 후보로만 감사한다.
2. 현재 run에는 새로운 제출 job ID와 새로운 raw archive가 있어야 한다.
3. SEA가 CAPTCHA(현재 Altcha 포함)를 요구하면 제출 worker는 `WAITING_USER`로 전환하고, 사용자가 브라우저에서 사람 확인을 완료한 뒤 재개한다.
4. PharmMapper 응답에서 공식 작업 ID를 추출하지 못하면 `SUBMITTED_RESPONSE_REVIEW_REQUIRED`로 기록하며 성공·완료로 처리하지 않는다.
5. 공식 job ID, 결과 원본, SHA-256, 화합물 identity 검증이 모두 끝난 뒤에만 downstream 분석을 unblock한다.

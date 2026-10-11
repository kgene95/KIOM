# NP Harness Adapter

## 목적

이 문서는 범용 하네스를 현재 Network Pharmacology workflow에 연결하는 adapter 계약이다. NP의 과학 규칙은 `skills/run-network-pharmacology/`에 남기고, 이 파일은 task mapping·artifact contract·외부 provider event만 정의한다.

영역별 worker와 구현 상태는 [NP_WORKERS.md](NP_WORKERS.md)와
[worker_registry.json](worker_registry.json)을 기준으로 한다. 계획된 worker는
모듈 연결과 contract test가 통과하기 전까지 dispatcher가 실행하지 않는다.

## 작업 매핑

새 NP run은 실제 provider 호출 전에 가상 화합물·질환 시뮬레이션을 통과한다. 외부자료 CID/구조 불일치, 격리, 올바른 재업로드, 재맵핑, downstream handoff를 검증한 결과가 없으면 실데이터 run을 시작하지 않는다.

NP 기획이 끝나면 총괄은 최종 목표와 완료 기준을 사용자에게 제시하고 확인받는다. 확인된 목표는 adapter 계약에 저장하며, 시뮬레이션은 그 목표의 마지막 artifact까지 도달해야 통과한다. 실제 실행 중 오류가 생기면 수정된 adapter 계약으로 실패 지점부터 최종 목표까지 빠른 시뮬레이션을 다시 돌린 후 실데이터 run을 재개한다.

NP adapter의 방향 변경, 재분석, 외부자료 교체, 후보 선정과 같은 변경 요청은 요청 해석과 현재 evidence 상태, 총괄의 추천 방향, 대안, 영향과 완료 기준을 먼저 제시하고 사용자 확인 후 queue에 반영한다. 단순 조회·검수·재현 테스트는 즉시 수행한다. 입력 identity 불일치나 중복 제출 위험은 확인을 기다리지 않고 해당 branch를 격리한 뒤 보고한다.

adapter는 시뮬레이션에서 사용할 입력·오류 주입·기대 상태·완료 artifact를 정의한다. 정상 provider 결과, 잘못된 CID 또는 구조, 중복 업로드, 외부자료 지연, worker 재시작을 가상으로 주입하고 `external_validation_manifest`, route report, 수신 worker 결과, 최종 NP artifact가 모두 일관되는지 확인한다. 시뮬레이션 실패는 실제 provider 호출 전 차단 사유로 기록한다.

| 범용 단계 | NP 작업 |
|---|---|
| intake / identity | compound identity, CID, SMILES, disease ontology, species |
| source audit | 기존 SEA·PharmMapper·질환 자료 감사와 재사용 승인 |
| external provider | SEA·PharmMapper 제출·공식 job status·원본 다운로드 |
| normalize | 표준 protein accession/HGNC/species/mapping QC (`uniprot_mapping_qc`) |
| analysis | overlap, STRING, PPI, topology, GO/KEGG, OmniPath |
| independent validation | Agent 4 PASS 또는 CORRECT_AND_RERUN |
| visualization | 검증된 PPI를 Cytoscape로 재현하고 네트워크·허브 artifact 생성 |
| docking handoff | Cytoscape/QC 근거 기반 도킹 후보 선정 및 `docking_candidates.json` |
| manuscript handoff | frozen manifest 기반 Methods/Results와 figure legend 초안 |

실행 큐의 후반부는 `manuscript_review → cytoscape_visualization → docking_candidate_selection → methods_results_draft → completion_packager` 순서로 고정한다. 문서에만 있는 단계를 완료로 간주하지 않으며, 각 단계의 registry·dispatcher·artifact contract가 모두 있어야 한다.

`uniprot_mapping_qc`는 외부 표적 자료를 downstream 분석에 전달하기 전의 필수 gate다. `compound_targets.csv`와 질환 표적을 입력으로 받아 표준 protein accession, human species, mapping status, 중복·obsolete·ambiguous 여부를 확인하고 `normalized_targets.csv`, `uniprot_mapping_manifest.json`, 필요 시 `uniprot_unmapped.csv`를 생성한다. manifest가 PASS가 아니면 overlap·STRING·Cytoscape worker를 dispatch하지 않는다. 외부 결과나 입력 hash가 바뀌면 이 worker와 영향을 받는 downstream task를 함께 재실행한다.

## 연결된 외부 자산

사용자가 이미 연결해 둔 Gmail·SEA·PharmMapper 자동화는 기존 provider adapter 자산으로 간주한다. 하네스는 이를 새로 대체하지 않고, 다음 이벤트를 받아 상태와 downstream 작업만 조정한다.

- 제출 응답과 job ID
- 공식 job 상태 변경
- PharmMapper Check Job의 provider/job ID 일치 상태·공식 다운로드
- Gmail의 provider/job ID 일치 완료 알림(선택적 보조 이벤트)
- raw 결과 저장 및 SHA 검증
- 결과 QC 통과 또는 수정 요청

연결 상태는 `connector_status`와 `verification_status`로 기록하며, 단순히 문서에 이름이 있다는 이유로 연결 완료라고 판정하지 않는다.

## 신규 실행과 과거 실행의 구분

과거 실행에서 SEA와 PharmMapper를 직접 제출하고, 작업 완료를 기다린 뒤 결과 원본을 다운로드한 기록이 있을 수 있다. 이 기록은 `historical evidence`로 보존하며, 새 run의 결과로 자동 승격하지 않는다.

새 run이 `reuse_existing: false`로 시작되면 다음을 적용한다.

1. 과거 job ID·결과 파일·SHA-256은 참고 후보로만 감사한다.
2. 현재 run에는 새로운 제출 job ID와 새로운 raw archive가 있어야 한다.
3. SEA가 CAPTCHA(현재 Altcha 포함)를 요구하면 제출 worker는 `CAPTCHA_CONFIRMATION_REQUIRED`를 기록하고, 행동 직전 확인 후 Agent 2가 브라우저에서 사람 확인을 수행한 뒤 재개한다.
4. PharmMapper 응답에서 공식 작업 ID를 추출하지 못하면 `SUBMISSION_NOT_CONFIRMED`로 기록하며 성공·완료로 처리하지 않는다. 공식 페이지의 JavaScript 오류, 비활성화된 Submit 버튼, 빈 응답이 있으면 같은 요청을 반복 전송하지 않는다. 접수·완료 메일 부재는 실패 조건이 아니다.
5. 공식 job ID, 결과 원본, SHA-256, 화합물 identity 검증이 모두 끝난 뒤에만 downstream 분석을 unblock한다.

### 외부 제출 책임

SEA·PharmMapper 제출은 사용자가 매번 수동으로 수행하는 단계가 아니라 Controller/Agent 2가 맡는 실행 작업이다. 총괄은 검증된 구조와 승인 정보를 사용해 공식 제출 화면을 열고, 입력·CAPTCHA 확인·제출·작업 ID 기록·결과 회수까지 직접 수행한 뒤 다음 작업으로 연결한다. 사용자는 정상 실행 중간에 반복해서 개입하지 않는다. CAPTCHA 클릭처럼 외부 서비스에 직접 영향을 주는 순간에는 해당 행동 직전에만 확인을 받고, 확인 뒤 같은 실행 흐름에서 즉시 재개한다. 이를 일반 대기나 사용자 수행 작업으로 분류하지 않는다.

같은 `SUBMITTED_RESPONSE_REVIEW_REQUIRED` 또는 `WAITING_USER` 상태를 반복 보고하거나 재제출하지 않는다. `run_id`, provider, 상태, next action의 fingerprint와 `action_notice_id`를 기록하고, 상태가 바뀌거나 사용자가 조치할 때만 새 보고를 만든다.

## 무진척 감시와 보고 계약

NP supervisor는 1분마다 controller heartbeat, queue, task 상태, artifact 변화를 확인한다. 어느 worker라도 실행 중이거나 실제 상태·artifact가 갱신되면 정상 진척으로 간주하고 중간 polling 보고를 반복하지 않는다. worker·task가 완료되면 완료된 분석, artifact, 다음 분석 worker를 총괄이 보고한다. 오류 해결·재수행·재시작을 시도한 뒤에도 5분 이상 변화가 없을 때만 총괄이 원인, 시도한 복구, 관련 task와 다음 행동을 보고한다. 이 조건은 외부 제출 대기와 내부 분석 대기를 구분하며, 대기 상태를 이유로 전체 run을 종료하지 않는다.

### 제출 실패 재개 절차

제출 실패는 다음 순서로 처리한다.

1. 공식 브라우저 화면, HTTP/브라우저 콘솔 오류, 응답 본문, job ID 표시 여부를 보존한다.
2. PharmMapper는 공식 Check Job 화면에서 기록된 Job ID를 조회한다. `PENDING/RUNNING`이면 다음 조회 시각을 기록하고 독립 task를 계속한다.
3. Job ID가 없으면 상태를 `SUBMISSION_NOT_CONFIRMED`로 바꾸고, 재전송하지 않는다. 메일 미수신은 이 상태를 유발하지 않는다.
4. 사용자가 직접 제출해야 하는 경우에는 공식 제출 URL과 복사 가능한 입력 파일 폴더 주소를 제공한다. 사용자는 파일 선택·필수 입력·CAPTCHA만 수행한다.
5. 공식 job ID가 확인되면 `record_external_job` 경로로 ledger와 progress를 갱신하고 결과 회수 worker를 재개한다.
6. 같은 오류가 재현되면 `CORRECT_AND_RERUN`으로 기록하고, 원인 수정·재현 테스트·통과 확인 후에만 다음 제출을 시도한다.

## 외부자료 이벤트 handoff

NP run의 외부자료는 `external_data_intake`가 첫 수신자다. 검수 worker가 `external_validation_manifest.json`을 만든 뒤 `worker_notifications.jsonl`에 `sea_collect` 또는 `pharmmapper_collect`를 수신자로 기록한다. 수신 worker는 `*_intake_handoff.json`을 만들고 원본 hash를 기준으로 재맵핑·표준 변환을 수행한다. 이 handoff가 없으면 이전 결과를 새 입력으로 간주하지 않는다.

## 계획 밖 이벤트 담당 Agent 6

NP adapter의 `agent6/event_agent_router`는 PharmMapper·SEA·Gmail 첨부, 사용자가 추가로 제공한 분석자료, 사용자가 실행 중 추가로 지시한 업무를 담당한다. 자료를 검수한 뒤 provider·CID·입력 hash를 기준으로 `sea_collect`, `pharmmapper_collect`, `initial_ppi`, 또는 새 task로 라우팅한다. 원래 담당 worker에 handoff 완료를 보고하고, 총괄에는 `event_agent_report.json`과 event log로 route·오류·다음 행동을 보고한다. 계획 밖 이벤트가 생겼는데 Agent 6 report가 없으면 NP run은 완료가 아니다.

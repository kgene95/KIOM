# NP 영역 워커 구성

## 원칙

Agent는 책임 영역을 조정하고, worker는 한 가지 검증 가능한 작업을 수행한다. `worker_registry.json`에서 `status`가 `implemented`인 항목만 dispatcher가 호출할 수 있다.

## 총괄 영역

| 역할 | 책임 | 실행 방식 |
|---|---|---|
| Controller | 목표, 승인, 예산, 의존성, 재개 | `np_harness.py` |
| State worker | 상태·이벤트·checkpoint 기록 | `state_store.py` |
| Verifier | artifact·SHA·gate 판정 | `verifier.py` |

## Agent 1: 입력·구조·자료 준비

| worker | 산출물 | 현재 상태 |
|---|---|---|
| `compound_identity` | identity manifest, 구조 SHA | planned |
| `disease_target_collection` | 질환 표적 manifest | planned |
| `structure_qc` | 구조 QC manifest | planned |
| `source_audit` | 재사용·재수집 판단 manifest | planned |

## Agent 2: 외부 provider

| worker | 산출물 | 현재 상태 |
|---|---|---|
| `sea_submit` | SEA job ledger | planned |
| `pharmmapper_submit` | PharmMapper job ledger | planned |
| `sea_collect` | raw 결과·SHA·수집 manifest | planned |
| `pharmmapper_collect` | raw 결과·SHA·수집 manifest | planned |
| `pharmmapper_check_job` | Job ID 상태 조회·공식 다운로드 metadata | planned |
| `gmail_job_monitor` | 선택적 보조 알림 metadata | planned |

제출 worker는 최초 승인과 공식 경로를 확인한다. CAPTCHA는 `CAPTCHA_CONFIRMATION_REQUIRED`를 거쳐 Agent 2가 직접 수행하고, 로그인·이메일 입력 등 별도 정보가 필요한 경우에만 해당 상태를 기록한다. PharmMapper 결과는 이메일이 아니라 `pharmmapper_check_job`가 공식 Check Job 화면에서 Job ID로 조회한다. Gmail worker는 선택적 보조 알림만 다루며 메일 본문과 주소를 저장하지 않는다.

### 외부 제출 상태 규칙

이전 실행에서 제출·대기·다운로드가 완료된 사실은 새 run의 자동 완료 근거가 아니다. 새 run은 기존 자료 재사용 승인 없이는 과거 결과를 사용하지 않는다.

- SEA: SMILES 입력 후 CAPTCHA가 표시되면 `CAPTCHA_CONFIRMATION_REQUIRED`; 행동 직전 확인 후 Agent 2가 사람 확인·제출·job ID 확인을 재개한다.
- PharmMapper: 이메일은 제출 화면에서 필요한 경우 현재 세션에서만 사용하고 파일·로그·manifest에 저장하지 않는다. 제출 응답의 공식 Job ID를 즉시 기록한 뒤 Check Job에서 상태를 조회한다. Job ID가 없으면 `SUBMISSION_NOT_CONFIRMED`로 중지하고, 메일 미수신을 실패로 판정하거나 자동 재전송하지 않는다.
- 두 provider 모두 raw 결과와 SHA-256, CID/구조 identity 검증 전에는 `DONE`이나 downstream unblock을 선언하지 않는다.

제출 책임은 Agent 2와 총괄 Controller에 있다. 정상적인 입력·CAPTCHA 확인·제출·작업 ID 확인·결과 회수는 에이전트가 직접 수행하며 사용자는 진행 중 매 단계마다 클릭하거나 명령을 입력하지 않는다. CAPTCHA 클릭 직전에는 `CAPTCHA_CONFIRMATION_REQUIRED`를 기록하고 행동 확인을 받은 뒤 즉시 같은 worker를 재개한다.

## Agent 3: 계산·통합 분석

### 다성분 연구 project 통합

성분이 여러 개이고 논문이 하나인 경우 총괄은 성분별 child run을 독립적으로 검증한 뒤 project-level 통합을 반드시 호출한다. 이 통합은 성분 worker가 아니라 Controller가 소유하고, supervisor가 child run 완료 이벤트를 감지하면 자동 실행한다. 통합기는 각 child의 Cytoscape degree artifact·Figure 초안·completion manifest를 확인하고, 공통 Top-10 허브·성분별 허브·통합 provenance를 생성한다. child 결과가 부족하면 `WAITING_CHILD_RUNS`를 기록하고 멈춰 있지 말고 supervisor가 재확인·재개한다.

| worker | 산출물 | 현재 상태 |
|---|---|---|
| `normalize_targets` | stable-ID/species QC | planned |
| `overlap_analysis` | overlap table | planned |
| `ppi_analysis` | PPI·topology 결과 | planned |
| `enrichment_analysis` | GO/KEGG/Reactome 결과 | planned |
| `integration_analysis` | 통합 manifest | planned |
| `cytoscape_visualization` | Cytoscape primary network·degree·MCODE manifest | implemented |

`cytoscape_visualization`은 검증된 `ppi_manifest.json`을 frozen 입력으로 사용한다. Cytoscape/cyREST가 실행 중이 아니면 `WAITING_EXTERNAL`과 `reason_code=WAITING_CYTOSCAPE_ONLINE`을 남기며, 실제 Cytoscape 결과로 위장하지 않는다.

## Agent 7: 도킹 후보 handoff

| worker | 산출물 | 현재 상태 |
|---|---|---|
| `docking_candidate_selection` | `docking_candidates.json` | implemented |

도킹 후보 선정은 Cytoscape와 독립 QC가 모두 통과한 뒤에만 수행한다. 이 단계는 후보와 근거를 확정하는 단계이며 실제 AutoDock/Vina 계산은 별도 도킹 workflow에서 수행한다.

## Agent 4·5: 품질과 결과

| worker | 완료 조건 | 현재 상태 |
|---|---|---|
| `independent_qc` | `PASS` 또는 수정 요청 | planned |
| `manuscript_review` | 검토 manifest | planned |
| `methods_results_draft` | `methods_results_draft.md` | implemented |
| `completion_packager` | 결과·manifest·raw 패키지 | implemented |

## 실행 규칙

새 분석 전에는 가상 입력과 의도적 외부자료 오류를 포함한 사전 시뮬레이션을 실행한다. 잘못된 CID·구조 자료가 격리되고, 올바른 재업로드가 자동 재검수·재라우팅되며, PPI·enrichment·MCC/MCODE·Figure·도킹 후보 추천·Methods/Results·완료 보고서까지 생성되는지 확인한다. 후보 추천과 보고서가 빠진 시뮬레이션은 통과시키지 않는다. 실패한 시뮬레이션은 worker 회귀 실패로 기록하고 실제 분석을 시작하지 않는다.

worker 시뮬레이션은 정상 순서만 확인하지 않는다. 각 worker의 실행 중간에 외부자료 도착, 잘못된 파일, 중복 이벤트, 실패·재시작을 주입하고, 담당 worker가 입력 계약을 검증한 뒤 결과·오류·다음 action을 총괄과 수신 worker에게 전달하는지 확인한다. 복구 후에는 실패 task만 재실행되고 독립 worker가 계속 수행되며, 마지막 목표 artifact와 QC 상태가 생성되어야 통과다.

1. 독립 resource는 병렬 실행한다.
2. 같은 provider·브라우저·출력 파일은 lock으로 직렬화한다.
3. 모든 worker는 run 폴더, task ID, 입력 hash를 받는다.
4. worker는 출력 manifest를 만들고, 최종 `DONE`은 verifier가 선언한다.
5. 오류는 `WAITING_USER`, `WAITING_EXTERNAL`, `CORRECT_AND_RERUN`, `BUDGET_STOP` 중 하나로 기록한다.
6. 최종 완료는 `independent_qc → manuscript_review → cytoscape_visualization → docking_candidate_selection → methods_results_draft → completion_packager` 전체가 통과한 경우에만 허용한다.

## worker 진척 보고와 supervisor 감시

각 worker는 시작·상태 변경·재수행·완료 또는 실패 시 queue와 event log를 갱신한다. supervisor는 1분마다 이를 확인하며, 어떤 worker라도 실제 실행 또는 artifact 갱신이 있으면 사용자에게 무진척 보고를 만들지 않는다. 오류 해결·재수행·재시작 후 5분 이상 변화가 없을 때만 총괄에 원인과 다음 행동을 알리고, 재수행 가능한 task는 `READY_FOR_WORKER`로 재큐잉한다. 외부 승인·보안·네트워크 차단은 반복하지 않고 재개 조건을 기록한다.

### 제출 실패 시 사용자 안내

제출 실패가 발생하면 총괄은 사용자에게 같은 질문을 반복하지 않고 한 번에 다음 정보를 제공한다.

- 공식 제출 사이트 주소
- 화합물별 입력 파일의 절대 폴더 주소와 파일명
- 복사·붙여넣기 가능한 job description
- 사이트에서 수행할 단계(파일 선택, 이메일 입력, 설정, Submit)
- 실패 시 캡처할 화면과 확인할 오류(job ID, 메일, 비활성화 버튼, CAPTCHA)

사용자가 제출한 뒤 job ID를 전달하면 worker는 ID·provider·compound identity를 대조하고 ledger를 갱신한다. ID가 없으면 이전 ID나 historical evidence를 현재 run에 연결하지 않는다.

## 외부자료 검수·재맵핑 워커

`external_data_intake`는 Agent 0에 속한 경계 worker다. 업로드 원본을 `source_archive/ExternalIntake/`에 보존하고 `external_validation_manifest.json`에 SHA·provider·CID·검수 상태를 기록한다. 성공하면 담당 provider worker에 `worker_notifications.jsonl`로 전달한다. `sea_collect`와 `pharmmapper_collect`는 알림을 소비해 `*_intake_handoff.json`을 만들고, 원본을 표준 `compound_targets.csv`로 변환한 뒤 stable-ID mapping worker를 재실행한다. 한 worker가 실패해도 총괄은 알림 누락·재실행 여부를 확인하고, 필요한 경우 같은 worker를 bounded retry한다.

## Agent 6: 계획 밖 이벤트 라우터

| worker | 역할 | 산출물 |
|---|---|---|
| `event_agent_router` | 외부자료·추가업무 검수, 재맵핑 route, 담당 worker handoff, 총괄 보고 | `event_agent_report.json`, `external_validation_manifest.json`, event log |

Agent 6은 원래 분석 worker의 일을 대신하지 않는다. 자료를 검수하고 올바른 worker를 깨우며, 수신 worker가 실제로 재실행했는지 확인한다. 사용자가 진행 중 추가 데이터를 주면 기존 결과와 자동 병합하지 않고 새 event/task로 기록한다. CID·구조 hash·provider가 맞지 않으면 해당 branch만 격리하고 총괄에 즉시 보고한다.

## 후반부 자동 통합 파이프라인(개정)

총괄 controller는 enrichment 결과가 생성되었다고 바로 Figure·도킹·원고를 호출하지 않는다. 다음 artifact handoff를 순서와 의존성으로 확인한다.

1. `experimental_evidence_synthesis` (Agent 4): 동물·세포 실험 결과를 evidence schema로 정규화하고 방향·모델·출처를 기록한다.
2. `mechanism_enrichment_synthesis` (Agent 4): STRING GO/KEGG와 실험 evidence를 교차검증하고, 각 범주 상위 7개 term과 제외 이유를 기록한다.
3. `cytoscape_visualization` (Agent 3): 통합 PPI를 Cytoscape에 불러와 degree·CytoHubba MCC·MCODE 결과를 생성한다.
4. `figure_draft` (Agent 5): 검증된 PPI·MCC/MCODE·기전 enrichment만 사용해 패널 초안을 만든다. 수치가 없으면 placeholder로 완료 처리하지 않는다.
5. `docking_candidate_selection` (Agent 7): 실험 evidence + MCC + MCODE + degree + UC pathway + 구조 가용성을 교차평가해 3–5개 후보를 추천한다.
6. `methods_results_draft` (Agent 5): 위 artifact와 provenance를 인용해 Methods/Results 초안을 작성한다.
7. `manuscript_review`와 `completion_packager`: 과학적 주장·그림·후보·원자료 hash를 함께 검토한 뒤 완료 패키지를 만든다.

총괄은 각 단계의 `worker_results/*.json`, 입력 hash, 산출물 존재, 오류·재시도 event를 확인한 후 다음 worker를 자동 dispatch한다. 하나의 worker가 대기해도 독립적인 evidence 수집과 QC는 계속 수행하되, 의존 단계는 임의로 DONE 처리하지 않는다.

### Figure term 선택 규칙

GO BP·CC·MF와 KEGG는 전체 결과를 삭제하지 않는다. Supplementary table에는 전체 결과를 보존하고, 본문 Figure에는 유의도(FDR), Gene ratio, Count, UC 기전 관련성, term 중복을 평가해 범주별 약 7개를 표시한다. 이 선택 규칙과 제외 term은 manifest에 저장한다.

### 도킹 후보 규칙

degree만으로 후보를 확정하지 않는다. MCC와 MCODE artifact가 없으면 `WAITING_EXTERNAL`로 남기고 총괄에 재개 조건을 보고한다. 실험 evidence가 없는 후보는 예비 후보로만 표시하며 최종 추천에 포함하지 않는다.

### 도킹 후보 검증 확장 단계

`docking_candidate_selection` 전후에는 다음 세부 검증을 병렬로 수행한다.

1. `compound_target_match_audit`: 프로젝트 adapter가 정의한 각 입력 성분 양쪽에 실제로 매칭되는지, 프로젝트별 공동 표적 집합에 포함되는지 확인한다. 전체 provider 공통 수와 최종 분석 교집합 수를 별도 필드로 기록한다.
2. `target_mechanism_literature_audit`: 해당 질환·표현형 기전, 입력 성분–표적 근거, 최신 문헌을 확인하고 DOI/PMID와 검색 시점을 기록한다. 제공된 동물·세포 실험 근거는 있으면 가점으로 반영하고 없으면 `미확인`으로 남긴다.
3. `target_structure_docking_audit`: UniProt/PDB identity, 해상도, co-crystal ligand, 결합 포켓, kinase·metalloprotease·nuclear-receptor 도메인, 막단백질·무질서 영역·multimer 의존성을 확인한다. 적합하지 않은 표적은 이유와 함께 보류한다.
4. `docking_candidate_ranker`: compound match + MCC/MCODE/degree + 기전·문헌 + 구조 적합성을 통합해 순위와 짧은 선정 사유를 만든다. 실험 근거가 없다는 이유만으로 자동 탈락시키지 않되, 문헌과 구조 근거가 없는 표적은 최종 추천에서 보류한다.

이 네 단계의 결과와 근거 파일이 모두 존재해야 `RECOMMENDATION_READY`를 허용한다. 실제 도킹 계산은 별도 도킹 하네스로 handoff하며, 후보 선정 결과를 도킹 결과로 표현하지 않는다. 프로젝트 고유 성분명·질환명·교집합 수·marker 연결은 각 프로젝트의 `<PROJECT_NAME>.md`에서만 읽는다.

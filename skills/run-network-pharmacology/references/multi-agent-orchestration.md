# NP 다중 에이전트 운영 설계 — 한국어 기본 정책 (v2)

## 한국어 의무
사용자 질문, 답변, 진행상황, 승인 요청, 경고 및 최종 보고는 사용자의 입력 언어와 관계없이 **한국어**로 작성한다. DB 이름, 파일 경로, 프로그램명, 유전자명, 표준 생물학 명칭은 원어 병기가 허용된다. 구조화된 기계 출력의 key는 영어 가능하지만 사용자 표시용 설명은 한국어다. 이 규칙은 총괄 및 세부 에이전트 1~5 모두에 적용한다.

## 실제 역할 구성
- 총괄 에이전트 0: 화합물명/CID(여러 개 가능), 질환명, 생물종(Homo sapiens 기본값), 기존 자료 재사용 승인 접수. 작업 큐, 재시도, 비용, 알림과 의존성 관리. 별도 Python 실행기에서 상태 유지.
- 세부 에이전트 1, NP 자료·화학구조 담당: CID/SMILES/InChIKey/3D SDF·MOL2 구조 QC, 질환 유전자·화합물 표적 수집, 기존 데이터 탐색 및 비-SEA/PharmMapper 분석. 유효한 구조가 나오자마자 2번에 인계.
- 세부 에이전트 2, SEA·PharmMapper 전담: 1번의 구조 인계 파일을 검증하고 기존 데이터 승인 상태를 확인한 후 서비스에서 지원하는 공식 경로로 제출, job ID/입력 SHA 저장, 결과 상태 조회·원본 수집·검증. 이메일은 서비스의 알림 또는 확인 용도로만 사용한다. 자동 제출 지원 여부는 서비스별로 실제 검증해야 하며 미검증이면 NEEDS_EXTERNAL_SUBMISSION으로 대기.
- 세부 에이전트 3, STRING·Cytoscape·네트워크/경로 분석: 1·2번이 진행 중이어도 검증된 독립 자료가 도착하면 예비 브랜치에서 즉시 시작. PPI, degree, cytoHubba(지원되는 공식 경로 또는 GUI), MCODE, GO BP/CC/MF, KEGG, Reactome, g:Profiler. 최종 네트워크는 모든 필수 표적과 mapping QC 후 별도 확정. 예비 자료와 확정 결과를 섞지 않음.
- 세부 에이전트 4, 독립 QC·차등 재실행: 모든 새 데이터 도착 이벤트마다 화합물-작업 매핑, UniProt/HGNC/종, 원본 SHA, UC 질환 배경, STRING 매핑, PPI/경로 결과를 검토. 새 입력이 기존 결과를 바꾸는 경우 3번 작업을 invalidated로 표시하고 재실행 의뢰. PASS·REVISE·BLOCKED를 기록. 독립 QC 이전에 완결 선언 금지.
- 세부 에이전트 5, 논문용 Methods·Results 근거 검토: 실험 원고, 동물·세포 데이터 및 NP 분석 결과가 들어오면 바로 문헌·원고 자료 목록과 문장 근거를 검토할 수 있음. 최종 통계·기전 결론 및 논문용 Figure legend는 4번의 PASS 후 확정. 실제 NP Methods/Results 초안 본문 작성은 기존 NP 스킬의 사용자 승인 조건을 지킨다.

## 작업 큐와 인계 구현
`scripts/np_agent_queue.py`는 RUN_ID 기반 작업 큐를 생성하고 단일 실행으로 상태를 확인한다. `--new --compound <CID/name> --disease <name> --species <organism>`으로 새 분석을 만들고, `--run <run folder>`로 인계·결과 상태를 갱신한다. 모든 실행에는 `request.json`, `work_queue.json`, `execution_state.json` 사용.
1번은 `structure_manifest.json`에 CID, SMILES, structure_qc=PASS, 필요 시 structure_file 및 structure_sha256 입력. 실행기가 구조 검증 후 `handoff_to_agent2.json` 생성.
2번은 `job_ledger.json`에 명시된 CID, 구조 SHA 및 작업 ID가 맞아야 제출 완료로 처리된다. `sea_result_manifest.json`과 `pharmmapper_result_manifest.json`에 각 job_id, CID, raw_file, SHA, verified=true가 모두 일치할 때만 수집 완료.
3번은 질환 표적 데이터와 검증된 PPI 입력이 존재할 때 예비 분석 가능. 4번이 PASS 하지 않으면 최종 완결 금지.
승인 및 검증 조건을 만족하지 않는 서비스 제출, 원고 최종화, 결과 병합은 자동 실행하지 않음.

## 아직 연결되지 않은 서비스
현재 실행기는 작업 생성/의존성/핸드오프 검증이며 SEA·PharmMapper 사이트의 실사용 자동 제출 API 또는 브라우저 자동화와 결합되지 않았다. 공식 제출·결과 API를 확인하고 CAPTCHA/로그인이 필요한 경우 사용자 개입이 필요하다. 로컬 감시기는 고정된 이전 UC 프로젝트 전용이므로 신규 RUN_ID의 감시를 위해 run registry 확장이 추가로 필요하다. ChatGPT 기반 세부 에이전트가 24시간 독립 실행된다고 주장하면 안 된다.

---
# NP multi-agent orchestration (v1, 2026-10-10)

## Purpose
This design implements a *single controlled workflow* with role-specific workers. It does not imply autonomous ChatGPT subagents or background LLM execution. Workers may be scripts, connected tools or authorized assistants. Use this design for future compounds/extracts and diseases.

## Intake by overall controller (agent 0)
Required: compound name or PubChem CID for each compound; disease name. Optional: SMILES, InChIKey, SDF, MOL2, extract-to-compound table, species (default Homo sapiens), disease ontology ID, study aim, output workspace.
Create a dedicated RUN_ID and a frozen `request.json` under `runs/<RUN_ID>/`. Resolve disease ontology and PubChem identity. Check stereochemistry, 3D conformer validity, tautomers/salts, and source-specific formats.
If chemical identity is ambiguous, request user confirmation before submissions.
Audit authorized workspace for pre-existing SEA/PharmMapper and other outputs. Show evidence matches and mismatches and obtain explicit user decision REUSE_VERIFIED or RECOLLECT_NEW before a new submission or before treating old material as study evidence. NEVER overwrite source files.

## Role 1 — NP analyst
- Start disease-target/source access audit and collect independent fast/accessible compound-target evidence immediately.
- Prepare separate immutable compound identity package: compound_id, CID, canonical/isomeric SMILES, InChIKey, provenance, validated SDF/MOL2 where required, chemical structures, SHA256, date, mapping warnings.
- Persist `handoff_to_agent2.json` with absolute *authorized local paths*, hashes, species, source parameters, submit approval/status and RUN_ID.
- Hand off as soon as structure validation passes, in parallel with disease and other target collection. Do not wait for Agent 2 before running independent branches.
- After Agent 2 returns verified archives, merge through HGNC/UniProt QC, overlap, STRING, Cytoscape, GO/KEGG and docking candidate recommendation (NO DOCKING EXECUTION).

## Role 2 — SEA & PharmMapper collector
- Read handoff manifest and verify checksums/identities before submission.
- SEA uses validated SMILES and the job/compound identity on its actual supported user interface/API; PharmMapper uses a supported MOL2/SDF upload and may require a recipient email or confirmation.
- **Email is a communication/notification channel, not the universal way of submitting structures to SEA or PharmMapper.** Prefer secure project-local handoff, not raw molecular attachments by email between worker roles. Send minimal email notification only when authorized; do not persist email addresses, secrets, or message contents in shareable data.
- If a service explicitly supports an email submission route, verify official instructions before use; never assume this.
- Submit one job per exact chemical identity only when new-collection approval is recorded. Persist `job_ledger.csv` with RUN_ID, CID, structure SHA, provider, job ID, URL, submission time, options, status; exclude private email addresses.
- Poll official job URL/email results through authorized connectors. Store PENDING without claiming background continuity absent scheduled automation. Preserve raw original, retrieval time, SHA256, source version, native ranks.
- Verify result job corresponds to submitted structure and species; fail closed as UNVERIFIED if correspondence cannot be proven. Never reuse an old job merely because its ID or name looks plausible.
- Emit `handoff_from_agent2.json` with dataset paths, result SHA256, IDs, native metrics and QC status.

## Role 3 — independent evidence auditor
- Check compound identity, source metadata, raw/processed lineage, disease universe, species, one-to-many mapping and exclusions, native-score interpretation, thresholds, STRING and enrichment mapping drift.
- Reject unverified SEA assignments from primary branch; allow explicitly labeled sensitivity/proxy branch only.
- Return PASS / CORRECT_AND_RERUN / BLOCKED_NEEDS_USER plus specific affected stages and required evidence.
- Only after independent PASS may overall controller mark COMPLETE and send final delivery.

## Overall controller orchestration
1. INTAKE -> IDENTITY_QC.
2. SOURCE_AUDIT -> WAITING_REUSE_APPROVAL if matching prior archives exist.
3. Run Role 1 independently; when valid structure package exists, queue Role 2 without requiring the entire NP analysis to finish.
4. Role 2 statuses: QUEUED, SUBMITTED, PENDING, RETRIEVED, VERIFIED, ERROR_RETRY, NEEDS_USER, UNAVAILABLE.
5. On Role 2 VERIFIED, wake Role 1 for gene mapping/merge and invalidate/rerun affected downstream branches; Role 3 re-audits.
6. Terminal status COMPLETE only after QC PASS, figures/report/manifest exist. NO docking execution.

## Fault and resource policy
- Local Python scheduler polls pending work every 30 minutes without LLM calls, respecting providers' terms/rate limits; ChatGPT checks at 09:00 and 18:00 Korea time only for meaningful changes.
- Retry transient network errors up to 3 times with bounded backoff, record alternative routes; auth/CAPTCHA/user reuse approval stops at NEEDS_USER.
- Use one reviewed Python controller invocation for multiple deterministic subtasks and durable atomic checkpoints. Do not try to bypass tool permission requests.
- Do not send raw research materials to a third-party email address without explicit authorization. Institutional privacy policies and terms of the destination service still apply.
- Gmail recipient and OAuth credentials stay runtime-private. `email_notification_status` can be logged, not addresses/message bodies.
- The GitHub repository carries reusable code/templates only; never publish research source archives, private emails, or user-specific local state.

## Required machine-readable run artifacts
`request.json`, `compound_identity.csv`, `structure_manifest.json`, `handoff_to_agent2.json`, `job_ledger.csv`, `handoff_from_agent2.json`, `source_attempts.csv`, `source_archive_index.csv`, `data_lineage.csv`, `execution_state.json`, `NP_manifest.json`, QC report and result files.

## Current project note
Previously saved SEA job folders 41debffd05f4 and 47e4702598a2 exist, with their compound assignment unverified. They are historically archived and must not be classified as verified inputs. A fresh submission can solve this, provided input compound identity and provider route are recorded. This historical example is not a universal input template.

## 기존 데이터 우선 운영 원칙 (2026-10-10 추가)
1. 새 분석의 화합물명/CID, 질환명, 생물종을 등록하면 원본 자료를 새로 수집하기 전에 모든 접근 가능한 연구 작업 폴더의 기존 파일 및 메타데이터를 탐색한다.
2. SEA, PharmMapper, SwissTargetPrediction, 질환 유전자, STRING, GO/KEGG, Cytoscape 등 **소스와 분석 결과 유형별**로 원본·제출 CID/SMILES/InChIKey·생물종·분석 파라미터·작업 ID·버전·수집 일자·SHA256을 대조한다.
3. 파일명에 화합물명이 포함되어 있다는 사실만으로 재사용을 허용하지 않는다. 검증이 끝난 자료에만 [검증된 자료 반영 및 재분석] 선택을 허용한다. 원본을 수정하지 않으며 해당 입력 해시가 같다면 같은 네트워크를 다시 계산하지 않는다.
4. 분석 누락·불완전 자료에는 [부족한 부분 보완], [새로 분석], [제외]와 검증 이유를 묻는 별도 승인 대화창을 표시한다. 사용자 승인 없는 새 제출과 불필요한 중복 분석을 금지한다.
5. 승인·원본 SHA·적용 브랜치·추가된 파일·결과 영향 범위를 기록한다. 새 자료가 기존 입력을 변경하면 세부 4가 확인 후 세부 3의 영향을 받은 결과만 무효화/재실행하고, 독립 QC 이전에는 논문용 최종이라고 표시하지 않는다.
6. 로컬 검토 UI는 `scripts/np_local_dashboard.py` (127.0.0.1:8765)로 제공하며 외부 네트워크에 노출하지 않는다. `scripts/np_multi_run_monitor.py`는 `NP_Runs/runs/*`를 감시하고 30분 간격 Windows 작업 스케줄러로 실행할 수 있다. 기타 Windows/계정에서는 별도 설치가 필요하다.
7. 자동 수집 구현 수준: 공식 완료 페이지가 확인된 PharmMapper의 이미 제출된 job 결과 HTML을 추가 보존할 수 있고, SEA는 *검증된* 결과 URL만 수집할 수 있다. 이 둘의 신규 작업 제출을 자동 완성하는 기능은 아직 연결되지 않았다. CAPTCHAs/계정 로그인·이메일 승인/지원되지 않는 API를 우회하지 않는다.
8. Cytoscape 작업자 `np_cytoscape_worker.py`는 manifest에 명시된 검증된 입력 SHA와 브랜치가 준비된 경우에만 cyREST로 PPI/MCODE·degree 결과를 실행하며 미변경 입력은 재실행하지 않는다. 최종 브랜치는 세부 4의 선행 QC 확인을 요구한다.

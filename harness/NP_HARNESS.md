# NP 전용 하네스 지침

> 이 문서는 NP 분석에만 적용한다. 범용 규칙은 상위 `HARNESS.md`와 `HARNESS_GUIDE.md`를 따른다.

## 적용 순서

1. `HARNESS.md`
2. `HARNESS_GUIDE.md`
3. 이 문서
4. `NP_ADAPTER.md`
5. `NP_WORKERS.md`
6. `NP_EXTERNAL_DATA.md`
7. `EXTERNAL_EVENT_CONTRACT.md`
8. `WORKER_CONTRACT.md`

프로젝트별 성분명·질환명·실험 marker·공동 target 수·최종 보고서 항목은 이 문서에 넣지 않는다. 실행 시작 시 프로젝트 폴더의 `<PROJECT_NAME>.md`를 추가로 읽고, 그 파일을 프로젝트 adapter 계약으로 사용한다.

## NP 전용 원칙

### 연구 단위와 성분 run의 구분

추출물·복합제·다성분 연구는 논문 단위의 **상위 project**와 성분별 **child run**을 분리한다. 각 성분은 독립 입력으로 검증·분석하되, 최종 논문 결과는 project 단위에서 통합한다. 총괄은 성분 run을 각각 완료했다고 해서 논문 목표를 완료로 선언하지 않는다. 모든 child run의 완료 gate가 통과되면 project integrator가 공통 허브, 성분별 허브, 통합 Figure/Methods 연결을 생성하고 project 상태를 갱신한다.

project integrator의 최소 산출물은 `project_manifest.json`, project별 통합 허브 표, 사람이 읽는 통합 요약, child run 목록·식별자·입력 hash·artifact 링크다. 공통 허브는 실제 frozen 네트워크의 topology 결과에서 계산하며 성분별 run의 허브를 임의로 합치거나 다른 프로젝트 자료를 재사용하지 않는다. child run이 하나라도 미완료·오류이면 project는 `WAITING_CHILD_RUNS`로 남기고, supervisor가 child 상태를 다시 확인한 뒤 자동 재시도·통합을 수행한다.

새 NP run은 실제 provider 호출 전에 가상 화합물·질환 시뮬레이션을 통과한다. SEA·PharmMapper 자료의 CID 불일치, 재업로드, 재맵핑, PPI·enrichment·그림 초안·도킹 후보까지의 handoff를 검증하고, 실패하면 실제 run을 시작하지 않는다.

NP 인터뷰와 기획이 끝나면 총괄은 최종 목표를 `입력·외부자료 검증 → 표적/PPI/enrichment → Cytoscape 네트워크·그림 → 도킹 후보 확정 → Methods/Results 초안 → 완료 패키지`로 제시하고 사용자에게 확인받는다. 확인된 목표와 각 단계의 완료 artifact를 run 계약에 기록한다.

NP에서 새로운 분석, 재분석, 외부 제출, 파일 교체, 후보 확정 또는 단계 변경 요청을 받으면 총괄은 먼저 자료 상태와 과학적 제약을 검토하고 자신의 의견·추천 방향·대안·예상 영향·완료 기준을 제시한 뒤 사용자 확인 후 실행한다. 단순 상태 확인, 파일 구조 검사, 재현 테스트와 오류 원인 조사는 바로 수행할 수 있다. 화합물 identity 불일치, 중복 제출, 원본 훼손 위험은 즉시 차단하고 보고한다.

NP 관련 질문이나 의견에는 현재 상태와 핵심 답을 먼저 짧고 명확하게 제시한다. 필요한 경우 다음 분석 단계나 추천 방향을 덧붙인다. 사용자가 이해가 안 되거나 상세 설명을 요청하면 입력 자료, 의존성, 검증 게이트를 쉬운 말과 순서로 설명한다. 총괄은 사용자 판단에 자동으로 동의하지 않고 근거·불확실성·자신의 추천을 구분해 보고한다.

시뮬레이션은 계획된 NP workflow와 같은 task·의존성을 가진 가상 run으로 시작한다. A·B 화합물과 질환 X의 정상 자료를 넣어 표적 수집부터 PPI·enrichment·통합·그림 초안·도킹 후보까지 도달한 뒤, SEA 또는 PharmMapper 단계에 잘못된 CID·구조·파일 형식·중복 자료를 가상 업로드한다. 외부자료 전담 worker가 원본을 보존하고 오류를 격리하며, 총괄이 `CORRECT_AND_RERUN`과 다음 수신 worker를 기록하고, 올바른 재업로드 후 해당 지점부터 자동 재개하는지 검증한다. 발견한 오류는 NP 회귀 테스트와 adapter 문서에 반영하고 같은 가상 run을 다시 통과시킨 후에만 실제 provider를 호출한다.

- 실제 NP run이 중간 오류로 최종 목표에 도달하지 못하면 수정 후 실패 지점부터 최종 목표까지의 축약 NP 시뮬레이션을 재실행한다. 외부자료 재맵핑, downstream handoff, Cytoscape, 도킹 후보, Figure artifact, Methods/Results artifact와 완료 보고서가 다시 생성되는지 확인한 뒤에만 실제 run을 checkpoint에서 재개한다.
- SEA·PharmMapper 원자료는 원본과 분석용을 분리하고 SHA-256과 source provenance를 기록한다.
- 외부 제출·로그인·CAPTCHA·raw 데이터 전송은 승인 게이트로 기록한다.
- UniProt·STRING 등 외부 API 실패는 `FAILED_RETRYABLE`로 제한 재시도하고, 한도 초과 시 `FAILED`와 총괄 경고를 남긴다.
- 매핑 미확인 표적은 임의로 제외하거나 확정하지 않는다.
- `DONE`은 필요한 산출물과 독립 QC가 확인된 경우에만 허용한다.
- 이 문서와 평가 보고서는 서로 다른 목적이다. 평가 보고서는 실행 지침으로 사용하지 않는다.


## NP supervisor

## Cytoscape 실행 방식

NP 계산·네트워크 생성·반복 실행은 Controller가 터미널·cyREST로 수행한다. 입력 네트워크, Cytoscape 버전, API 응답, 파라미터와 결과 manifest를 저장해 재현성과 자동 복구를 보장한다. Cytoscape GUI는 레이아웃·라벨·그림 품질의 최종 시각 검수에만 사용한다. GUI가 중단되어도 cyREST 경로에서 run을 재개할 수 있어야 하며, Controller와 GUI가 같은 Cytoscape 세션을 동시에 조작하지 않는다.

필수 NP task와 완료 manifest가 모두 검증되면 run 상태를 `COMPLETE`로 기록한다. 완료 후에는 `과학적 결과 검토 → 별도 도킹 workflow handoff`를 `next_action`으로 표시하며, 실제 도킹 계산은 별도 승인·검증 절차를 거친다.

NP run은 `run_controller.ps1`의 단기 cycle과 `run_supervisor.ps1`의 1분 감시를 함께 사용한다. supervisor는 실행 가능한 task가 있으면 controller를 자동 재호출하고, 실행할 수 없으면 외부 결과·선행 의존성·등록 worker 중 blocker를 기록한다. 외부 업로드 이벤트, 매핑 실패, downstream 무진척은 supervisor가 확인하고, 변환 가능한 파일은 재큐잉하며 보안·외부 전송 차단은 alert로 승격한다. 오류 해결·재수행·상태 변화가 5분 이상 없을 때만 사용자에게 보고한다.

## 후반부 목표 달성 gate

NP 분석의 최종 목표는 통합 target/PPI/enrichment 산출에 그치지 않는다. 동물·세포 실험 evidence를 기전 enrichment와 연결하고, Cytoscape degree·CytoHubba MCC·MCODE 결과를 확보한 뒤, 논문 Figure 패널·도킹 후보 추천·Methods/Results 초안을 생성하는 것까지 포함한다.

총괄은 다음 handoff를 자동 관리한다.

`enrichment_analysis → experimental_evidence_synthesis → mechanism_enrichment_synthesis → cytoscape_visualization → figure_draft → docking_candidate_selection → methods_results_draft → manuscript_review → completion_packager`

`figure_draft`는 통합 enrichment와 MCC/MCODE가 모두 검증되기 전에는 완료할 수 없다. `docking_candidate_selection`은 degree 단독 결과를 최종 후보로 승격하지 않으며, 실험 evidence·MCC·MCODE·pathway·구조 가용성의 교차검증을 요구한다. 각 handoff는 입력 hash, 산출물 경로, 수신 worker, 다음 action을 event log에 기록한다.

도킹 후보를 최종 추천하기 전에는 화합물별 공동 target 매칭, 문헌·기전 감사, PDB/결합 포켓 적합성 감사를 병렬로 실행한다. 동물·세포 실험 자료가 연구 설계상 아직 없을 수 있으므로 실험 근거는 선택적 가점이며, 없으면 `미확인`으로 표시한다. 문헌·구조 근거가 부족한 표적은 순위표에 보류 사유를 남기고 최종 후보에서 제외한다. 후보 순위에는 MCC·MCODE·degree 숫자뿐 아니라 화합물 매칭, 기전, 문헌, 구조 적합성에 대한 짧은 사유를 포함한다.

## NP review package contract

After the raw-data validation gate, create the collaborator review package under the NP project root. Keep the sequence 01_raw -> 02_calculated -> 03_STRING -> 04_Cytoscape -> 05_figures_reports. 01_raw contains verified compound/disease inputs, PharmMapper and SEA source files, PubChem structures, compound-protein and disease-gene tables. 02_calculated contains stable-ID normalization, mapping QC and overlap. 03_STRING contains STRING PPI and GO BP/CC/MF/KEGG outputs. 04_Cytoscape contains network inputs, degree, MCC, MCODE and visual-QC artifacts. 05_figures_reports contains candidate rationale, figures, Methods/Results and the final report. The README must list every file and record input -> analysis -> output filename/extension. Invalid identity-mismatch files and superseded compounds are excluded.

The NP review-package README must use a table for the inventory and data lineage. Required columns are folder, file, input/source, NP or STRING/Cytoscape operation, output extension, and manuscript/review use. The table must distinguish raw files from calculated and provider-generated files.

NP completion packaging must include reproducibility metadata: Python/runtime, Cytoscape and app versions, STRING release and thresholds, PharmMapper/SEA job dates and IDs, parameters, hashes, and script revision. A package may be collaborator-review complete while still marked REVIEW_ONLY; Methods/Results and publication-ready status require the metadata gate to pass.

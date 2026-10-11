# CMPE–UC NP 하네스 실데이터 수용 시뮬레이션 보고서

## 결론

범용 NP 분석 하네스 기준으로 CMPE의 두 화합물과 UC 관련 실제 산출물 복사본을 사용한 가상 프로젝트를 실행했다. 원래 CMPE 프로젝트는 수정하지 않았다. 오류 입력 검출·격리·재업로드·재라우팅부터 STRING/PPI, Cytoscape/cyREST, MCODE, MCC, 후보 추천, 그림 생성까지 통과했다.

## 오류 이벤트 및 복구

- 잘못된 PharmMapper 파일 1개와 잘못된 SEA 파일 1개를 의도적으로 주입했다.
- 두 파일 모두 `IDENTITY_MISMATCH`로 격리했다.
- 올바른 자료를 재업로드하여 source archive로 이동하고 수신 worker handoff를 기록했다.
- child run 이벤트 로그에 수신·거부·격리·재업로드·라우팅을 남겼다.

## 계산 및 산출물

- STRING/PPI: 374 nodes, 4,205 edges
- STRING enrichment: 4,378 rows
- Cytoscape/cyREST import: PASS
- MCODE: PASS, 10 clusters
- MCC: 374 rows
- 후보 추천: PASS, 4개 후보

## 도킹 후보 추천

후보는 단순 degree 순위가 아니라 공동 표적 여부, MCC, 문헌·기전 근거, 구조 적합성을 통합해 순위를 냈다. 두 화합물 모두에 매칭되는 공동 표적만 사용했다.

1. **AKT1** — MCC·degree 최상위, UC/PI3K–AKT 기전 근거, PDB 3O96·6CCY
2. **MMP9** — 염증·ECM 관련성, PDB 1GKC·8K5W. 촉매영역과 zinc-site 조건 확인 필요
3. **PPARG** — 염증·대장염 기전 근거, PDB 6C1I·7AWC
4. **JAK2** — JAK/STAT 기전 및 kinase 구조. 문헌 근거가 상대적으로 약해 4순위

후보 검증 파일은 `candidate_validation/`에 보존했다. 이 단계는 도킹 입력 후보 확정이며, AutoDock/Vina 실제 도킹은 별도 하네스에서 수행한다.

## 생성된 그림

계산 결과를 변경하지 않고 실제 산출물에서 그림을 생성했다.

- `figures/Figure_A_MCC_top20.svg`: MCC 상위 20개 표적
- `figures/Figure_B_GO_KEGG_top7.svg`: Process·Component·Function·KEGG별 FDR 상위 7개
- `figures/Figure_C_artifact_counts.svg`: 계산 산출물 규모
- `figures/figure_manifest.json`: 입력자료와 그림 목록

그림의 값은 `mcc_rank.csv`, `cmpe_union_string_enrichment.tsv`, `simulation_summary.json`에서 직접 읽었다. 따라서 그림 생성이 계산값을 변경하지 않는다.

## GUI와 터미널 검증 범위

터미널에서 Cytoscape/cyREST를 호출해 실제 네트워크 import와 MCODE를 수행했다. 계산 경로는 검증됐다. Cytoscape GUI의 최종 노드 배치·라벨·색상·가독성은 별도 화면 검수 대상이다.

## 판정

`PASS_WITH_GUI_VISUAL_REVIEW_PENDING`

자료 검수, 오류 격리, 재라우팅, STRING/PPI, Cytoscape, MCODE, MCC, 후보 추천 및 그림 생성까지 통과했다. GUI 시각 검수와 실제 AutoDock/Vina 계산은 별도 단계다.

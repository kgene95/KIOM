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
| `gmail_job_monitor` | 수신 상태·공식 링크 metadata | planned |

제출 worker는 최초 승인과 공식 경로를 확인한다. CAPTCHA·로그인·이메일 입력이 필요하면 `WAITING_USER`로 전환한다. Gmail worker는 메일 본문과 주소를 저장하지 않고 job ID 매칭과 공식 결과 링크만 기록한다.

## Agent 3: 계산·통합 분석

| worker | 산출물 | 현재 상태 |
|---|---|---|
| `normalize_targets` | stable-ID/species QC | planned |
| `overlap_analysis` | overlap table | planned |
| `ppi_analysis` | PPI·topology 결과 | planned |
| `enrichment_analysis` | GO/KEGG/Reactome 결과 | planned |
| `integration_analysis` | 통합 manifest | planned |

## Agent 4·5: 품질과 결과

| worker | 완료 조건 | 현재 상태 |
|---|---|---|
| `independent_qc` | `PASS` 또는 수정 요청 | planned |
| `manuscript_review` | 검토 manifest | planned |
| `completion_packager` | 결과·manifest·raw 패키지 | planned |

## 실행 규칙

1. 독립 resource는 병렬 실행한다.
2. 같은 provider·브라우저·출력 파일은 lock으로 직렬화한다.
3. 모든 worker는 run 폴더, task ID, 입력 hash를 받는다.
4. worker는 출력 manifest를 만들고, 최종 `DONE`은 verifier가 선언한다.
5. 오류는 `WAITING_USER`, `WAITING_EXTERNAL`, `CORRECT_AND_RERUN`, `BUDGET_STOP` 중 하나로 기록한다.

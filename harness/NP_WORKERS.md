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

제출 worker는 최초 승인과 공식 경로를 확인한다. CAPTCHA는 `CAPTCHA_CONFIRMATION_REQUIRED`를 거쳐 Agent 2가 직접 수행하고, 로그인·이메일 입력 등 별도 정보가 필요한 경우에만 해당 상태를 기록한다. Gmail worker는 메일 본문과 주소를 저장하지 않고 job ID 매칭과 공식 결과 링크만 기록한다.

### 외부 제출 상태 규칙

이전 실행에서 제출·대기·다운로드가 완료된 사실은 새 run의 자동 완료 근거가 아니다. 새 run은 기존 자료 재사용 승인 없이는 과거 결과를 사용하지 않는다.

- SEA: SMILES 입력 후 CAPTCHA가 표시되면 `CAPTCHA_CONFIRMATION_REQUIRED`; 행동 직전 확인 후 Agent 2가 사람 확인·제출·job ID 확인을 재개한다.
- PharmMapper: 이메일은 현재 세션에서만 사용하고 파일·로그·manifest에 저장하지 않는다. 응답에 공식 job ID가 없거나 공식 완료 메일이 없으면 `SUBMISSION_NOT_CONFIRMED`로 중지한다. 이 상태에서 자동 재전송하지 않는다.
- 두 provider 모두 raw 결과와 SHA-256, CID/구조 identity 검증 전에는 `DONE`이나 downstream unblock을 선언하지 않는다.

제출 책임은 Agent 2와 총괄 Controller에 있다. 정상적인 입력·CAPTCHA 확인·제출·작업 ID 확인·결과 회수는 에이전트가 직접 수행하며 사용자는 진행 중 매 단계마다 클릭하거나 명령을 입력하지 않는다. CAPTCHA 클릭 직전에는 `CAPTCHA_CONFIRMATION_REQUIRED`를 기록하고 행동 확인을 받은 뒤 즉시 같은 worker를 재개한다.

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

### 제출 실패 시 사용자 안내

제출 실패가 발생하면 총괄은 사용자에게 같은 질문을 반복하지 않고 한 번에 다음 정보를 제공한다.

- 공식 제출 사이트 주소
- 화합물별 입력 파일의 절대 폴더 주소와 파일명
- 복사·붙여넣기 가능한 job description
- 사이트에서 수행할 단계(파일 선택, 이메일 입력, 설정, Submit)
- 실패 시 캡처할 화면과 확인할 오류(job ID, 메일, 비활성화 버튼, CAPTCHA)

사용자가 제출한 뒤 job ID를 전달하면 worker는 ID·provider·compound identity를 대조하고 ledger를 갱신한다. ID가 없으면 이전 ID나 historical evidence를 현재 run에 연결하지 않는다.

# 이벤트 기반 총괄·세부 에이전트 실행 규칙

작업 큐의 역할 이름은 상태표시만을 뜻하지 않는다. 총괄은 새 체크포인트를 감지하면 아래 의존 작업을 즉시 실행하거나, 외부 서비스·과학적 게이트가 남은 경우에는 그 정확한 재개 조건을 기록한다.

| 이벤트 | 총괄의 즉시 조치 | 후속 담당 | 완료 기준 |
|---|---|---|---|
| 구조 QC와 CID/구조 SHA 확보 | SEA·PharmMapper 제출 준비와 질환 표적 수집을 병렬 시작 | 세부 1, 세부 2 | `structure_manifest`, `handoff_to_agent2` 기록 |
| SEA/PharmMapper 제출 응답·job ID 확보 | 공식 상태를 확인하고 결과 원본 회수 작업을 등록 | 세부 2 | job ID·입력 SHA·결과 URL 기록 |
| Gmail에서 해당 provider와 정확한 job ID 결과 수신 | 메일 원문/주소를 저장하지 않고 공식 결과를 회수, 원본 SHA와 manifest 작성 | 세부 2 | raw+SHA+출처+수집시각 |
| SEA/PharmMapper 원본 확보 | 종·UniProt·HGNC QC를 실행하고 실패 행을 격리 | 세부 1, 세부 4 | QC 표·원본 API 응답·QC manifest |
| UC 질환 원본·고정 규칙 확보 | 질환 집합 QC를 실행하고 primary/sensitivity 분기를 고정 | 세부 1, 세부 4 | frozen disease manifest |
| 화합물·질환 양쪽 QC 통과 | STRING 입력을 만들고 실제 PPI 원본을 회수 | 세부 3 | STRING mapping/edge 원본+SHA |
| 검증된 PPI 확보 | Cytoscape/MCODE·hub·GO/KEGG를 실행 | 세부 3 | 실행 로그·원본/파생 파일·버전 |
| 새 입력 또는 QC 수정 | 하류 PPI·Cytoscape·enrichment를 무효화하고 고정 입력으로 재실행 | 총괄, 세부 4 | change event와 새 결과 |

## 대기와 재시도

- Gmail 감시는 실제 설치·확인된 heartbeat/connector에서만 수행한다. 상태가 변하지 않으면 사용자에게 통지하지 않는다.
- 네트워크·일시 서비스 오류는 최대 3회 제한 재시도하고, 그 뒤 두 가지 문서화된 대안을 시도한다.
- CAPTCHA는 `CAPTCHA_CONFIRMATION_REQUIRED`로 기록하고 Agent 2가 행동 직전 확인 후 직접 수행한다. 로그인, 이용약관 동의, 사용자가 제공해야 하는 이메일처럼 별도 정보·권한이 필요한 행동만 `WAITING_USER`로 둔다.
- 보조 자료(예: PharmMapper) 지연은 이미 검증된 primary 입력의 STRING/PPI 진행을 막지 않는다. 단, 보조 자료 부재를 결과와 Methods에 명시한다.
- 총괄은 각 이벤트 때 `work_queue.json`, `execution_state.json`, `job_ledger.json`을 함께 갱신한다. 단순 상태 점검만 하고 실행 가능한 후속 작업을 남겨 두지 않는다.

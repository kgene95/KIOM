# Initial access and notification approval

At project intake, show one auditable approval panel. Store only scope, timestamp, and yes/no choices in `initial_access_approval.json` or the project manifest. Never store an email address, API key, password, token, session cookie, or Gmail message content.

## Approval registry

| Capability | Initial panel option | Operational boundary |
|---|---|---|
| Public read-only retrieval | TTD, Open Targets, PubChem, MyGene, STRING, g:Profiler | Verify a real dataset response and archive it; an HTML shell is not raw data. |
| Interactive source access | SwissTargetPrediction, SEA, PharmMapper | 최초 승인 뒤 Agent 2가 검증된 공식 경로를 직접 실행하고 job ID·URL·입력 SHA를 기록한다. SEA는 SMILES 입력, Altcha 일반 확인, Submit을 브라우저 자동화로 수행하며 CAPTCHA를 우회하지 않는다. 일시 네트워크 오류는 최대 3회 재시도한다. |
| PharmMapper email | Registration and completion notification if required | 사용자는 대시보드 세션에 주소를 한 번 입력한다. Agent 2가 그 주소를 PharmMapper 공식 제출 요청에 직접 전달하므로 공급자 사이트에서 다시 입력하게 하지 않는다. 주소는 manifest·log·raw·report에 저장하지 않는다. |
| Gmail completion check | Provider and job ID matching only | Search only for the named provider and exact job ID after a user-authorized submission. Preserve provider result, never raw email content. |
| OMIM | Official API if a user supplies a valid key | Do not request, store, print, or infer an API key. No key means not retrieved or user-export route. |
| GeneCards or other login/CAPTCHA/terms site | Record planned source only | Stop for the exact login, CAPTCHA, terms, or permission gate. An initial panel cannot accept these on the user's behalf. |

## State model

Record every source separately as planned, retrieved, not retrieved, unavailable, pending external submission, or failed, with exact reason. An initial approval is authorization to attempt the scoped action; it never changes source status to retrieved and never claims the service or adapter is implemented.

## Agent routing

- Agent 0 freezes the access plan and verifies that every baseline source has a ledger row.
- Agent 1 collects public disease-source raw files and extraction records.
- Agent 2는 세션 전용 PharmMapper 이메일 입력란을 제공한 뒤 사용자가 입력하면 공식 PharmMapper 제출을 자동 실행한다. SEA는 검증된 공식 브라우저 흐름(SMILES → Altcha 확인 → Submit)을 실행하고 task ID·URL·입력 SHA를 기록한다. 이메일 주소가 아니라 이메일 제공 여부·job ID·provider·result provenance만 기록한다.
- Agent 4 verifies archive hash, source-native release, species and stable identifier mapping before integration.
- Agent 3 integrates only QC-passed branch tables.
- Agent 5 writes only from the frozen manifest and never exposes credentials or email content.

## Codex discovery

Codex does not need a visible web-agent category to use this design. Skill discovery supplies SKILL.md; the skill routes to this reference and agents/openai.yaml carries a concise UI/default-prompt summary. These are instructions and metadata, not an always-running agent or automatic connector.

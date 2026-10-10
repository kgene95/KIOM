# Skill Stack Audit

## 목차

1. 목적
2. 감사 대상
3. 판정 기준
4. NP 적용 결과
5. 갱신 절차

## 목적

같은 일을 여러 Skill, plugin, script가 중복 수행하거나 서로 충돌해 에이전트가 잘못된 호출을 하는 문제를 먼저 찾는다. 스킬 설명만 보고 설치 완료로 간주하지 않으며, 실제 경로·입력·출력·검증 테스트를 확인한다.

## 감사 대상

- `skills/run-network-pharmacology/`: 과학 분석 규칙
- `skills/research-project-memory/`: 프로젝트 상태와 cross-environment handoff
- `harness/`: 실행·상태·예산·게이트
- `agents/AGENTS.md`: 역할과 파일 계약
- 기존 `scripts/`: 결정적 계산과 상태 감지
- 연결된 plugin/connector: 실제 설치·권한·호출 가능 여부

## 판정 기준

각 Skill은 `purpose`, `entrypoint`, `inputs`, `outputs`, `side_effects`, `verification`, `owner`, `overlap`을 기록한다. 다음 중 하나로 판정한다.

- `ACTIVE`: 현재 run에서 검증된 경로
- `AVAILABLE_UNVERIFIED`: 경로는 있으나 실제 호출 검증 전
- `REFERENCE_ONLY`: 설계 참고용
- `DUPLICATE`: 다른 Skill과 책임 중복
- `BLOCKED`: 의존성·권한·입력 부족

같은 책임의 Skill을 두 개 동시에 호출하지 않는다. 하나는 실행 소유자가 되고 나머지는 참고 또는 폐기 대상으로 기록한다.

## NP 적용 결과

현재 NP의 과학 소유자는 `run-network-pharmacology`이고, 상태·handoff 소유자는 `research-project-memory`와 `harness`다. `np_agent_queue.py`와 `np_multi_run_monitor.py`는 결정적 보조 도구이며 총괄을 대신하지 않는다. OpenAI Agents SDK, Awesome Copilot, Anthropic Skills, Superpowers는 현재 NP의 실행 소유자가 아니라 설계 참고 또는 선택적 adapter 후보로 취급한다.

## 갱신 절차

새 Skill/plugin을 추가할 때 먼저 이 감사 파일과 `worker_registry.json`을 갱신한다. 그 다음 dry-run, 실패·재시작 테스트, provenance 검사를 통과해야 ACTIVE로 승격한다. 기존 결과를 바꾸는 Skill 교체는 새 branch와 결정 기록을 만든다.

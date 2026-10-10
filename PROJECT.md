# KIOM project

## 목적

KIOM 연구와 소프트웨어 작업을 재현 가능하고 검증 가능한 방식으로 수행한다. 범용 하네스는 작업 lifecycle을 관리하고, NP·docking·MD·문헌·논문·웹앱은 분야별 adapter로 연결한다.

## 범위

- 연구 분석과 원본 provenance
- Skill·agent·connector 운영
- 테스트·QC·checkpoint·handoff
- Git/GitHub branch·review·merge
- Codex·ChatGPT·다른 실행 환경 간 재개

## 기준 문서

- `HARNESS_GUIDE.md`: 범용 하네스
- `AGENT_CONTRACT.md`: 에이전트 역할
- `CODEX/ChatGPT.md`: Codex/ChatGPT 실행 규칙
- `PROJECT_STATE.md`: 현재 상태와 다음 행동
- `00_shared/MEMORY/DECISIONS.md`: 설계 결정
- `adapters/`: 분야별 연결

## 저장소 경계

GitHub/KIOM에는 문서·코드·스키마·테스트·manifest·checkpoint를 저장한다. OneDrive와 지정된 연구 저장소에는 대용량 raw와 binary를 보관하고, GitHub에는 경로와 SHA를 기록한다.

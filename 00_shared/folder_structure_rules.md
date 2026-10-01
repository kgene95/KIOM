# 폴더 구조 규칙

- `00_shared/`: 공통 규칙·서식·DB 문서·skill 사용법만 저장합니다. 프로젝트별 화합물·유전자 데이터 금지.
- `01_CMPE/`, `02_MGC/`: 프로젝트 자료를 분리합니다.
- `01_NP_GPT/`: GPT 보조 분석. MGC는 5개 화합물 분석 전용입니다.
- `02_NP_Direct/`: 연구자 직접 분석. MGC는 연구자가 직접 수행한 멸가치 NP 전용입니다.
- GPT와 Direct의 raw, processed, compound_information, gene_lists, ppi, enrichment를 혼합하지 않습니다.
- `metadata/`: 분석 조건, 출처 레지스트리, 분석 분기 레지스트리, 파일 계보.
- `raw/`: 원자료. 수집 이후 수정하지 않고 정제본은 processed에 저장합니다.
- `processed/`: 정제·변환 데이터. `compound_information/`: 화합물 정보. `gene_lists/`: 유전자 목록.
- `ppi/`: 상호작용 네트워크. `enrichment/`: 기능·경로 분석.
- GPT의 `checkpoints/`: 프롬프트·응답·단계별 검토 기록.
- Direct의 `cytoscape/`: Cytoscape 세션·내보내기 자료.
- 분석 `figures/`, `reports/`: 해당 분석의 그림·보고서.
- `03_Manuscript/`: drafts, figures, tables, references, supplementary. 인용 분석의 provenance를 유지합니다.
- `99_archive/CMPE/`, `99_archive/MGC/`: 원래 분석 유형·경로·이관 이유·일자를 유지해 보관합니다. 서로 다른 분석 자료를 한 묶음으로 합치지 않습니다.
- 빈 폴더는 .gitkeep로 유지할 수 있습니다. 실제 파일이 들어오면 불필요한 .gitkeep는 제거할 수 있습니다.

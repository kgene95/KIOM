# KIOM

CMPE와 MGC 네트워크 약리학(NP) 분석 및 원고 자료를 관리합니다.
현재는 구조와 템플릿만 초기화한 상태이며, CMPE Library 실제 데이터는 업로드하지 않았습니다.

| 경로 | 분석 유형 / 용도 |
| --- | --- |
| `00_shared/` | 공통 규칙, 템플릿, DB 문서, skill 사용법 |
| `01_CMPE/01_NP_GPT/` | CMPE GPT 보조 NP 분석 |
| `01_CMPE/02_NP_Direct/` | CMPE 연구자 직접 NP 분석 |
| `01_CMPE/03_Manuscript/` | CMPE 원고 |
| `02_MGC/01_NP_GPT/` | MGC 5개 화합물 GPT 보조 NP 분석 |
| `02_MGC/02_NP_Direct/` | 연구자가 직접 수행한 멸가치 NP 분석 |
| `02_MGC/03_Manuscript/` | MGC 원고 |
| `99_archive/CMPE/`, `99_archive/MGC/` | 프로젝트별 보관 자료 |

## Provenance와 데이터 분리
- 모든 분석 입력·결과는 해당 분석의 `metadata/`에서 출처, 생성 주체, 도구/모델, 매개변수, 부모 파일을 기록합니다.
- CMPE와 MGC 데이터를 혼합하지 않습니다. 각 프로젝트의 GPT와 Direct 원자료·중간 결과도 혼합하지 않습니다.
- `00_shared/`에 프로젝트별 화합물·유전자 데이터를 두지 않습니다.
- 원고에서 결과를 비교·인용할 때 프로젝트/분석 유형/실행 ID/원본 경로를 명시하고, 분석 결과를 하나의 데이터셋으로 합치지 않습니다.
- 빈 폴더는 `.gitkeep`로 유지합니다. 초기 metadata의 빈 값과 헤더만 있는 CSV는 실제 분석 완료를 의미하지 않습니다.

공통 안내: [폴더 규칙](00_shared/folder_structure_rules.md), [파일명 규칙](00_shared/file_naming_rules.md), [출처 규칙](00_shared/provenance_rules.md).

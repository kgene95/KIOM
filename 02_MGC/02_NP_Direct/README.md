# MGC 02_NP_Direct

## 분석 유형
연구자가 직접 수행한 멸가치 NP 분석.
현재 상태: initialized. 실제 데이터·분석 결과 미등록.

## Provenance
- [analysis_metadata.yaml](metadata/analysis_metadata.yaml): 범위·실행 조건·도구·검토 상태.
- [source_registry.csv](metadata/source_registry.csv): 원자료 및 DB 출처.
- [branch_registry.csv](metadata/branch_registry.csv): 분석 분기와 선택적 Git 참조.
- [file_manifest.csv](metadata/file_manifest.csv): 입력·출력·부모 파일·해시 계보.
수행 연구자·도구·버전·설정·작업 기록을 보존합니다. Cytoscape 자료는 cytoscape에 둡니다.
CSV는 현재 헤더만 있으며 YAML의 null/빈 목록은 미입력 값입니다.

## 데이터 혼합 금지
이 폴더의 MGC/Direct 입력·중간 결과를 다른 프로젝트 또는 다른 분석 유형의 자료와 혼합하지 않습니다.
프로젝트별 화합물·유전자 자료를 00_shared에 저장하지 않습니다.

## 폴더 안내
raw(원자료), processed(정제본), compound_information(화합물 정보),
gene_lists(유전자 목록), ppi(네트워크), enrichment(기능·경로),
cytoscape(세션·내보내기),
figures(그림), reports(방법·결과 보고서).

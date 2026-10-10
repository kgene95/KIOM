# 공개 질환 표적 수집과 누락 감사
공식 원본 확보와 질환 표적 추출, stable-ID QC, 분석 통합은 별도 완료 상태로 기록한다.

1. 먼저 지정 프로젝트의 원본, source_attempts, manifest, 실행기록을 검사한다. 과거 시도 기록이 없으면 '시도 증거 없음'으로 기록하며 접속 실패, 인증 필요 또는 무결과라고 추정하지 않는다.
2. TTD는 공식 다운로드 페이지에서 실제로 확인한 공개 링크를 사용한다. HTTP 200 HTML/SPA 화면만 저장한 경우 데이터 상태는 not retrieved다. 응답 내용과 원본 형식을 검증한 뒤에만 retrieved로 기록한다. 로그인/키가 필요하다고 단정하지 않는다. 접근 제한/약관을 우회하지 않는다.
3. source_attempts에는 source, subject_type/id, exact_query, URL, final_URL, access_utc/KST, HTTP, retrieval_status, failure_reason, raw_path, SHA256, bytes, source_native_release, extraction_status, mapping_qc, inclusion_status를 기록한다. 과거와 신규 시도는 다른 행에 남긴다.
4. 공개 원본은 새로운 실행 폴더에 독점 생성하고 기존 원본은 덮어쓰지 않는다. HTML 원본과 실제 데이터 원본을 구별한다. 날짜는 실제 접근일, 데이터 버전은 파일 헤더에서 기록한다. 홈페이지 2026 인용이 파일 2024 버전을 바꾸지 않는다.
5. UC는 ulcerative colitis 및 공식 질환 ID(해당 파일에 있으면 ICD-11 DD71)를 명시적으로 대조한다. 원본 행 번호와 TTD ID, native indication/status/score를 보존한다. 일반 colitis/Crohn's/IBD를 자동 합산하지 않는다.
6. TTD indication 매핑과 genetic/transcriptomic evidence는 별도 증거 분기로 추출한다. 원본 행 수, 고유 TTD ID 수, HGNC/UniProt QC 후 유전자 수를 구별한다. 복합 표적/여러 gene/entry-name/비인간 및 미매핑은 별도 QC로 남긴다.
7. 원본 확보 또는 UC 추출만으로 primary/manuscript-ready 상태로 승격하지 않는다. OpenTargets 등 다른 출처, CMPE 등 다른 프로젝트, 기존 PPI/허브/경로 결과와 혼동하지 않는다. 새 자료가 기존 gene universe를 바꾸면 먼저 영향평가와 mapping QC를 수행하고 승인 범위 내에서 재계산한다.
8. 총괄 0은 모든 필수 출처 행을 점검한다. 자료 담당 1은 공식 경로/원본/추출을, QC 담당 4는 SHA/질환/버전/종/ID를 검증한다. 분석 담당 3은 검증된 분기만 통합하며 원고 담당 5는 실제 frozen manifest만 인용한다. 에이전트 지침 추가는 실행기 자동수집 구현이나 상시 에이전트 실행 완료를 뜻하지 않는다.
9. 이미 사용자가 현재 수집과 지침 갱신을 승인한 범위는 다시 묻지 않고 진행한다. 과거 원본 재사용/새 결과 통합에 관한 별도 승인이 필요한 경우 현재 명시 지시로 충족됐는지 먼저 판단한다.

# NP 외부자료 수신·변환 규칙

## PharmMapper·SEA 파일

- 사용자가 다운로드한 원본 CSV/TSV/ZIP은 `source_archive/<provider>/`에 원본 그대로 저장한다.
- 원본 파일명과 SHA-256을 `source_manifest.json`에 기록한다.
- provider별 parser가 열 이름과 행 수를 확인한 뒤 NP 표준 `compound_targets.csv`로 변환한다.
- 변환 시 `compound_cid`, `target_id`, `source`, `source_score`, `raw_file`, `raw_sha256`를 보존한다.
- 확인되지 않은 ID는 제거하지 않고 `unmapped_targets.csv`와 `normalized_targets.json`의 `unmapped`에 기록한다.
- CID가 run의 CID와 다르면 `IDENTITY_MISMATCH`로 차단한다.
- 변환 성공 후 `sea_collect` 또는 `pharmmapper_collect`를 `DONE_RAW_UNVERIFIED`로 갱신하고 `initial_ppi`를 자동 재호출한다.

## 자동 실행이 불가능한 경우

CAPTCHA·로그인·외부 전송 정책 때문에 사용자가 직접 다운로드한 경우에도 사용자는 원본 파일만 제공하면 된다. 총괄은 파일을 검사하고, 이름·열·CID·provider를 확인해 적절한 위치와 표준 형식으로 변환한다. 같은 형식 오류를 사용자에게 반복해서 묻지 않는다.

## 재개 규칙

새 PharmMapper 자료가 들어오면 기존 실패 결과를 재사용하지 않고 새 SHA와 새 이벤트로 기록한다. mapping worker가 재실행되고, 성공한 행으로 가능한 분석은 계속한다. 미확인 행만 별도 QC gate로 남긴다.

## 외부자료 검수 worker와 담당 worker 알림

PharmMapper·SEA·Gmail 파일은 먼저 `external_data_intake`가 원본 보존, SHA-256, provider, 열 구조, CID를 검수한다. 검수 성공 시 `worker_notifications.jsonl`로 `pharmmapper_collect` 또는 `sea_collect`에 전달하고, 해당 worker는 표준 `compound_targets.csv` 변환·stable-ID 매핑을 다시 수행한다. 미매핑 표적은 삭제하지 않고 별도 QC 파일에 남긴다. CID 불일치나 손상은 해당 provider branch만 재수신·재변환하며 독립 branch는 계속한다.

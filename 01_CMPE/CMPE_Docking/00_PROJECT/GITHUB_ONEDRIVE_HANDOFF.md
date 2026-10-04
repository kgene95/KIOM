# GitHub–OneDrive handoff instructions

이 문서는 다른 ChatGPT 일반 채팅에서 현재 CMPE 도킹 재검증 프로젝트를 GitHub와 OneDrive에 반영할 때 사용하는 작업 지침이다. 과학적 판단과 문서 내용은 이미 이 프로젝트에서 정리했으므로, 새 채팅에서는 분석을 처음부터 다시 실행하지 않는다.

## 기준 폴더

- 로컬 프로젝트: `CMPE_Docking_Revalidation`
- OneDrive 공유 폴더: `CMPE_Docking`
- 우선 읽을 파일: `00_PROJECT/README_AGENT.md`, `00_PROJECT/CURRENT_STATUS.md`, `docking_manifest.json`, `docking_checkpoint.md`

## 저장소별 역할

GitHub에는 버전 관리가 필요한 텍스트·코드 파일을 둔다.

- `README_AGENT.md`, `CURRENT_STATUS.md`, `CHANGELOG.md`
- `docking_checkpoint.md`, `docking_manifest.json`, `file_inventory.csv`
- 재현 가능한 Python/PowerShell 스크립트
- 필요한 경우 figure 생성 코드와 작은 검토용 표

OneDrive에는 계산 자료와 공유용 산출물을 둔다.

- 원본 PDB/PDBQT/SDF 및 준비된 구조
- Vina config, 로그, pose 파일, 결과 CSV
- PDF, figure PNG/TIFF, 최종 manuscript handoff 자료
- 필요한 경우 GitHub commit ID와 연결된 release ZIP

도킹 스킬 ZIP, 복구 폴더, 중복 ZIP, 임시 캐시를 프로젝트 자료로 다시 업로드하지 않는다.

## 현재 과학적 상태

- Fig. 3(B) 재검증의 주 receptor는 human IKKβ `4KIK` chain B이다.
- native KSA redocking은 symmetry-aware heavy-atom RMSD `0.3808 Å`로 PASS했다.
- 주 ligand는 vitexin-4″-O-glucoside이다.
- naringenin은 비교용 ligand이다.
- 4KIK 결과는 Vina 계산까지 완료되었지만 interaction fingerprint와 일부 pose-QC가 미완료이므로 전체 job은 `LIMITED`로 유지한다.
- COX-2 `5IKR`은 COH cobalt metalloporphyrin 처리 근거가 정리될 때까지 `BLOCKED`이다.
- docking 결과를 실제 결합, target engagement, inhibition의 증거라고 표현하지 않는다.

## 반영 절차

1. 로컬 파일과 OneDrive 파일 목록을 먼저 읽고, 파일명·크기·수정일·SHA-256을 비교한다.
2. 기존 문서와 결과를 자동으로 덮어쓰지 말고 차이를 기록한다.
3. Markdown·manifest·CSV·스크립트는 GitHub 변경 대상으로 분류한다.
4. raw data·로그·pose·PDF·figure는 OneDrive 보관 대상으로 분류한다.
5. `file_inventory.csv`를 갱신하고 변경 내용을 `CHANGELOG.md`에 추가한다.
6. GitHub push나 OneDrive 파일 이동·삭제가 필요하면 실제 대상과 변경 내용을 먼저 요약한다.
7. 최종 보고서에는 동기화된 파일, 충돌, 누락, 보류 항목을 분리해서 적는다.

## 일반 채팅에 붙여 넣을 요청문

현재 폴더의 `00_PROJECT/README_AGENT.md`, `CURRENT_STATUS.md`, `GITHUB_ONEDRIVE_HANDOFF.md`, `docking_manifest.json`, `docking_checkpoint.md`를 먼저 읽어줘. 도킹 분석을 다시 실행하지 말고, 이 문서에 기록된 상태를 기준으로 로컬 프로젝트와 GitHub·OneDrive의 파일 구조를 비교해줘. Markdown·manifest·CSV·스크립트는 GitHub 대상, raw 구조·로그·pose·PDF·figure는 OneDrive 대상으로 분류하고, 파일명·크기·수정일·SHA-256 차이를 표로 정리해줘. 복구 폴더·중복 ZIP·스킬 ZIP은 다시 만들거나 업로드하지 말아줘. 변경 전에는 대상과 이유를 요약하고, push·이동·삭제는 별도 확인 후 실행해줘. 최종적으로 동기화 상태, 충돌, 누락, 다음 작업을 보고해줘.

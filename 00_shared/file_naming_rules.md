# 파일명 규칙

- 분석 파일은 `<project>_<analysis>_<run_id>_<stage>_<description>_v<NN>.<ext>`를 사용합니다.
- project는 `CMPE` 또는 `MGC`, analysis는 `GPT` 또는 `Direct`입니다.
- run_id는 분석 폴더 안에서 고유한 `YYYYMMDD_NN` 형식입니다. 날짜 기준은 Asia/Seoul입니다.
- 공백과 경로 구분자를 피하고 설명은 영문·숫자·밑줄로 작성합니다.
- 기존 고정 파일명 `README.md`, metadata 4종, 공통 템플릿은 이 규칙의 예외입니다.
- 원본 파일명은 source_registry의 original_filename에 보존합니다. 보관용 이름 변경 시 해시와 원본명을 기록합니다.
- 덮어쓰지 말고 버전 또는 실행 ID를 갱신합니다. 이름이 같아도 다른 분석 폴더 사이에 파일을 이동·혼합하지 않습니다.

# Approval policy

자동 진행: 파일 읽기, 결정적 계산, 테스트, 로그, checkpoint, 안전한 새 파일 생성.

승인 필요: 기존 자료 재사용, 외부 전송, Gmail·SEA·PharmMapper 실행, 로그인·CAPTCHA, 삭제·덮어쓰기, GitHub push, 배포, 논문 최종화, 최종 과학 결론.

승인은 `approval_id`, 대상 task, 범위, 시각, 사용자 결정, 만료 조건을 남긴다. 이미 승인된 동일 task·동일 입력은 다시 묻지 않는다.

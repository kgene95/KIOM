"""오류 분류와 bounded retry 정책."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RecoveryDecision:
    status: str
    retryable: bool
    next_action: str


def classify_error(error: BaseException | str, attempts: int, max_attempts: int = 3) -> RecoveryDecision:
    text = str(error).lower()
    if any(token in text for token in ("approval", "captcha", "permission", "인증", "승인")):
        return RecoveryDecision("WAITING_USER", False, "사용자 승인 또는 인증을 기록한 뒤 재개")
    if any(token in text for token in ("input", "schema", "invalid", "qc", "입력")):
        return RecoveryDecision("INVALIDATED", False, "입력 또는 QC를 수정하고 재검증")
    if attempts >= max_attempts:
        return RecoveryDecision("BUDGET_STOP", False, "시도 한도를 늘리거나 원인을 수정한 뒤 명시적으로 재개")
    if any(token in text for token in ("timeout", "tempor", "rate", "network", "provider", "일시")):
        return RecoveryDecision("FAILED_RETRYABLE", True, "지수 backoff 후 같은 task를 재시도")
    return RecoveryDecision("FAILED", False, "원인을 조사하고 복구 조건을 기록")

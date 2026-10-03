#!/usr/bin/env python3
"""Fail if shareable text files contain email addresses or obvious secret assignments."""

import argparse
import re
from pathlib import Path

EMAIL = re.compile(r"(?i)(?<![A-Z0-9._%+-])[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}(?![A-Z0-9._%+-])")
SECRET = re.compile(r"(?i)\b(api[_-]?key|access[_-]?token|auth[_-]?token|password|secret)\b\s*[:=]\s*[\"']?[^\s,;\"']{8,}")
PRIVATE_MAIL_FIELD = re.compile(r"(?i)\b(gmail[_-]?(message|thread|account)[_-]?id|recipient[_-]?email|sender[_-]?email|email[_-]?address|mail(box)?[_-]?account[_-]?id|mail[_-]?subject|message[_-]?subject|mail[_-]?body|message[_-]?body)\b\s*[:=,]")
TEXT_SUFFIXES = {".md", ".txt", ".csv", ".tsv", ".json", ".yaml", ".yml", ".py", ".r", ".sh", ".html", ".xml"}
SKIP_NAMES = {"privacy_audit.py"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    base = args.path.resolve()
    paths = [base] if base.is_file() else sorted(p for p in base.rglob("*") if p.is_file())
    findings = []
    for path in paths:
        if path.name in SKIP_NAMES or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        rel = str(path.relative_to(base)) if base.is_dir() else path.name
        if EMAIL.search(text):
            findings.append(f"email-like identifier: {rel}")
        if SECRET.search(text):
            findings.append(f"secret-like assignment: {rel}")
        if PRIVATE_MAIL_FIELD.search(text):
            findings.append(f"private mail metadata field: {rel}")
    if findings:
        for finding in findings:
            print(finding)
        raise SystemExit(1)
    print(f"Privacy audit clean: {base}")


if __name__ == "__main__":
    main()

"""Fail-closed personal-data and secret-pattern scanning."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class PrivacyFinding:
    kind: str
    source: str


PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("email", re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)),
    ("phone", re.compile(r"(?<!\d)(?:\+?82[- ]?)?0?1[016789][- ]?\d{3,4}[- ]?\d{4}(?!\d)")),
    ("resident_id", re.compile(r"(?<!\d)\d{6}[- ]?[1-4]\d{6}(?!\d)")),
    ("credit_card", re.compile(r"(?<!\d)(?:\d[ -]?){15,19}(?!\d)")),
    ("bearer_token", re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{16,}", re.I)),
    ("openai_style_key", re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b")),
    ("aws_access_key", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    ("assigned_secret", re.compile(r"\b(?:api[_-]?key|secret|password|token)\s*[:=]\s*['\"]?[A-Za-z0-9_./+=-]{8,}", re.I)),
)


def scan_texts(values: Iterable[tuple[str, str]]) -> list[PrivacyFinding]:
    findings: list[PrivacyFinding] = []
    for source, value in values:
        for kind, pattern in PATTERNS:
            if pattern.search(value):
                findings.append(PrivacyFinding(kind=kind, source=source))
    return findings

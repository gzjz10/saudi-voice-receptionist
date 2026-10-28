"""Mask phones, long digit runs and caller names before anything is committed (review B5)."""

from __future__ import annotations

import re

_PATTERNS = [
    re.compile(r"\+?9665\d{8}"),
    re.compile(r"05\d{8}"),
    re.compile(r"\d{7,}"),
    re.compile(r"[٠-٩۰-۹]{7,}"),
]


def redact(text: str, names: list[str] | None = None) -> str:
    for rx in _PATTERNS:
        text = rx.sub("[رقم]", text)
    for name in sorted({n.strip() for n in names or [] if n and n.strip()}, key=len, reverse=True):
        text = text.replace(name, "[اسم]")
    return text

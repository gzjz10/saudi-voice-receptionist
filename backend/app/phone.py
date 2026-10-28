"""Saudi mobile normalization: +966 / 966 / 00966 / 5XXXXXXXX / Arabic digits / words -> 05XXXXXXXX."""

from __future__ import annotations

import re

from .arabic import digit_stream

_PHONE = re.compile(r"^05\d{8}$")


def normalize_phone(raw: str | None) -> str | None:
    """Return `05XXXXXXXX`, or None when the input is not a Saudi mobile number."""
    if not raw:
        return None
    raw = raw.strip()
    plus = raw.startswith("+")
    digits = digit_stream(raw)
    if plus and digits.startswith("966"):
        digits = digits[3:]
    elif digits.startswith("00966"):
        digits = digits[5:]
    elif digits.startswith("966") and len(digits) == 12:
        digits = digits[3:]
    if len(digits) == 9 and digits.startswith("5"):
        digits = "0" + digits
    return digits if _PHONE.match(digits) else None

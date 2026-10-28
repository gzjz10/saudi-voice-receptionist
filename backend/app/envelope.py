"""The one response envelope every tool returns with HTTP 200 (amendment 4)."""

from __future__ import annotations

from typing import Any, Literal

Status = Literal["ok", "error", "needs_clarification", "not_found"]

ERROR_CODES = {
    "not_found", "unknown_topic", "unknown_product", "invalid_qty", "invalid_phone",
    "out_of_stock", "area_not_served", "below_minimum", "outside_hours", "missing_field",
    "quote_not_found", "quote_mismatch",
}


def envelope(status: Status, say_ar: str, error_code: str | None = None, **fields: Any) -> dict:
    if error_code is not None and error_code not in ERROR_CODES:
        raise ValueError(f"unknown error_code {error_code}")
    return {"status": status, "error_code": error_code, "say_ar": say_ar, **fields}


def ok(say_ar: str, **fields: Any) -> dict:
    return envelope("ok", say_ar, **fields)


def error(code: str, say_ar: str, **fields: Any) -> dict:
    return envelope("error", say_ar, error_code=code, **fields)

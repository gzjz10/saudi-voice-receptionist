"""Numbers -> spoken Saudi colloquial Arabic (white Saudi register, plural address).

The register follows the signed TTS lines 2-6 (docs/phase0/tts_script.md); the rest of
backend/tests/golden_spoken.csv is a draft until Ahmed signs it (T072).
"""

from __future__ import annotations

UNITS = ["صفر", "واحد", "اثنين", "ثلاثة", "أربعة", "خمسة", "ستة", "سبعة", "ثمانية", "تسعة"]
# Short forms used before a feminine counted noun (ثلاث علب).
UNITS_SHORT = {3: "ثلاث", 4: "أربع", 5: "خمس", 6: "ست", 7: "سبع", 8: "ثمان", 9: "تسع", 10: "عشر"}
TEENS = {
    10: "عشرة", 11: "احدعش", 12: "اثنعش", 13: "ثلطعش", 14: "أربعطعش", 15: "خمسطعش",
    16: "ستطعش", 17: "سبعطعش", 18: "ثمنطعش", 19: "تسعطعش",
}
TENS = {
    20: "عشرين", 30: "ثلاثين", 40: "أربعين", 50: "خمسين", 60: "ستين", 70: "سبعين",
    80: "ثمانين", 90: "تسعين",
}
HUNDREDS = {
    100: "مية", 200: "ميتين", 300: "ثلاثمية", 400: "أربعمية", 500: "خمسمية",
    600: "ستمية", 700: "سبعمية", 800: "ثمنمية", 900: "تسعمية",
}


def number_ar(n: int) -> str:
    """0..999999 as colloquial words: 117 -> «مية وسبعطعش»."""
    if n < 0:
        raise ValueError("negative")
    if n < 10:
        return UNITS[n]
    if n < 20:
        return TEENS[n]
    if n < 100:
        tens, unit = divmod(n, 10)
        return TENS[tens * 10] if unit == 0 else f"{UNITS[unit]} و{TENS[tens * 10]}"
    if n < 1000:
        h, rest = divmod(n, 100)
        head = HUNDREDS[h * 100]
        return head if rest == 0 else f"{head} و{number_ar(rest)}"
    th, rest = divmod(n, 1000)
    if th == 1:
        head = "ألف"
    elif th == 2:
        head = "ألفين"
    elif th <= 10:
        head = f"{UNITS_SHORT.get(th, number_ar(th))} آلاف"
    else:
        head = f"{number_ar(th)} ألف"
    return head if rest == 0 else f"{head} و{number_ar(rest)}"


def _riyals(r: int) -> str:
    if r == 1:
        return "ريال واحد"
    if r == 2:
        return "ريالين"
    return f"{number_ar(r)} ريال"


def _halalas(h: int) -> str:
    if h == 1:
        return "هللة وحدة"
    if h == 2:
        return "هللتين"
    return f"{number_ar(h)} هللة"


def money_ar(halalas: int) -> str:
    """975 -> «تسعة ريال وخمسة وسبعين هللة»; whole amounts drop the halala part."""
    riyals, hal = divmod(int(halalas), 100)
    if riyals and hal:
        return f"{_riyals(riyals)} و{_halalas(hal)}"
    if hal:
        return _halalas(hal)
    return _riyals(riyals) if riyals else "صفر ريال"


def qty_ar(qty: int, unit: str, unit_dual: str, unit_plural: str, gender: str) -> str:
    """Quantity agreeing with its unit: 1 علبة وحدة, 2 علبتين, 3 ثلاث علب, 11 احدعش علبة."""
    if qty == 1:
        return f"{unit} {'وحدة' if gender == 'f' else 'واحد'}"
    if qty == 2:
        return unit_dual
    if 3 <= qty <= 10:
        word = UNITS_SHORT[qty] if gender == "f" else (TEENS[10] if qty == 10 else UNITS[qty])
        return f"{word} {unit_plural}"
    return f"{number_ar(qty)} {unit}"


def digits_ar(digits: str) -> str:
    return " ".join(UNITS[int(d)] for d in digits)


def phone_ar(phone: str) -> str:
    """0551234567 -> «صفر خمسة خمسة، واحد اثنين ثلاثة، أربعة خمسة ستة سبعة» (3·3·4)."""
    groups = [phone[:3], phone[3:6], phone[6:]]
    return "، ".join(digits_ar(g) for g in groups if g)


def order_id_ar(order_id: str) -> str:
    """4821 -> «أربعة، ثمانية، اثنين، واحد»."""
    return "، ".join(UNITS[int(d)] for d in order_id)

import json

import pytest

from backend.app.arabic import digit_stream, normalize
from backend.app.tools import DATA, matcher

# (query as heard, expected product id). Plurals, dialect words, clitics, fillers and
# Arabic-Indic digits included (review B4 golden table, ≥ 30 pairs).
GOLDEN = [
    ("صحون زجاج", "KIT-004"),
    ("الصحون الزجاج", "KIT-004"),
    ("بكم الصحون الزجاج؟", "KIT-004"),
    ("والصحون الزجاج", "KIT-004"),
    ("بالصحون الزجاج", "KIT-004"),
    ("صحن زجاج", "KIT-004"),
    ("صحون زياي", "KIT-004"),
    ("أطباق زجاج", "KIT-004"),
    ("صُحُون زُجَاج", "KIT-004"),
    ("صحـــون زجاج", "KIT-004"),
    ("صحون بلاستيك", "PLA-011"),
    ("طبق بلاستيك", "PLA-011"),
    ("عندكم كاسات ورق؟", "KIT-001"),
    ("كاسة ورق", "KIT-001"),
    ("أكواب ورقية", "KIT-001"),
    ("كاسات زجاج", "KIT-002"),
    ("أبي اثنعش علبة من أكياس الزبالة", "CLN-001"),
    ("أكياس زبالة", "CLN-001"),
    ("كيس زباله", "CLN-001"),
    ("أكياس قمامة", "CLN-001"),
    ("أكياس النفايات", "CLN-001"),
    ("فوط مطبخ", "KIT-003"),
    ("فوطة", "KIT-003"),
    ("مناديل", "CLN-002"),
    ("ابغى ٣ علب محارم", "CLN-002"),
    ("كلينكس", "CLN-002"),
    ("صابون مواعين", "CLN-003"),
    ("فيري", "CLN-003"),
    ("سطل", "PLA-005"),
    ("برواز", "GFT-003"),
    ("مباخر", "GFT-004"),
    ("سلوتيب", "STA-005"),
    ("شنطة مدرسة", "STA-004"),
    ("ممكن ترمس قهوة", "KIT-007"),
    ("جدر ضغط", "KIT-006"),
    ("معطر جو", "CLN-006"),
]


def products():
    return json.loads((DATA / "products.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("query,expected", GOLDEN)
def test_golden_query(query, expected):
    hits, ambiguous, _ = matcher().match(query)
    assert not ambiguous, (query, hits)
    assert hits and hits[0].product_id == expected, (query, hits)


def test_golden_table_size():
    assert len(GOLDEN) >= 30


@pytest.mark.parametrize("query,pair", [
    ("بكم الصحون", {"KIT-004", "PLA-011"}),
    ("صحن", {"KIT-004", "PLA-011"}),
    ("كاسات", {"KIT-001", "KIT-002"}),
    ("أكواب", {"KIT-001", "KIT-002"}),
])
def test_near_duplicates_ask_with_two_options(query, pair):
    hits, ambiguous, _ = matcher().match(query)
    assert ambiguous and len(hits) == 2 and {h.product_id for h in hits} == pair


@pytest.mark.parametrize("query", ["ايفون", "سيارة", "بكم", "؟؟"])
def test_unknown_product_has_no_match(query):
    hits, _, _ = matcher().match(query)
    assert hits == []


def test_alias_lint():
    items = products()
    seen: dict[str, str] = {}
    categories = {"مطبخ", "تنظيف", "بلاستيك", "هدايا", "قرطاسيه", "اكواب", "صحون", "اكياس", "اقلام"}
    for p in items:
        for name in [p["name_ar"], *p["aliases_ar"]]:
            key = normalize(name)
            assert key not in seen or seen[key] == p["id"], f"{name} shared by {seen.get(key)} and {p['id']}"
            seen[key] = p["id"]
            assert key not in categories, f"bare category word {name} on {p['id']}"


def test_catalog_shape():
    items = products()
    assert len(items) == 30
    assert sum(not p["in_stock"] for p in items) == 2
    assert {p["price_halalas"] for p in items} <= {575, 975, 1475}
    assert {p["category"] for p in items} == {"kitchen", "cleaning", "plastics", "gifts", "stationery"}
    assert all(p["unit_gender"] in {"m", "f"} for p in items)
    assert len({p["id"] for p in items}) == 30


def test_normalize_steps():
    assert normalize("الصُّحـون") == "صحون"
    assert normalize("للمبرز والصحون") == "مبرز صحون"
    assert normalize("إأآٱ ة ى ؤ ئ") == "اااا ه ي و ي"
    assert normalize("٠٥٥١٢٣٤٥٦٧") == "0551234567"
    assert normalize("بكم الصحون؟", drop_fillers=True) == "صحون"
    # Short stems keep their ال (min stem 3).
    assert normalize("الجو") == "الجو"


def test_name_ar_is_never_normalized():
    from backend.app.tools import _match_dict, products as prods
    assert _match_dict(prods()["KIT-004"])["name_ar"] == "صحون زجاج"


def test_digit_stream():
    assert digit_stream("صفر خمسة وخمسين، ثمانية وسبعين، ثلاثة أربعة خمسة ستة سبعة") == "0557834567"
    assert digit_stream("رقمه أربعة، ثمانية، اثنين، واحد") == "4821"
    assert digit_stream("٠٥٥ ١٢٣ ٤٥٦٧") == "0551234567"

"""The 6 tool handlers. Each takes a validated request and returns an envelope dict.

Facts come only from data/products.json, data/store.json and SQLite; every number a caller
hears has a *_spoken_ar field built by spoken.py.
"""

from __future__ import annotations

import json
import secrets
import sqlite3
from datetime import datetime
from functools import lru_cache
from pathlib import Path

from . import db, spoken
from .arabic import Matcher, normalize
from .envelope import envelope, error, ok
from .models import (CheckOrderStatusRequest, CreateOrderRequest, EscalateRequest, GetProductRequest,
                     GetStoreInfoRequest, QuoteOrderRequest)
from .phone import normalize_phone
from .timeslot import RIYADH, SlotError, parse_now, resolve

DATA = Path(__file__).resolve().parents[2] / "data"
MAX_QTY = 20

STATUS_AR = {
    "received": "استلمنا طلبكم وبنبدأ نجهزه",
    "preparing": "طلبكم قاعد يتجهز",
    "ready": "طلبكم جاهز للاستلام",
    "out_for_delivery": "طلبكم طلع مع المندوب",
    "delivered": "طلبكم توصل",
    "cancelled": "طلبكم ملغي",
}


@lru_cache(maxsize=1)
def products() -> dict[str, dict]:
    items = json.loads((DATA / "products.json").read_text(encoding="utf-8"))
    return {p["id"]: p for p in items}


@lru_cache(maxsize=1)
def store() -> dict:
    return json.loads((DATA / "store.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def matcher() -> Matcher:
    return Matcher(list(products().values()))


def bi(word: str) -> str:
    """Attach the preposition ب: «ب» + «تسعة» -> «بتسعة»."""
    return "ب" + word


def li(word: str) -> str:
    """Attach the preposition ل: «الهفوف» -> «للهفوف», «مبرز» -> «لمبرز»."""
    return "ل" + word[1:] if word.startswith("ال") else "ل" + word


def _now_iso() -> str:
    return datetime.now(RIYADH).isoformat(timespec="seconds")


def _match_dict(p: dict) -> dict:
    return {
        "product_id": p["id"], "name_ar": p["name_ar"], "price_halalas": p["price_halalas"],
        "price_spoken_ar": spoken.money_ar(p["price_halalas"]), "in_stock": p["in_stock"], "unit": p["unit"],
    }


def _alternatives(pid: str) -> list[dict]:
    p = products()[pid]
    pool = [q for q in products().values() if q["in_stock"] and q["id"] != pid and q["category"] == p["category"]]
    return [_match_dict(products()[i]) for i in matcher().similar(pid, pool)]


# ---------------------------------------------------------------- get_product
def get_product(req: GetProductRequest) -> dict:
    hits, ambiguous, weak = matcher().match(req.query)
    if not hits:
        sugg = [_match_dict(products()[h.product_id]) for h in weak if products()[h.product_id]["in_stock"]]
        return envelope("not_found", "ما لقيت هالمنتج عندنا، ممكن توضحون اسمه؟", error_code="not_found",
                        matches=[], needs_clarification=False, suggestions=sugg[:2])
    matches = [_match_dict(products()[h.product_id]) for h in hits][:3]
    if ambiguous:
        names = [m["name_ar"] for m in matches[:2]]
        return envelope("needs_clarification", f"تقصدون {names[0]} أو {names[1]}؟", matches=matches[:2],
                        needs_clarification=True, clarify_options_ar=names)
    top = matches[0]
    if not top["in_stock"]:
        alts = _alternatives(top["product_id"])
        say = f"للأسف {top['name_ar']} خلصت حالياً"
        if alts:
            say += "، عندنا " + " و".join(a["name_ar"] for a in alts)
        return ok(say, matches=matches, needs_clarification=False, suggestions=alts)
    p = products()[top["product_id"]]
    say = f"{p['name_ar']} موجودة، {p['unit']} {bi(top['price_spoken_ar'])}"
    return ok(say, matches=matches, needs_clarification=False, suggestions=[])


# ------------------------------------------------------------- get_store_info
def get_store_info(req: GetStoreInfoRequest) -> dict:
    s = store()
    extra: dict = {}
    if req.topic == "hours":
        if req.day == "fri":
            text = s["hours_spoken_ar"]["fri"]
        elif req.day:
            text = s["hours_spoken_ar"]["sat_thu"]
        else:
            text = f"{s['hours_spoken_ar']['sat_thu']}، و{s['hours_spoken_ar']['fri']}"
    elif req.topic == "location":
        text = s["location_ar"]
        extra["map_url"] = s["map_url"]
    elif req.topic == "delivery":
        d = s["delivery"]
        text = (f"نوصل {'، و'.join(li(a) for a in d['areas_ar'])}. التوصيل {bi(spoken.money_ar(d['fee_halalas']))}، "
                f"وأقل طلب للتوصيل {spoken.money_ar(d['min_order_halalas'])}")
        extra["served_areas_ar"] = d["areas_ar"]
    elif req.topic == "returns":
        text = s["returns_ar"]
    else:
        text = f"رقم المحل {spoken.phone_ar(s['phone'])}"
    return ok(text, text_ar=text, **extra)


# ---------------------------------------------------------------- quote_order
def quote_order(req: QuoteOrderRequest, conn: sqlite3.Connection) -> dict:
    s = store()
    merged: dict[str, int] = {}
    for it in req.items:
        if it.product_id not in products():
            return error("unknown_product", "ما لقيت هالمنتج عندنا، ممكن توضحون اسمه؟")
        merged[it.product_id] = merged.get(it.product_id, 0) + it.qty
    for pid, qty in merged.items():
        if not 1 <= qty <= MAX_QTY:
            return error("invalid_qty", f"نقدر ناخذ من {spoken.number_ar(1)} لين {spoken.number_ar(MAX_QTY)} من كل منتج")
        if not products()[pid]["in_stock"]:
            p = products()[pid]
            return error("out_of_stock", f"للأسف {p['name_ar']} خلصت حالياً", suggestions=_alternatives(pid))
    area = None
    if req.fulfillment == "delivery":
        if not req.area:
            return error("missing_field", "وين تبون نوصل الطلب؟")
        key = normalize(req.area)
        area = next((a for a in s["delivery"]["areas_ar"] if normalize(a) == key), None)
        if area is None:
            served = s["delivery"]["areas_ar"]
            return error("area_not_served", f"للأسف ما نوصل لهالمنطقة، نوصل {'، و'.join(li(a) for a in served)}",
                         served_areas_ar=served)
    now = parse_now(req.now)
    try:
        slot = resolve(req.time_slot, s, now)
    except SlotError as e:
        if e.code == "missing_field":
            return error("missing_field", "متى يناسبكم؟ الصبح ولا الظهر ولا العصر ولا المغرب؟")
        return error("outside_hours", "المحل مسكر بهالوقت، " + s["hours_spoken_ar"]["sat_thu"])

    lines = []
    for pid, qty in merged.items():
        p = products()[pid]
        lines.append({
            "product_id": pid, "name_ar": p["name_ar"], "qty": qty,
            "qty_spoken_ar": spoken.qty_ar(qty, p["unit"], p["unit_dual_ar"], p["unit_plural_ar"], p["unit_gender"]),
            "unit_price_halalas": p["price_halalas"], "line_total_halalas": qty * p["price_halalas"],
        })
    subtotal = sum(l["line_total_halalas"] for l in lines)
    fee = s["delivery"]["fee_halalas"] if req.fulfillment == "delivery" else 0
    total = subtotal + fee
    slot_out = {"date": slot.date.isoformat(), "window": slot.window, "time_slot_spoken_ar": slot.spoken_ar}
    totals = {"lines": lines, "subtotal_halalas": subtotal, "delivery_fee_halalas": fee, "total_halalas": total,
              "total_spoken_ar": spoken.money_ar(total), "slot": slot_out}
    if req.fulfillment == "delivery" and subtotal < s["delivery"]["min_order_halalas"]:
        need = spoken.money_ar(s["delivery"]["min_order_halalas"])
        return error("below_minimum", f"أقل طلب للتوصيل {need}، وطلبكم الحين {spoken.money_ar(subtotal)}",
                     below_minimum=True, **totals)

    quote_id = "q_" + secrets.token_hex(8)
    body = req.model_dump(exclude={"conversation_id", "now"})
    conn.execute(
        "INSERT INTO quotes (quote_id, conversation_id, body_json, lines_json, subtotal_halalas, delivery_fee_halalas,"
        " total_halalas, below_minimum, fulfillment, area, slot_date, slot_window, slot_spoken_ar, created_at)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (quote_id, req.conversation_id, json.dumps(body, ensure_ascii=False), json.dumps(lines, ensure_ascii=False),
         subtotal, fee, total, 0, req.fulfillment, area, slot_out["date"], slot.window, slot.spoken_ar, _now_iso()),
    )
    basket = "، و".join(f"{l['qty_spoken_ar']} {l['name_ar']}" for l in lines)
    how = f"توصيل {li(area)}" if area else "استلام من المحل"
    fee_txt = f" شامل التوصيل {spoken.money_ar(fee)}" if fee else ""
    say = f"طلبكم {basket}، المجموع {spoken.money_ar(total)}{fee_txt}، {how} {slot.spoken_ar}. أأكد الطلب؟"
    return ok(say, quote_id=quote_id, below_minimum=False, **totals)


# --------------------------------------------------------------- create_order
def _order_reply(row: sqlite3.Row, duplicate: bool) -> dict:
    oid = row["order_id"]
    say = (f"تم تأكيد طلبكم، رقم الطلب {spoken.order_id_ar(oid)}، "
           f"والمجموع {spoken.money_ar(row['total_halalas'])}")
    return ok(say, order_id=oid, order_id_spoken_ar=spoken.order_id_ar(oid),
              phone_spoken_ar=spoken.phone_ar(row["phone"]), total_halalas=row["total_halalas"],
              total_spoken_ar=spoken.money_ar(row["total_halalas"]), duplicate=duplicate)


def create_order(req: CreateOrderRequest, conn: sqlite3.Connection) -> dict:
    q = conn.execute("SELECT * FROM quotes WHERE quote_id = ?", (req.quote_id,)).fetchone()
    if q is None:
        return error("quote_not_found", "صار خطأ في الطلب، خلوني أراجع السلة معكم مرة ثانية")
    if req.conversation_id and q["conversation_id"] and req.conversation_id != q["conversation_id"]:
        return error("quote_mismatch", "صار خطأ في الطلب، خلوني أراجع السلة معكم مرة ثانية")
    # Idempotent on the quote: a quote is bound to its conversation, and SQLite's UNIQUE
    # treats NULL conversation ids as distinct, so look the quote up directly.
    existing = conn.execute("SELECT * FROM orders WHERE quote_id = ?", (req.quote_id,)).fetchone()
    if existing is not None:
        return _order_reply(existing, duplicate=True)
    phone = normalize_phone(req.phone)
    if phone is None:
        return error("invalid_phone", "الرقم ما وصلني صح، ممكن تعيدونه رقم رقم؟ يبدأ بصفر خمسة")
    lines = json.loads(q["lines_json"])
    items = [{"product_id": l["product_id"], "qty": l["qty"], "unit_price_halalas": l["unit_price_halalas"]} for l in lines]
    for _ in range(50):
        oid = f"{secrets.randbelow(9000) + 1000}"
        try:
            conn.execute(
                "INSERT INTO orders (order_id, created_at, customer_name, phone, fulfillment, area, slot_date,"
                " slot_window, items_json, total_halalas, quote_id, conversation_id) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (oid, _now_iso(), req.customer_name, phone, q["fulfillment"], q["area"], q["slot_date"],
                 q["slot_window"], json.dumps(items, ensure_ascii=False), q["total_halalas"], req.quote_id,
                 req.conversation_id or q["conversation_id"]),
            )
            break
        except sqlite3.IntegrityError:
            continue
    row = conn.execute("SELECT * FROM orders WHERE order_id = ?", (oid,)).fetchone()
    return _order_reply(row, duplicate=False)


# --------------------------------------------------------- check_order_status
def check_order_status(req: CheckOrderStatusRequest, conn: sqlite3.Connection) -> dict:
    if req.order_id:
        rows = conn.execute("SELECT * FROM orders WHERE order_id = ?", (req.order_id,)).fetchall()
    else:
        phone = normalize_phone(req.phone)
        if phone is None:
            return error("invalid_phone", "الرقم ما وصلني صح، ممكن تعيدونه رقم رقم؟ يبدأ بصفر خمسة")
        rows = conn.execute("SELECT * FROM orders WHERE phone = ? ORDER BY created_at DESC LIMIT 2", (phone,)).fetchall()
    if not rows:
        return envelope("not_found", "ما لقيت طلب بهالمعلومات، ممكن تتأكدون من الرقم؟", error_code="not_found", orders=[])
    orders = [{"order_id": r["order_id"], "order_id_spoken_ar": spoken.order_id_ar(r["order_id"]),
               "status": r["status"], "status_ar": STATUS_AR[r["status"]]} for r in rows]
    say = "، و".join(f"الطلب رقم {o['order_id_spoken_ar']}: {o['status_ar']}" for o in orders)
    return ok(say, orders=orders)


# ---------------------------------------------------------- escalate_to_human
def escalate_to_human(req: EscalateRequest, conn: sqlite3.Connection) -> dict:
    ticket_id = "t_" + secrets.token_hex(6)
    conn.execute(
        "INSERT INTO tickets (ticket_id, created_at, reason, summary, customer_name, phone, conversation_id)"
        " VALUES (?,?,?,?,?,?,?)",
        (ticket_id, _now_iso(), req.reason, req.summary, req.customer_name, normalize_phone(req.phone),
         req.conversation_id),
    )
    if req.reason == "cancel_request":
        text = "ما أقدر ألغي الطلب بنفسي، بس سجلت طلبكم وبيتواصل معكم موظف يساعدكم في الإلغاء"
    else:
        text = "أبشروا، سجلت طلبكم وبيتواصل معكم موظف في أقرب وقت"
    return ok(text, ticket_id=ticket_id, callback_text_ar=text)


HANDLERS = {
    "get_product": (GetProductRequest, get_product, False),
    "get_store_info": (GetStoreInfoRequest, get_store_info, False),
    "quote_order": (QuoteOrderRequest, quote_order, True),
    "create_order": (CreateOrderRequest, create_order, True),
    "check_order_status": (CheckOrderStatusRequest, check_order_status, True),
    "escalate_to_human": (EscalateRequest, escalate_to_human, True),
}

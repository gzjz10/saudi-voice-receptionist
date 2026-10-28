"""SQLite storage for quotes, orders and tickets (data-model C1-C3)."""

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DEFAULT_DB = REPO / "backend" / "data" / "sara.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS quotes (
  quote_id             TEXT PRIMARY KEY,
  conversation_id      TEXT,
  body_json            TEXT NOT NULL,
  lines_json           TEXT NOT NULL,
  subtotal_halalas     INTEGER NOT NULL CHECK (subtotal_halalas >= 0),
  delivery_fee_halalas INTEGER NOT NULL CHECK (delivery_fee_halalas >= 0),
  total_halalas        INTEGER NOT NULL CHECK (total_halalas >= 0),
  below_minimum        INTEGER NOT NULL DEFAULT 0,
  fulfillment          TEXT NOT NULL CHECK (fulfillment IN ('pickup','delivery')),
  area                 TEXT,
  slot_date            TEXT NOT NULL,
  slot_window          TEXT NOT NULL,
  slot_spoken_ar       TEXT NOT NULL,
  created_at           TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS orders (
  order_id        TEXT PRIMARY KEY CHECK (length(order_id) = 4 AND order_id GLOB '[0-9][0-9][0-9][0-9]'),
  created_at      TEXT NOT NULL,
  customer_name   TEXT NOT NULL CHECK (length(customer_name) BETWEEN 1 AND 40),
  phone           TEXT NOT NULL CHECK (phone GLOB '05[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]'),
  fulfillment     TEXT NOT NULL CHECK (fulfillment IN ('pickup','delivery')),
  area            TEXT,
  slot_date       TEXT NOT NULL,
  slot_window     TEXT NOT NULL,
  items_json      TEXT NOT NULL,
  total_halalas   INTEGER NOT NULL CHECK (total_halalas >= 0),
  status          TEXT NOT NULL DEFAULT 'received'
                  CHECK (status IN ('received','preparing','ready','out_for_delivery','delivered','cancelled')),
  quote_id        TEXT REFERENCES quotes(quote_id),
  conversation_id TEXT,
  UNIQUE (conversation_id, quote_id),
  CHECK (fulfillment = 'pickup' OR area IS NOT NULL)
);
CREATE TABLE IF NOT EXISTS tickets (
  ticket_id       TEXT PRIMARY KEY,
  created_at      TEXT NOT NULL,
  reason          TEXT NOT NULL CHECK (reason IN ('asked_for_human','angry','not_understood','cancel_request','other')),
  summary         TEXT NOT NULL CHECK (length(summary) BETWEEN 1 AND 300),
  customer_name   TEXT CHECK (customer_name IS NULL OR length(customer_name) <= 40),
  phone           TEXT,
  conversation_id TEXT
);
"""

# One order per status group (in progress / ready / done), obviously fake phones.
SEED_ORDERS = [
    ("4821", "2026-10-26T18:10:00+03:00", "فهد", "0500000001", "pickup", None, "2026-10-29", "afternoon",
     [{"product_id": "CLN-002", "qty": 3, "unit_price_halalas": 575}], 1725, "preparing"),
    ("3157", "2026-10-25T11:30:00+03:00", "نورة", "0500000002", "delivery", "المبرز", "2026-10-27", "evening",
     [{"product_id": "KIT-004", "qty": 2, "unit_price_halalas": 975}, {"product_id": "CLN-001", "qty": 4, "unit_price_halalas": 975}],
     7350, "out_for_delivery"),
    ("2690", "2026-10-20T20:05:00+03:00", "سلمان", "0500000003", "pickup", None, "2026-10-21", "morning",
     [{"product_id": "GFT-004", "qty": 1, "unit_price_halalas": 1475}], 1475, "delivered"),
]


def db_path() -> Path:
    return Path(os.environ.get("SARA_DB_PATH", DEFAULT_DB))


def connect() -> sqlite3.Connection:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init(reset: bool = False) -> None:
    """Create tables and the 3 seed orders. `reset` drops everything first (per eval run)."""
    with connect() as conn:
        if reset:
            conn.executescript("DROP TABLE IF EXISTS orders; DROP TABLE IF EXISTS tickets; DROP TABLE IF EXISTS quotes;")
        conn.executescript(SCHEMA)
        for (oid, created, name, phone, ful, area, sdate, swin, items, total, status) in SEED_ORDERS:
            conn.execute(
                "INSERT OR IGNORE INTO orders (order_id, created_at, customer_name, phone, fulfillment, area,"
                " slot_date, slot_window, items_json, total_halalas, status) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (oid, created, name, phone, ful, area, sdate, swin, json.dumps(items, ensure_ascii=False), total, status),
            )

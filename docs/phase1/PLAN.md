# Phase 1 — Tools backend + tunnel: plan and tasks

Started 2026-10-28 on the Mac, in parallel with Phase 0b (Ahmed's say-so, review amendment 12).
Full task text: `specs/001-saudi-voice-receptionist/tasks.md` T044–T076. API shapes:
`specs/001-saudi-voice-receptionist/contracts/tools.openapi.yaml`. Data: `data-model.md` B–C.

## Goal

A FastAPI backend that Sara calls as webhook tools. It is the only source of prices, stock,
orders and store facts, and every number it returns has a ready-to-speak Saudi Arabic version.

## The 6 tools (`POST /tools/<name>`, header `X-Tool-Secret`)

| Tool | What it does |
| --- | --- |
| `get_product` | Finds a product from what the caller said (aliases, plurals, dialect). ≤ 3 matches; asks to choose between 2 when names are close |
| `get_store_info` | Hours (Friday separate), location, delivery areas and fee, returns, phone |
| `quote_order` | Prices a basket with no side effects. The only source of the total Sara reads back |
| `create_order` | Creates the order from a quote after a clear yes. Same call twice → same order (`duplicate: true`) |
| `check_order_status` | By 4-digit order id, or the 2 latest orders by phone |
| `escalate_to_human` | Opens a callback ticket (asked for human, angry, not understood, cancel request) |

## Decisions taken for Phase 1

- **Arabic only:** `say_en` / `text_en` are dropped from the contract.
- **Store name:** مقاضينا (as in the signed TTS line 1), with the demo disclaimer «نسخة تجريبية، الأسعار غير حقيقية».
- **Money in halalas** (integers); order ids are 4 digits; seed phones are obviously fake (0500000001…).
- **Rate limit** (~30/min per IP) can be switched off for tests and the latency run; behind the tunnel it reads `CF-Connecting-IP`.
- **Pins** (PyPI, 2026-10-28, newest ≥ 14 days old): fastapi 0.143.1, pydantic 2.14.1, uvicorn 0.54.0, rapidfuzz 3.14.6, httpx 0.28.1, PyYAML 6.0.3, jsonschema 4.26.0, pytest 9.1.1, tzdata 2026.5.

## Tasks

Legend: ✅ done · 🔄 in progress · ⬜ to do · 👤 needs Ahmed

### Setup
- ✅ T044 Pin packages in `requirements.txt`, install, record versions
- ✅ T045 Package skeleton: `backend/app/main.py`, `backend/tests/conftest.py`
- ✅ T046 gitleaks hook script + `.gitleaks.toml` (gitleaks 8.30.1 pinned, not installed yet)

### Data and building blocks
- ✅ T048 `data/products.json` (30 fake items, 5 categories, trap items) and `data/store.json`
- ✅ T047 `db.py`: SQLite tables `quotes`, `orders`, `tickets`
- ✅ T049 Seed 3 orders (one per status group)
- ✅ T051 Response envelope `{status, error_code, say_ar, …}`
- ✅ T052 Secret check (401), rate limit (429), 8 KB body cap (413)
- ✅ T053 JSON tool-call log (no header values)
- ✅ T054–T055 Arabic matcher + ≥ 30 golden query→product tests
- ✅ T056–T057 Spoken Arabic numbers + `golden_spoken.csv` (signed lines 2–6 reproduced exactly)
- ✅ T058 Phone normalizer (+966, 966, 5XXXXXXXX, Arabic digits → 05XXXXXXXX)
- ✅ T059 Time slot resolver («بكرة العصر» → date + window, Friday hours)
- ✅ T060 Redaction of phones and names for eval excerpts
- ✅ T061 Contract tests: every response checked against the OpenAPI schemas
- ✅ T050 `scripts/build_agent_config.py` (render `sara.json` from the prompt)

### Tools
- ✅ T062 `get_product`
- ✅ T063 `get_store_info`
- ✅ T064 `quote_order`
- ✅ T065 `create_order` (idempotent)
- ✅ T066 `check_order_status`
- ✅ T067 `escalate_to_human`

### Scripts and checks
- ✅ T068 `scripts/test.sh` · T069 `scripts/dev.sh` · T070 `scripts/latency.sh` (p95 < 300 ms)
- ✅ T071 `scripts/tunnel.sh` written (cloudflared 2026.7.1); Ahmed starts it for T074
- ✅ T073 Run tests + latency on the Mac, summary into `docs/STATUS.md`
- ✅ T072 Ahmed approved `backend/tests/golden_spoken.csv` (all rows, 2026-10-28)
- ✅ T074 Tunnel check: all 6 tools 200 with secret, 401 without, through the public URL (`scripts/tunnel_check.sh`)
- 👤 T075 Fresh clone on the Windows laptop runs `scripts/test.sh` green

### Gate
- ⬜ T076 **Phase 1 gate** (everything PASS except the Windows clone): tests green (≥ 30 matcher pairs, golden spoken), 401/413/422 and 200 envelopes on every error path, idempotent `create_order`, p95 < 300 ms, tunnel check, Windows clone green

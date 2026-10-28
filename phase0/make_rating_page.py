"""Phase 0b: build one self-contained rating page from the blind clips.

    python phase0/make_rating_page.py            # -> phase0/samples/blind/rate.html (git-ignored)

The page embeds phase0/samples/blind/NNN.mp3 as data URIs, so a rater gets a
single file (WhatsApp, AirDrop) that works offline on a phone. It shows only
blind ids, never voice, model or line. The rater picks R1/R2/R3, rates each
clip, and copies or downloads rows in the docs/phase0/tts_ratings.csv format:
rater_id,blind_id,naturalness,number_correct,note
"""

from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

BLIND = Path(__file__).resolve().parent / "samples" / "blind"

PAGE = """<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>تقييم الأصوات</title>
<style>
  :root { --bg:#fafaf7; --card:#fff; --ink:#1c1c1a; --muted:#6b6b66; --line:#e3e2dc; --accent:#0f4c4a; --on:#fff; }
  @media (prefers-color-scheme: dark) {
    :root { --bg:#151514; --card:#1e1e1c; --ink:#ecebe6; --muted:#a3a29b; --line:#33332f; --accent:#5fb3ae; --on:#0d0d0c; }
  }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:var(--ink); font:16px/1.6 system-ui, -apple-system, "Segoe UI", Tahoma, sans-serif; }
  main { max-width:640px; margin:0 auto; padding:20px 16px 64px; }
  h1 { font-size:22px; margin:0 0 4px; }
  p { margin:6px 0; color:var(--muted); }
  .scale { background:var(--card); border:1px solid var(--line); border-radius:12px; padding:12px 16px; margin:14px 0; }
  .scale div { color:var(--ink); }
  .card { background:var(--card); border:1px solid var(--line); border-radius:12px; padding:14px 16px; margin:12px 0; }
  .card.done { border-color:var(--accent); }
  .id { font-weight:700; font-size:18px; }
  audio { width:100%; margin:8px 0; }
  .row { display:flex; gap:6px; flex-wrap:wrap; align-items:center; margin:6px 0; }
  .lbl { color:var(--muted); font-size:14px; min-width:100%; }
  button.opt { flex:1; min-width:44px; padding:10px 0; border:1px solid var(--line); border-radius:8px; background:transparent; color:var(--ink); font:inherit; cursor:pointer; }
  button.opt[aria-pressed="true"] { background:var(--accent); color:var(--on); border-color:var(--accent); }
  input[type=text], select { width:100%; padding:10px; border:1px solid var(--line); border-radius:8px; background:transparent; color:var(--ink); font:inherit; }
  .bar { position:sticky; bottom:0; background:var(--bg); border-top:1px solid var(--line); padding:12px 0; display:flex; gap:8px; }
  .bar button { flex:1; padding:12px; border:0; border-radius:10px; background:var(--accent); color:var(--on); font:inherit; font-weight:600; cursor:pointer; }
  .bar button:disabled { opacity:.45; cursor:not-allowed; }
  #msg { text-align:center; min-height:1.6em; }
</style>
</head>
<body>
<main>
  <h1>تقييم صوت موظفة الاستقبال</h1>
  <p>اسمع كل مقطع مرة وحدة بسماعات، وقيّمه لحالك بدون نقاش مع أحد.</p>
  <div class="scale">
    <div><b>مدى سعودية الصوت (١–٥):</b></div>
    <div>١ = أجنبي أو مكسّر · ٢ = فصحى مثل قارئ الأخبار · ٣ = خليجي فيه أخطاء واضحة</div>
    <div>٤ = موظفة استقبال سعودية مع غلطة بسيطة · ٥ = ما تفرقها عن سعودية أصلية</div>
    <div style="margin-top:6px"><b>الرقم:</b> إذا المقطع فيه رقم أو سعر، هل سمعت الرقم واضح وصحيح؟</div>
  </div>
  <div class="row"><span class="lbl">مين أنت؟</span>
    <select id="rater"><option value="">اختر</option><option>R1</option><option>R2</option><option>R3</option></select>
  </div>
  <div id="list"></div>
  <p id="msg"></p>
  <div class="bar">
    <button id="copy" disabled>انسخ النتائج</button>
    <button id="save" disabled>حمّل الملف</button>
  </div>
</main>
<script>
const CLIPS = __CLIPS__;
const state = {};
const list = document.getElementById("list");
const msg = document.getElementById("msg");
const rater = document.getElementById("rater");
const digits = n => String(n).replace(/[0-9]/g, d => "٠١٢٣٤٥٦٧٨٩"[d]);

for (const c of CLIPS) {
  state[c.id] = { n: "", num: "", note: "" };
  const card = document.createElement("div");
  card.className = "card";
  card.innerHTML = `<div class="id">مقطع ${digits(c.id)}</div>
    <audio controls preload="none" src="${c.src}"></audio>
    <div class="row"><span class="lbl">مدى سعودية الصوت</span>
      ${[1,2,3,4,5].map(v => `<button class="opt" data-k="n" data-v="${v}" aria-pressed="false">${digits(v)}</button>`).join("")}</div>
    <div class="row"><span class="lbl">الرقم (إذا فيه رقم)</span>
      <button class="opt" data-k="num" data-v="y" aria-pressed="false">صح</button>
      <button class="opt" data-k="num" data-v="n" aria-pressed="false">غلط</button>
      <button class="opt" data-k="num" data-v="" aria-pressed="true">ما فيه رقم</button></div>
    <input type="text" placeholder="ملاحظة: الكلمة اللي طلعت غلط (اختياري)">`;
  card.querySelectorAll("button.opt").forEach(b => b.onclick = () => {
    card.querySelectorAll(`button[data-k="${b.dataset.k}"]`).forEach(x => x.setAttribute("aria-pressed", "false"));
    b.setAttribute("aria-pressed", "true");
    state[c.id][b.dataset.k] = b.dataset.v;
    card.classList.toggle("done", !!state[c.id].n);
    refresh();
  });
  card.querySelector("input").oninput = e => { state[c.id].note = e.target.value; };
  list.appendChild(card);
}
rater.onchange = refresh;

function ready() { return rater.value && CLIPS.every(c => state[c.id].n); }
function refresh() {
  const left = CLIPS.filter(c => !state[c.id].n).length;
  document.getElementById("copy").disabled = document.getElementById("save").disabled = !ready();
  msg.textContent = !rater.value ? "اختر R1 أو R2 أو R3 فوق" : left ? `باقي ${digits(left)} مقطع` : "خلصت، انسخ النتائج وأرسلها";
}
function csv() {
  const q = s => /[",\\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  return CLIPS.map(c => [rater.value, c.id, state[c.id].n, state[c.id].num, q(state[c.id].note.trim())].join(",")).join("\\n") + "\\n";
}
document.getElementById("copy").onclick = async () => {
  try { await navigator.clipboard.writeText(csv()); msg.textContent = "انتسخت، الصقها في رسالة"; }
  catch { msg.textContent = "ما قدرت أنسخ، استخدم «حمّل الملف»"; }
};
document.getElementById("save").onclick = () => {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([csv()], { type: "text/csv" }));
  a.download = `ratings_${rater.value}.csv`;
  a.click();
};
refresh();
</script>
</body>
</html>
"""


def main() -> int:
    files = sorted(BLIND.glob("[0-9][0-9][0-9].mp3"))
    if not files:
        print(f"no blind clips in {BLIND}; run tts_samples.py --blind first", file=sys.stderr)
        return 1
    clips = [{"id": f.stem, "src": "data:audio/mpeg;base64," + base64.b64encode(f.read_bytes()).decode()} for f in files]
    out = BLIND / "rate.html"
    out.write_text(PAGE.replace("__CLIPS__", json.dumps(clips)), encoding="utf-8")
    print(f"wrote {out.relative_to(BLIND.parent.parent.parent)} ({len(clips)} clips, {out.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

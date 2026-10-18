"""40-second autoplay stage view for the demo -> results/stage.html (1920x1080, dark).

Numbers come from results/summary.json (behavior) and results/graded.jsonl; frames from the headline v2 batch.
Box coordinates are fixed because the v2 layout is fixed (measured on the 1100px-wide full-page frames).
usage: .venv/bin/python src/stage.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
import grade  # noqa: E402

SET = "runs_rendered_v2_n10"
S = json.loads((ROOT / "results/summary.json").read_text())
runs = [json.loads(l) for l in open(ROOT / f"results/{SET}.jsonl") if l.strip()]
MODELS = [("claude", "Claude"), ("gpt-oss-20b", "gpt-oss 20B"), ("gemma4-26b", "Gemma 4 26B"), ("qwen3.5-9b", "Qwen 3.5 9B")]


def verdict(r):
    if grade.infra_reason(r):
        return "infra"
    g = grade.grade(r)
    return "correct" if g["all_correct"] else ("wrong" if g["any_wrong"] else "notfound")


tiles = sorted(runs, key=lambda r: (r["layout"], [m for m, _ in MODELS].index(r["model"]), r["rep"]))
tile_data = [{"m": r["model"], "l": r["layout"][0], "v": verdict(r)} for r in tiles]


def pick(model, layout, cond):
    return next(r for r in runs if r["model"] == model and r["layout"] == layout and cond(r))


clicked = lambda r: any(t["name"] == "click" for t in r["tool_calls"])  # noqa: E731
g_a = pick("gpt-oss-20b", "A_original", lambda r: verdict(r) == "wrong")
g_c = pick("gpt-oss-20b", "C_faq_structured", lambda r: verdict(r) == "correct")
c_a = pick("claude", "A_original", lambda r: verdict(r) == "correct" and clicked(r))
fr = lambda r, i: r["tool_calls"][i]["frame"]  # noqa: E731
g_ans = g_a["answer"]

B = {(b["run_set"], b["layout"], b["model"]): b for b in S["behavior"]}
board = []
for m, ml in MODELS:
    b = B[(SET, "A_original", m)]
    dots = [verdict(r) for r in sorted((r for r in runs if r["model"] == m and r["layout"] == "A_original"), key=lambda r: r["rep"])]
    board.append({"name": ml, "dots": dots, "clicked": f"{b['click_rate']['k']}/{b['click_rate']['n']}",
                  "cw": f"{b['confident_wrong_rate']['k']}/{b['confident_wrong_rate']['n']}",
                  "ok": f"{b['correct_rate']['k']}/{b['correct_rate']['n']}"})
allA = B[(SET, "A_original", "ALL")]
allC = B[(SET, "C_faq_structured", "ALL")]
n_infra = sum(S.get("excluded_infra_by_run_set", {}).get(SET, {}).values())

# crop window on the 1100px frames (GPU card) and boxes in crop coordinates
CROP_Y = 615
A_PRICE = (296, 323, 80, 32)      # RTX 4090 price, layout A (both tabs: same row position)
C_PRICE = (303, 344, 74, 32)      # RTX 4090 on-demand price, layout C
OD_TAB = (308, 55)                # On-demand pill tab centre, layout A

doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>AgentReadable Stage</title>
<style>
:root{{--bg:#0a0a0a;--fg:#f5f5f5;--mut:#9a9a9a;--ok:#22c55e;--bad:#ef4444;--nf:#f59e0b;--inf:#3f3f46}}
html,body{{margin:0;background:var(--bg);color:var(--fg);font-family:Inter,"Helvetica Neue",Arial,sans-serif;overflow:hidden}}
#stage{{width:1920px;height:1080px;position:relative;transform-origin:0 0}}
.scene{{position:absolute;inset:0;opacity:0;transition:opacity .6s;padding:60px 80px;box-sizing:border-box}}
.scene.on{{opacity:1}}
h1{{font-size:56px;font-weight:600;margin:0 0 12px}} .sub{{font-size:26px;color:var(--mut);margin:0 0 30px}}
.grid{{display:grid;grid-template-columns:repeat(10,1fr);gap:14px;width:1300px}}
.tile{{height:64px;border-radius:10px;background:#1a1a1a;opacity:.15;transform:scale(.8);transition:all .25s;display:flex;align-items:center;justify-content:center;font-size:15px;color:#000;font-weight:700}}
.tile.lit{{opacity:1;transform:scale(1)}} .correct{{background:var(--ok)}} .wrong{{background:var(--bad)}} .notfound{{background:var(--nf)}} .infra{{background:var(--inf);color:#aaa}}
.legend{{margin-top:24px;font-size:22px;color:var(--mut)}} .legend span{{display:inline-block;width:18px;height:18px;border-radius:4px;margin:0 8px 0 24px;vertical-align:-2px}}
.pair{{display:flex;gap:60px;margin-top:10px}}
.shot{{position:relative;width:800px;height:780px;background-repeat:no-repeat;background-size:2200px auto;border:2px solid #333;border-radius:12px;overflow:hidden}}
.box{{position:absolute;border:6px solid;border-radius:8px;opacity:0;transition:opacity .4s}} .box.on{{opacity:1}}
.box.bad{{border-color:var(--bad);box-shadow:0 0 30px var(--bad)}} .box.good{{border-color:var(--ok);box-shadow:0 0 30px var(--ok)}}
.cap{{font-size:34px;font-weight:700;margin-top:16px;opacity:0;transition:opacity .4s}} .cap.on{{opacity:1}} .cap.bad{{color:var(--bad)}} .cap.good{{color:var(--ok)}}
.lbl{{font-size:28px;color:var(--mut);margin-bottom:10px}}
.click{{position:absolute;width:40px;height:40px;margin:-20px 0 0 -20px;border-radius:50%;border:5px solid #60a5fa;opacity:0}}
.click.go{{animation:ping 1.2s ease-out 2}}
@keyframes ping{{0%{{opacity:1;transform:scale(.4)}}100%{{opacity:0;transform:scale(3)}}}}
.board{{position:absolute;left:80px;right:80px;bottom:70px}}
.brow{{display:flex;align-items:center;gap:26px;font-size:34px;margin:22px 0}} .bname{{width:260px}}
.dots{{display:flex;gap:14px}} .dot{{width:38px;height:38px;border-radius:50%;background:#222;transition:background .2s}}
.bstat{{color:var(--mut);font-size:30px}}
.final{{font-size:40px;margin-top:30px}}
</style></head><body><div id="stage">

<section class="scene" id="s0"><h1>{len(runs)} real-browser runs inside Daytona sandboxes</h1>
<p class="sub">q1 "RTX 4090 that won't be interrupted" · styled pricing page · A = original tabs (10 reps/model), C = explicit layout (5 reps/model)</p>
<div class="grid" id="grid"></div>
<div class="legend"><span class="correct"></span>correct<span class="wrong"></span>confident wrong<span class="notfound"></span>not found<span class="infra"></span>infra (excluded, {n_infra})</div></section>

<section class="scene" id="s1"><h1>gpt-oss 20B · same question, two layouts</h1>
<div class="pair">
 <div><div class="lbl">A · original tabs (Preemptible shown)</div><div class="shot" style="background-image:url('{fr(g_a, 0)}');background-position:0 -{CROP_Y * 2}px">
   <div class="box bad" id="b1" style="left:{A_PRICE[0]*2}px;top:{A_PRICE[1]*2}px;width:{A_PRICE[2]*2}px;height:{A_PRICE[3]*2}px"></div></div>
   <div class="cap bad" id="c1">answered ${g_ans.get('usd_per_hour')} '{str(g_ans.get('pricing_type')).replace('_', '-')}' ✗ (actual $0.99)</div></div>
 <div><div class="lbl">C · explicit labels + FAQ</div><div class="shot" style="background-image:url('{fr(g_c, 0)}');background-position:0 -{CROP_Y * 2}px">
   <div class="box good" id="b2" style="left:{C_PRICE[0]*2}px;top:{C_PRICE[1]*2}px;width:{C_PRICE[2]*2}px;height:{C_PRICE[3]*2}px"></div></div>
   <div class="cap good" id="c2">answered $0.99 on-demand ✓</div></div>
</div></section>

<section class="scene" id="s2"><h1>Claude · clicks the On-demand tab first</h1>
<div class="pair">
 <div><div class="lbl" id="cl">step 1 · open_page → Preemptible tab shown</div>
  <div class="shot" id="cshot" style="background-image:url('{fr(c_a, 0)}');background-position:0 -{CROP_Y * 2}px">
   <div class="click" id="ck" style="left:{OD_TAB[0]*2}px;top:{OD_TAB[1]*2}px"></div>
   <div class="box good" id="b3" style="left:{A_PRICE[0]*2}px;top:{A_PRICE[1]*2}px;width:{A_PRICE[2]*2}px;height:{A_PRICE[3]*2}px"></div></div>
  <div class="cap good" id="c3">click("On-demand") → answered $0.99 on-demand ✓</div></div>
 <div style="font-size:34px;line-height:1.5;padding-top:80px;color:var(--mut)">On layout A the right price is<br>one click away.<br><br>
  <b style="color:var(--fg)">Clicked → correct {allA['correct_given_clicked']['k']}/{allA['correct_given_clicked']['n']}</b><br>
  <b style="color:var(--fg)">No click → correct {allA['correct_given_no_click']['k']}/{allA['correct_given_no_click']['n']}</b></div>
</div></section>

<section class="scene" id="s3"><h1>Layout A · per model (each dot = one run)</h1>
<div class="board" id="board"></div></section>
</div>
<script>
const TILES = {json.dumps(tile_data)};
const BOARD = {json.dumps(board)};
const FINAL = {json.dumps(f"A: {allA['correct_rate']['k']}/{allA['correct_rate']['n']} correct, {allA['confident_wrong_rate']['k']}/{allA['confident_wrong_rate']['n']} confident wrong  ·  C: {allC['correct_rate']['k']}/{allC['correct_rate']['n']} correct")};
const F2 = {json.dumps(fr(c_a, next(i for i, t in enumerate(c_a['tool_calls']) if t['name'] == 'click')))};
const $ = id => document.getElementById(id);
function fit() {{ const s = Math.min(innerWidth / 1920, innerHeight / 1080); $("stage").style.transform = `scale(${{s}})`; }}
addEventListener("resize", fit); fit();
const grid = $("grid");
TILES.forEach(t => {{ const d = document.createElement("div"); d.className = "tile " + t.v; d.textContent = t.l; grid.appendChild(d); }});
const board = $("board");
BOARD.forEach(b => {{
  board.insertAdjacentHTML("beforeend", `<div class="brow"><div class="bname">${{b.name}}</div><div class="dots">${{b.dots.map(v => `<div class="dot" data-v="${{v}}"></div>`).join("")}}</div>
  <div class="bstat" style="opacity:0">clicked ${{b.clicked}} · confident-wrong ${{b.cw}}</div></div>`);
}});
board.insertAdjacentHTML("beforeend", `<div class="final" style="opacity:0">${{FINAL}}</div>`);
const COL = {{correct: "var(--ok)", wrong: "var(--bad)", notfound: "var(--nf)", infra: "var(--inf)"}};
const T = [];
const at = (s, f) => T.push(setTimeout(f, s * 1000));
function scene(id) {{ document.querySelectorAll(".scene").forEach(s => s.classList.toggle("on", s.id === id)); }}
function play() {{
  T.forEach(clearTimeout); T.length = 0;
  document.querySelectorAll(".lit,.on").forEach(e => e.classList.remove("lit", "on"));
  $("cshot").style.backgroundImage = `url('{fr(c_a, 0)}')`; $("cl").textContent = "step 1 · open_page → Preemptible tab shown";
  document.querySelectorAll(".dot").forEach(d => d.style.background = "#222");
  document.querySelectorAll(".bstat,.final").forEach(d => d.style.opacity = 0);
  scene("s0");
  [...grid.children].forEach((t, i) => at(0.3 + i * 0.075, () => t.classList.add("lit")));
  at(5, () => scene("s1")); at(7, () => $("b1").classList.add("on")); at(8, () => $("c1").classList.add("on"));
  at(12, () => $("b2").classList.add("on")); at(13, () => $("c2").classList.add("on"));
  at(20, () => scene("s2")); at(22, () => {{ const c = $("ck"); c.classList.remove("go"); void c.offsetWidth; c.classList.add("go"); }});
  at(24.5, () => {{ $("cshot").style.backgroundImage = `url('${{F2}}')`; $("cl").textContent = 'step 2 · click("On-demand") → On-demand prices'; }});
  at(25.5, () => $("b3").classList.add("on")); at(26.5, () => $("c3").classList.add("on"));
  at(30, () => scene("s3"));
  const rows = [...board.querySelectorAll(".brow")];
  rows.forEach((row, ri) => {{
    row.querySelectorAll(".dot").forEach((d, di) => at(30.5 + ri * 2 + di * 0.15, () => d.style.background = COL[d.dataset.v]));
    at(30.5 + ri * 2 + 1.6, () => row.querySelector(".bstat").style.opacity = 1);
  }});
  at(39, () => board.querySelector(".final").style.opacity = 1);
}}
play();
addEventListener("keydown", e => {{ if (e.key === " " || e.key === "r") play(); if (e.key === "f") document.documentElement.requestFullscreen(); }});
</script></body></html>"""
(ROOT / "results/stage.html").write_text(doc)
print("wrote results/stage.html", {"gpt_oss_A": g_a["run_id"], "gpt_oss_C": g_c["run_id"], "claude_A": c_a["run_id"]})

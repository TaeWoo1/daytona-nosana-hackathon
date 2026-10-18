"""results/summary.json + graded.jsonl + runs*.jsonl -> results/dashboard.html (static, no CDN)

usage: .venv/bin/python src/report.py [runs.jsonl ...]
"""
import html
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
S = json.loads((ROOT / "results/summary.json").read_text())
G = [json.loads(l) for l in open(ROOT / "results/graded.jsonl")]
RUN_FILES = sys.argv[1:] or [str(ROOT / "results/runs.jsonl")]
RUNS = [{**json.loads(l), "_set": Path(f).stem} for f in RUN_FILES for l in open(f) if l.strip()]
for _r in RUNS:  # the earlier v2 batch (n=3) is kept but reported separately from the headline v2 batch (n10 file)
    if _r["_set"] == "runs_rendered_v2":
        _r["mode"] = "rendered_text_v2_n3"

LAYOUT_LABEL = {"A_original": "A · original (tabs)", "B_explicit": "B · explicit table",
                "C_faq_structured": "C · B + FAQ + JSON-LD", "NOPAGE": "No page (memory)"}
LAYOUTS = ["A_original", "B_explicit", "C_faq_structured", "NOPAGE"]
MODEL_ORDER = ["qwen3.5-9b", "gpt-oss-20b", "gemma4-26b", "claude", "openai"]
MODEL_LABEL = {"qwen3.5-9b": "Qwen 3.5 9B<br><small>Nosana</small>", "gpt-oss-20b": "gpt-oss 20B<br><small>Nosana</small>",
               "gemma4-26b": "Gemma 4 26B<br><small>Nosana</small>", "claude": "Claude<br><small>API</small>",
               "openai": "OpenAI<br><small>API</small>"}
QLABEL = {"q1_gpu_ondemand": "q1 GPU not interrupted", "q2_cpu_sandbox_cost": "q2 CPU sandbox cost",
          "q3_signup": "q3 card / free credit", "q4_billing": "q4 billing unit", "q5_windows": "q5 Windows price"}


def color(a):
    # red (0) -> amber -> green (1)
    if a is None:
        return "var(--empty)"
    h = int(a * 130)
    return f"hsl({h} 65% 42%)"


def heatmap(mode):
    cells = {(c["layout"], c["model"]): c for c in S["cells"] if c["mode"] in (mode, "none")}
    models = [m for m in MODEL_ORDER if any(k[1] == m for k in cells)]
    worst = {w["layout"]: w for w in S["worst_model"] if w["mode"] in (mode, "none")}
    rows = []
    for l in LAYOUTS:
        if not any(k[0] == l for k in cells):
            continue
        tds = []
        for m in models:
            c = cells.get((l, m))
            if not c:
                tds.append('<td class="cell" style="background:var(--empty)">–</td>')
                continue
            fc = c["field_counts"]
            tip = f"correct {fc.get('correct',0)} / not_found {fc.get('not_found',0)} / wrong {fc.get('wrong',0)} / invalid {fc.get('invalid',0)} fields"
            tds.append(f'<td class="cell" style="background:{color(c["field_accuracy"])}" title="{tip}">'
                       f'{c["field_accuracy"]*100:.0f}%<small>n={c["n_runs"]}</small></td>')
        w = worst.get(l)
        tds.append(f'<td class="cell worst" style="background:{color(w["worst_model_accuracy"])}">'
                   f'{w["worst_model_accuracy"]*100:.0f}%<small>{html.escape(w["worst_model"])}</small></td>')
        rows.append(f'<tr><th class="rowh">{LAYOUT_LABEL[l]}</th>{"".join(tds)}</tr>')
    head = "".join(f"<th>{MODEL_LABEL.get(m, m)}</th>" for m in models)
    return f'<table class="hm"><tr><th></th>{head}<th>Worst model</th></tr>{"".join(rows)}</table>'


def strict_q(mode, q):
    cells = {(c["layout"], c["model"]): c for c in S["cells_by_question"]
             if c["mode"] in (mode, "none") and c["question"] == q}
    models = [m for m in MODEL_ORDER if any(k[1] == m for k in cells)]
    rows = []
    for l in LAYOUTS:
        cs = [cells[(l, m)] for m in models if (l, m) in cells]
        if not cs:
            continue
        tds = "".join(
            f'<td class="cell" style="background:{color(cells[(l, m)]["fully_correct_rate"])}">'
            f'{cells[(l, m)]["fully_correct"]}/{cells[(l, m)]["n_runs"]}<small>wrong {cells[(l, m)]["any_wrong"]}</small></td>'
            if (l, m) in cells else '<td class="cell" style="background:var(--empty)">–</td>' for m in models)
        w = min(cs, key=lambda c: c["fully_correct_rate"])
        tds += (f'<td class="cell worst" style="background:{color(w["fully_correct_rate"])}">'
                f'{w["fully_correct_rate"]*100:.0f}%<small>{html.escape(w["model"])}</small></td>')
        rows.append(f'<tr><th class="rowh">{LAYOUT_LABEL[l]}</th>{tds}</tr>')
    head = "".join(f"<th>{MODEL_LABEL.get(m, m)}</th>" for m in models)
    return f'<table class="hm"><tr><th></th>{head}<th>Worst model</th></tr>{"".join(rows)}</table>'


def per_question(mode):
    bq = [b for b in S["by_question"] if b["mode"] in (mode, "none")]
    qs = sorted({b["question"] for b in bq})
    out = []
    for q in qs:
        bars = []
        for l in LAYOUTS:
            b = next((x for x in bq if x["question"] == q and x["layout"] == l), None)
            if not b:
                continue
            n = b["n_runs"]
            segs = "".join(
                f'<span class="seg {k}" style="width:{b.get(k,0)/n*100:.1f}%" title="{k} {b.get(k,0)}/{n}">'
                f'{b.get(k,0) if b.get(k,0) else ""}</span>'
                for k in ("correct", "not_found", "wrong", "invalid") if b.get(k, 0))
            bars.append(f'<div class="bar"><span class="bl">{LAYOUT_LABEL[l]}</span><span class="track">{segs}</span>'
                        f'<span class="bn">n={n}</span></div>')
        out.append(f'<div class="q"><h4>{QLABEL.get(q, q)}</h4>{"".join(bars)}</div>')
    return "".join(out)


def replay(mode):
    """q1, weakest model on A: show A vs C tool-call path for rep 0."""
    wa = next((w for w in S["worst_model"] if w["mode"] == mode and w["layout"] == "A_original"), None)
    if not wa:
        return ""
    m = wa["worst_model"]
    cols = []
    for l in ("A_original", "C_faq_structured"):
        r = next((r for r in RUNS if r["model"] == m and r["layout"] == l and r["question"] == "q1_gpu_ondemand"
                  and r["mode"] == mode and (not r.get("error") or "XML syntax error" in r["error"])), None)
        if not r:
            continue
        steps = "".join(f'<li><code>open_page("{html.escape(t["path"])}")</code> → {len(t["output"] or "")} chars, '
                        f'{t["sec"]}s in Daytona sandbox</li>' for t in r["tool_calls"])
        a = r.get("answer") or {}
        g = next(x for x in G if x["model"] == m and x["layout"] == l and x["question"] == r["question"]
                 and x["rep"] == r["rep"] and x["batch"] == r["batch"])
        verdict = "correct" if g["all_correct"] else ("wrong" if g["any_wrong"] else "not found / invalid")
        cols.append(f'<div class="rp"><h4>{LAYOUT_LABEL[l]}</h4><ol>{steps or "<li>(no tool call)</li>"}</ol>'
                    f'<p><b>Answer:</b> {html.escape(json.dumps({k: a.get(k) for k in ("usd_per_hour", "pricing_type")}))}'
                    f' <span class="tag {verdict.split()[0]}">{verdict}</span></p>'
                    f'<p class="quote">“{html.escape(str(a.get("evidence_quote", ""))[:200])}”</p></div>')
    return (f'<p>Model: <b>{html.escape(m)}</b> (worst on layout A in this mode), question q1, first logged run per layout. '
            f'Gold: $0.99/h on-demand.</p><div class="rps">{"".join(cols)}</div>')


modes = sorted({c["mode"] for c in S["cells"] if c["mode"] != "none"})
MODE_LABEL = {"html_text": "Reader mode: html_text (all HTML text, incl. hidden tab panel — like a crawler)",
              "visible_text": "Reader mode: visible_text (hidden elements dropped — static approximation of a browser view)",
              "rendered_text": "Reader mode: rendered_text (real Chromium in the Daytona sandbox, inner_text + click tool) on the plain mirror sites (v1) — q1 only, layouts A and C",
              "rendered_text_v2_n3": "Reader mode: rendered_text on the styled sites (v2), first batch n=3 per cell — kept for reference",
              "rendered_text_v2": "Reader mode: rendered_text on the styled sites (v2: dark theme + pill GPU toggle like the real page) — HEADLINE batch, q1 only, A n=10 / C n=5 per model"}
sections = []
for mode in modes:
    sections.append(f"""
<section><h2>{MODE_LABEL.get(mode, mode)}</h2>
<h3>q1 "RTX 4090 that won't be interrupted": fully correct runs (gold $0.99/h on-demand)</h3>
<p class="note">Cell = runs with every field correct / runs; "wrong" = runs with a confident wrong value.</p>
{strict_q(mode, "q1_gpu_ondemand")}
<h3>Field accuracy by layout × reader model (all 5 questions)</h3>
<p class="note">Cell = mean share of answer fields matching gold (code-graded). n = runs (questions × reps). Last column = accuracy of the weakest model for that layout.</p>
{heatmap(mode)}
<h3>Which fact breaks</h3>
<p class="note">Per question, all models pooled: runs fully correct / not found / any wrong value / invalid JSON.</p>
<div class="legend"><span class="seg correct">correct</span><span class="seg not_found">not found</span><span class="seg wrong">wrong</span><span class="seg invalid">invalid</span></div>
{per_question(mode)}
<h3>Path replay</h3>
{replay(mode)}
</section>""")

sys.path.insert(0, str(ROOT / "src"))
import grade as _grade  # noqa: E402

RENDERED = [r for r in RUNS if str(r.get("mode")).startswith("rendered_text") and r.get("run_id")
            and (not r.get("error") or "XML syntax error" in r["error"]) and not any("render.py" in (t.get("output") or "") and "Traceback" in (t.get("output") or "")
                for t in r.get("tool_calls", []))]
VER_LABEL = {"v1": "v1 plain mirror", "v2": "v2 styled n=3", "v2·n10": "v2 styled, headline batch (A n=10, C n=5)"}


def replay_section():
    if not RENDERED:
        return ""
    data = []
    for r in RENDERED:
        g = _grade.grade(r)
        verdict = "correct" if g["all_correct"] else ("wrong" if g["any_wrong"] else
                                                      ("invalid" if "invalid" in g["fields"].values() else "not_found"))
        a = r.get("answer") or {}
        data.append({
            "id": r["run_id"], "ver": r.get("site_version", "v1") + ("·n10" if r.get("_set") == "runs_rendered_v2_n10" else ""), "model": r["model"], "layout": r["layout"], "rep": r["rep"],
            "steps": [{"tool": t["name"], "arg": t["path"], "frame": t.get("frame"), "sec": t["sec"],
                       "out": (t["output"] or "")[:400]} for t in r["tool_calls"]],
            "answer": {k: a.get(k) for k in ("usd_per_hour", "pricing_type", "not_found")},
            "quote": str(a.get("evidence_quote", ""))[:200], "verdict": verdict, "latency": r["latency_sec"],
            "fields": g["fields"],
        })
    pairs = sorted({(d["ver"], d["model"], d["rep"]) for d in data},
                   key=lambda x: ({"v2·n10": 0, "v2": 1}.get(x[0], 2), MODEL_ORDER.index(x[1]) if x[1] in MODEL_ORDER else 9, x[2]))
    # featured defaults (headline batch): gpt-oss with A wrong + C correct, Claude with A clicked -> correct
    by = {(d["ver"], d["model"], d["rep"], d["layout"]): d for d in data}

    def feat(model, ok):
        for v, m, rp in pairs:
            a, c = by.get((v, m, rp, "A_original")), by.get((v, m, rp, "C_faq_structured"))
            if v == "v2·n10" and m == model and a and c and ok(a, c):
                return (v, m, rp)
    featured = [f for f in (feat("gpt-oss-20b", lambda a, c: a["verdict"] == "wrong" and c["verdict"] == "correct"),
                            feat("claude", lambda a, c: a["verdict"] == "correct" and any(st["tool"] == "click" for st in a["steps"])))
                if f]
    label = {"gpt-oss-20b": "A wrong, C correct", "claude": "A clicked → correct"}
    opts = "".join(f'<option value="{m}|{rep}|{v}">★ {html.escape(m)} · rep {rep} · {label[m]} ({VER_LABEL.get(v, v)})</option>'
                   for v, m, rep in featured)
    opts += "".join(f'<option value="{m}|{rep}|{v}">{VER_LABEL.get(v, v)} · {html.escape(m)} · rep {rep}</option>' for v, m, rep in pairs)
    js_data = json.dumps(data).replace("</", "<\\/")
    return f"""
<section id="replay"><h2>Replay · rendered_text (real browser in Daytona)</h2>
<p class="note">q1 "RTX 4090 that won't be interrupted" (gold $0.99/h on-demand). Each frame is a full-page screenshot taken inside the Daytona sandbox after that tool call
(results/frames/). Pick a site version, model and rep; step through layout A and C side by side. v1 = plain mirror HTML, v2 = styled like the real page.</p>
<label>Run: <select id="rpSel">{opts}</select></label> <button id="rpPlay">▶ Autoplay</button>
<div class="rpgrid"><div class="rpane" data-layout="A_original"></div><div class="rpane" data-layout="C_faq_structured"></div></div>
<script>
const RP = {js_data};
const LBL = {{"A_original": "A · original (tabs)", "C_faq_structured": "C · B + FAQ + JSON-LD"}};
function esc(s) {{ return String(s).replace(/[&<>"]/g, c => ({{"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}})[c]); }}
function renderPane(pane, run, i) {{
  const n = run.steps.length;           // steps 0..n-1 = tool calls, step n = final answer
  i = Math.max(0, Math.min(i, n));
  pane.dataset.i = i;
  const lastFrame = run.steps.filter(s => s.frame).map(s => s.frame).pop();
  const frame = i < n ? run.steps[i].frame : lastFrame;
  const list = run.steps.map((s, k) =>
    `<li class="${{k === i ? 'cur' : ''}}"><code>${{esc(s.tool)}}("${{esc(s.arg)}}")</code> <small>${{s.sec}}s</small></li>`).join("")
    + `<li class="${{i === n ? 'cur' : ''}}"><b>final answer</b></li>`;
  const detail = i < n
    ? `<pre>${{esc(run.steps[i].out)}}</pre>`
    : `<p><b>Answer:</b> ${{esc(JSON.stringify(run.answer))}}</p><p class="quote">“${{esc(run.quote)}}”</p>
       <p><span class="tag ${{run.verdict}}">${{run.verdict}}</span> <small>fields: ${{esc(JSON.stringify(run.fields))}} · ${{run.latency}}s total</small></p>`;
  const big = i === n ? " big" : "";
  pane.innerHTML = `<h4>${{LBL[run.layout]}} <span class="tag ${{run.verdict}}${{big}}">${{run.verdict}}</span></h4>
    <div class="rpin"><div class="frame">${{frame ? `<a href="${{esc(frame)}}" target="_blank" title="open full size"><img src="${{esc(frame)}}" alt="screenshot step ${{i + 1}}"></a>` : '<p class="note">(no frame)</p>'}}</div>
    <div class="steps"><div class="nav"><button data-d="-1">◀ prev</button> step ${{i + 1}}/${{n + 1}} <button data-d="1">next ▶</button></div>
    <ol>${{list}}</ol>${{detail}}</div></div>`;
  pane.querySelectorAll("button").forEach(b => b.onclick = () => renderPane(pane, run, i + Number(b.dataset.d)));
}}
function show() {{
  const [m, rep, ver] = document.getElementById("rpSel").value.split("|");
  document.querySelectorAll(".rpane").forEach(p => {{
    const run = RP.find(r => r.model === m && String(r.rep) === rep && r.ver === ver && r.layout === p.dataset.layout);
    if (run) renderPane(p, run, 0); else p.innerHTML = "<p class='note'>(no run)</p>";
  }});
}}
let timer = null;
function stopPlay() {{ if (timer) clearInterval(timer); timer = null; document.getElementById("rpPlay").textContent = "▶ Autoplay"; }}
function autoplay() {{
  if (timer) return stopPlay();
  show();  // both panes back to step 1
  document.getElementById("rpPlay").textContent = "■ Stop";
  timer = setInterval(() => {{
    let moving = false;
    document.querySelectorAll(".rpane").forEach(p => {{
      const run = currentRun(p);
      if (!run) return;
      const i = Number(p.dataset.i);
      if (i < run.steps.length) {{ renderPane(p, run, i + 1); moving = true; }}
    }});
    if (!moving) stopPlay();
  }}, 1500);
}}
function currentRun(p) {{
  const [m, rep, ver] = document.getElementById("rpSel").value.split("|");
  return RP.find(r => r.model === m && String(r.rep) === rep && r.ver === ver && r.layout === p.dataset.layout);
}}
document.getElementById("rpSel").onchange = () => {{ stopPlay(); show(); }};
document.getElementById("rpPlay").onclick = autoplay; show();
</script>
</section>"""


n_sb = len({r.get("sandbox_id") for r in RUNS if r.get("sandbox_id")})
n_tool = sum(r["n_tool_calls"] for r in RUNS)
doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AgentReadable Results</title>
<style>
:root{{--bg:#fafaf8;--fg:#1d1d1b;--mut:#6b6b66;--line:#ddd;--empty:#e8e8e4;--card:#fff}}
@media (prefers-color-scheme: dark){{:root{{--bg:#151514;--fg:#ecebe6;--mut:#a3a29c;--line:#333;--empty:#2a2a28;--card:#1d1d1b}}}}
body{{background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif;max-width:1100px;margin:auto;padding:16px}}
h1{{margin-bottom:0}} .sub{{color:var(--mut);margin-top:4px}} .note{{color:var(--mut);font-size:13px}}
section{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px;margin:20px 0}}
.hm{{border-collapse:separate;border-spacing:4px;width:100%}} .hm th{{font-weight:600;font-size:13px}}
.rowh{{text-align:left;white-space:nowrap}} .cell{{color:#fff;text-align:center;font-size:20px;font-weight:700;border-radius:6px;padding:10px 4px}}
.cell small{{display:block;font-size:11px;font-weight:400;opacity:.85}} .worst{{outline:3px solid var(--fg)}}
.q{{margin:10px 0}} .q h4{{margin:6px 0}} .bar{{display:flex;align-items:center;gap:8px;margin:3px 0;font-size:13px}}
.bl{{width:190px;flex:none}} .bn{{color:var(--mut);width:50px}} .track{{flex:1;display:flex;height:20px;border-radius:4px;overflow:hidden;background:var(--empty)}}
.seg{{display:inline-flex;align-items:center;justify-content:center;color:#fff;font-size:11px;padding:0 4px}}
.correct{{background:hsl(130 55% 38%)}} .not_found{{background:hsl(40 80% 45%)}} .wrong{{background:hsl(0 65% 48%)}} .invalid{{background:#888}}
.legend .seg{{padding:2px 8px;margin-right:4px;border-radius:3px}}
.rps{{display:grid;grid-template-columns:1fr 1fr;gap:12px}} .rp{{border:1px solid var(--line);border-radius:8px;padding:10px}}
.quote{{color:var(--mut);font-style:italic;font-size:13px}} .tag{{padding:1px 6px;border-radius:4px;color:#fff;font-size:12px}}
.tag.not{{background:hsl(40 80% 45%)}}
.rpgrid{{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:10px}} .rpane{{border:1px solid var(--line);border-radius:8px;padding:10px;min-width:0}}
.rpin{{display:grid;grid-template-columns:minmax(0,1.3fr) minmax(0,1fr);gap:10px}} .frame{{max-height:560px;overflow:auto;border:1px solid var(--line);border-radius:6px;background:#fff}}
.frame img{{width:100%;display:block}} .steps ol{{padding-left:20px;font-size:13px}} .steps li.cur{{font-weight:700;background:var(--empty);border-radius:4px}}
.steps pre{{white-space:pre-wrap;font-size:11px;max-height:300px;overflow:auto;background:var(--empty);padding:6px;border-radius:4px}}
.tag.big{{font-size:20px;padding:4px 14px;box-shadow:0 0 0 4px var(--fg)}}
#rpPlay{{font:inherit;padding:4px 12px;cursor:pointer;margin-left:8px}}
.nav button{{font:inherit;padding:2px 8px;cursor:pointer}} .tag.correct{{background:hsl(130 55% 38%)}} .tag.wrong{{background:hsl(0 65% 48%)}} .tag.not_found{{background:hsl(40 80% 45%)}} .tag.invalid{{background:#888}}
@media (max-width:1000px){{.rpgrid{{grid-template-columns:1fr}}}}
@media (max-width:700px){{.rpin{{grid-template-columns:1fr}} .rps{{grid-template-columns:1fr}} .bl{{width:110px}} .cell{{font-size:14px}}}}
</style></head><body>
<h1>AgentReadable</h1>
<p class="sub">How accurately does each AI reader get the facts from the real Daytona pricing page (captured 2026-10-18 15:35 KST), by layout and by model?</p>
<p class="note">{S['n_runs']} graded runs · {n_tool} tool calls (open_page / click) executed inside {n_sb} Daytona sandboxes · readers: 3 open-weight models on Nosana GPUs + Claude via API (OpenAI configured but excluded: no API credits) · temperature 0 · small n, results are "in these runs", not proof.</p>
{''.join(sections)}
{replay_section()}
<p class="note">Generated by src/report.py from {', '.join(html.escape(str(Path(f).name)) for f in RUN_FILES)}, results/graded.jsonl, results/summary.json.</p>
</body></html>"""
(ROOT / "results/dashboard.html").write_text(doc)
print("wrote results/dashboard.html")

# markdown tables for README (numbers straight from summary.json)
md = []
for mode in modes:
    cells = {(c["layout"], c["model"]): c for c in S["cells"] if c["mode"] in (mode, "none")}
    models = [m for m in MODEL_ORDER if any(k[1] == m for k in cells)]
    worst = {w["layout"]: w for w in S["worst_model"] if w["mode"] in (mode, "none")}
    md.append(f"### mode: {mode}\n")
    md.append("| layout | " + " | ".join(models) + " | worst model |")
    md.append("|---" * (len(models) + 2) + "|")
    for l in LAYOUTS:
        if l not in worst:
            continue
        row = [f"{cells[(l, m)]['field_accuracy']*100:.0f}% (n={cells[(l, m)]['n_runs']})" if (l, m) in cells else "–"
               for m in models]
        w = worst[l]
        md.append(f"| {l} | " + " | ".join(row) + f" | {w['worst_model_accuracy']*100:.0f}% ({w['worst_model']}) |")
    md.append("")
    md.append("| layout | question | correct | not_found | wrong | invalid | n |")
    md.append("|---|---|---|---|---|---|---|")
    for b in S["by_question"]:
        if b["mode"] in (mode, "none"):
            md.append(f"| {b['layout']} | {b['question']} | {b.get('correct',0)} | {b.get('not_found',0)} | "
                      f"{b.get('wrong',0)} | {b.get('invalid',0)} | {b['n_runs']} |")
    md.append("")
md.append(f"Excluded infra errors: {S.get('excluded_infra_errors')}")
md.append("")
md.append("### Browser behaviour (rendered_text runs): click vs outcome, per run set × layout × model")
md.append("")
if S.get("behavior_headline"):
    md.append(f"**{S['behavior_headline']}**")
    md.append("")
md.append("Each cell is k/n (rate). confident_wrong = a value was asserted and it was wrong.")
md.append("")
md.append("| run set | layout | model | click | correct | confident_wrong | not_found | invalid | correct given clicked | correct given no click |")
md.append("|---|---|---|---|---|---|---|---|---|---|")
fr = lambda x: f"{x['k']}/{x['n']} ({x['rate']*100:.0f}%)" if x["n"] else "0/0 (–)"  # noqa: E731
for b_ in S.get("behavior", []):
    md.append(f"| {b_['run_set']} | {b_['layout']} | {b_['model']} | " + " | ".join(fr(b_[k]) for k in (
        "click_rate", "correct_rate", "confident_wrong_rate", "not_found_rate", "invalid_rate",
        "correct_given_clicked", "correct_given_no_click")) + " |")
(ROOT / "results/results_table.md").write_text("\n".join(md))
print("wrote results/results_table.md")

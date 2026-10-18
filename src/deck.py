"""results/summary.json (+ runs) -> deck/deck.html -> deck/deck.pdf (headless Chrome). Every number comes from results/.

usage: .venv/bin/python src/deck.py results/runs.jsonl results/runs_visible.jsonl
"""
import html
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
S = json.loads((ROOT / "results/summary.json").read_text())
RUN_FILES = sys.argv[1:] or [str(ROOT / "results/runs.jsonl")]
RUNS = [{**json.loads(l), "_set": Path(f).stem} for f in RUN_FILES for l in open(f) if l.strip()]
for _r in RUNS:  # earlier v2 batch (n=3) kept but not used for the headline
    if _r["_set"] == "runs_rendered_v2":
        _r["mode"] = "rendered_text_v2_n3"
sys.path.insert(0, str(ROOT / "src"))
import grade as _grade  # noqa: E402
OK_RUNS = [r for r in RUNS if not _grade.infra_reason(r)]

LL = {"A_original": "A · original (tabs)", "B_explicit": "B · explicit table", "C_faq_structured": "C · + FAQ + JSON-LD",
      "NOPAGE": "No page (memory)"}
LAYOUTS = ["A_original", "B_explicit", "C_faq_structured", "NOPAGE"]
MODELS = ["qwen3.5-9b", "gpt-oss-20b", "gemma4-26b", "claude", "openai"]
ML = {"qwen3.5-9b": "Qwen 3.5 9B", "gpt-oss-20b": "gpt-oss 20B", "gemma4-26b": "Gemma 4 26B", "claude": "Claude", "openai": "OpenAI"}
QL = {"q1_gpu_ondemand": "q1 GPU not interrupted", "q2_cpu_sandbox_cost": "q2 CPU sandbox cost",
      "q3_signup": "q3 card / free credit", "q4_billing": "q4 billing unit", "q5_windows": "q5 Windows price"}


def col(a):
    return f"hsl({int(a * 130)} 65% 40%)"


def heat(mode):
    cells = {(c["layout"], c["model"]): c for c in S["cells"] if c["mode"] in (mode, "none")}
    ms = [m for m in MODELS if any(k[1] == m for k in cells)]
    worst = {w["layout"]: w for w in S["worst_model"] if w["mode"] in (mode, "none")}
    rows = []
    for l in LAYOUTS:
        if l not in worst:
            continue
        tds = "".join(
            f'<td style="background:{col(cells[(l, m)]["field_accuracy"])}">{cells[(l, m)]["field_accuracy"]*100:.0f}%'
            f'<small>n={cells[(l, m)]["n_runs"]}</small></td>' if (l, m) in cells else "<td>–</td>" for m in ms)
        w = worst[l]
        rows.append(f'<tr><th>{LL[l]}</th>{tds}<td class="w" style="background:{col(w["worst_model_accuracy"])}">'
                    f'{w["worst_model_accuracy"]*100:.0f}%<small>{ML.get(w["worst_model"], w["worst_model"])}</small></td></tr>')
    return (f'<table class="hm"><tr><th></th>{"".join(f"<th>{ML.get(m, m)}</th>" for m in ms)}<th>Worst model</th></tr>'
            f'{"".join(rows)}</table>')


def strict_q(mode, q):
    cells = {(c["layout"], c["model"]): c for c in S["cells_by_question"] if c["mode"] in (mode, "none") and c["question"] == q}
    ms = [m for m in MODELS if any(k[1] == m for k in cells)]
    rows = []
    for l in LAYOUTS:
        cs = [cells[(l, m)] for m in ms if (l, m) in cells]
        if not cs:
            continue
        tds = "".join(f'<td style="background:{col(cells[(l, m)]["fully_correct_rate"])}">{cells[(l, m)]["fully_correct"]}/{cells[(l, m)]["n_runs"]}'
                      f'<small>wrong {cells[(l, m)]["any_wrong"]}</small></td>' if (l, m) in cells else "<td>–</td>" for m in ms)
        w = min(cs, key=lambda c: c["fully_correct_rate"])
        rows.append(f'<tr><th>{LL[l]}</th>{tds}<td class="w" style="background:{col(w["fully_correct_rate"])}">'
                    f'{w["fully_correct_rate"]*100:.0f}%<small>{ML.get(w["model"], w["model"])}</small></td></tr>')
    return (f'<table class="hm"><tr><th></th>{"".join(f"<th>{ML.get(m, m)}</th>" for m in ms)}<th>Worst model</th></tr>'
            f'{"".join(rows)}</table>')


def qbars(mode, only=None):
    out = []
    for q in sorted({b["question"] for b in S["by_question"]}):
        if only and q not in only:
            continue
        bars = []
        for l in LAYOUTS:
            b = next((x for x in S["by_question"] if x["question"] == q and x["layout"] == l
                      and x["mode"] in (mode, "none")), None)
            if not b:
                continue
            n = b["n_runs"]
            segs = "".join(f'<span class="s {k}" style="width:{b.get(k,0)/n*100:.1f}%">{b.get(k,0) or ""}</span>'
                           for k in ("correct", "not_found", "wrong", "invalid") if b.get(k, 0))
            bars.append(f'<div class="bar"><span class="bl">{LL[l]}</span><span class="tr">{segs}</span><span class="bn">n={n}</span></div>')
        out.append(f'<div class="q"><b>{QL[q]}</b>{"".join(bars)}</div>')
    return "".join(out)


def example(mode, layout, model):
    r = next((r for r in OK_RUNS if r["mode"] == mode and r["layout"] == layout and r["model"] == model
              and r["question"] == "q1_gpu_ondemand"), None)
    if not r:
        return "<p>(no run)</p>"
    a = r.get("answer") or {}
    ok = a.get("usd_per_hour") == 0.99 and a.get("pricing_type") == "on_demand"
    tag = '<span class="tag ok">correct</span>' if ok else '<span class="tag bad">wrong</span>'
    return (f'<div class="ex"><div class="exh">{ML[model]} · {LL[layout]} · {mode} {tag}</div>'
            f'<p>Answer: <b>{a.get("usd_per_hour")}</b> $/h, type <b>{html.escape(str(a.get("pricing_type")))}</b></p>'
            f'<p class="qt">“{html.escape(str(a.get("evidence_quote", ""))[:140])}”</p></div>')


n_runs = S["n_runs"]
n_sb = len({r.get("sandbox_id") for r in RUNS if r.get("sandbox_id")})
n_tool = sum(r["n_tool_calls"] for r in OK_RUNS)
tool_secs = [t["sec"] for r in OK_RUNS for t in r["tool_calls"]]
med_tool = sorted(tool_secs)[len(tool_secs) // 2] if tool_secs else 0
nosana_runs = sum(1 for r in OK_RUNS if r["model"] in ("qwen3.5-9b", "gpt-oss-20b", "gemma4-26b"))
modes = sorted({c["mode"] for c in S["cells"] if c["mode"] != "none"})
excl = S.get("excluded_infra_errors", {})

# --- main deck: 7 slides, dark, same tone as results/stage.html; appendix after ---
_hb = {(b["run_set"], b["layout"], b["model"]): b for b in S.get("behavior", [])}
HL = "runs_rendered_v2_n10"
_a, _c = _hb[(HL, "A_original", "ALL")], _hb[(HL, "C_faq_structured", "ALL")]
_k = lambda x: f"{x['k']}/{x['n']}"  # noqa: E731
_g = _hb[(HL, "A_original", "gpt-oss-20b")]
_np = [c for c in S["cells_by_question"] if c["layout"] == "NOPAGE" and c["question"] == "q1_gpu_ondemand"]
np_k, np_n = sum(c["fully_correct"] for c in _np), sum(c["n_runs"] for c in _np)
hl_runs = [r for r in RUNS if r["_set"] == HL]
hl_ok = [r for r in hl_runs if not _grade.infra_reason(r)]
hl_infra = len(hl_runs) - len(hl_ok)
D = ROOT / "deck"
# real page capture (data/raw/ref), GPU card area
subprocess.run(["sips", "-c", "1100", "2880", "--cropOffset", "500", "0", str(ROOT / "data/raw/ref/daytona_pricing_2026-10-18_screenshot.png"),
                "--out", str(D / "ref_crop.png")], check=True, capture_output=True)
# v2 screenshot GPU crop (pre-click) from the gpt-oss A run, and the inner_text that same reader got
ga = next(r for r in hl_ok if r["model"] == "gpt-oss-20b" and r["layout"] == "A_original" and r["tool_calls"][0].get("frame"))
subprocess.run(["sips", "-c", "400", "400", "--cropOffset", "625", "0", str(ROOT / "results" / ga["tool_calls"][0]["frame"]),
                "--out", str(D / "human_view.png")], check=True, capture_output=True)
_o = ga["tool_calls"][0]["output"]
_i = _o.find("GPU\n")
ai_view = "\n".join(x for x in _o[_i:_o.find("Memory", _i)].split("\n") if x.strip())
_ga = ga.get("answer") or {}
# stage.html scene capture (gpt-oss A vs C at ~14 s)
chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
subprocess.run([chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--window-size=1920,1080", "--virtual-time-budget=14000",
                f"--screenshot={D / 'stage_scene.png'}", f"file://{ROOT / 'results/stage.html'}"], check=True, capture_output=True, timeout=120)
subprocess.run(["sips", "-Z", "1600", str(D / "stage_scene.png")], check=True, capture_output=True)


def dots(layout):
    out = []
    for m in ["claude", "gemma4-26b", "qwen3.5-9b", "gpt-oss-20b"]:
        xs = [r for r in hl_ok if r["layout"] == layout and r["model"] == m]
        b = _hb[(HL, layout, m)]
        ds = "".join(f'<i class="d {_grade.outcome(_grade.grade(r))}"></i>' for r in xs)
        out.append(f'<div class="dr"><span class="dm">{ML[m]}</span><span class="ds">{ds}</span>'
                   f'<span class="dn">correct {_k(b["correct_rate"])} · clicked {_k(b["click_rate"])} · confident-wrong {_k(b["confident_wrong_rate"])}</span></div>')
    return "".join(out)


cu = {k: json.loads((ROOT / f"results/cu_aside/{k}/run.json").read_text()) for k in ("A_original", "A_original_gemma", "C_faq_structured")}
for k in ("A_original", "A_original_gemma"):
    subprocess.run(["cp", str(ROOT / f"results/cu_aside/{k}/step_3.png"), str(D / f"cu_{k}.png")], check=True)


def cu_line(k):
    j = cu[k]
    clicks = [s["input"] for s in j["steps"] if s["action"] == "click"]
    a = j.get("answer") or {}
    pts = ", ".join(f"({c['x']},{c['y']})" for c in clicks[:1])
    return (f"{html.escape(j['model'])}: {len(clicks)} click(s) at {pts or '–'}; "
            f"answer {html.escape(str(a.get('usd_per_hour')) if a else 'none')} · verdict {html.escape(str(j.get('verdict')))}")


slides = []
slides.append(f"""<section class="hook"><div class="hk"><p class="kick">AgentReadable</p>
<h1><span class="red">{_g['confident_wrong_rate']['k']}/{_g['confident_wrong_rate']['n']}</span> wrong price</h1>
<p class="big">"I need an RTX 4090 that won't be interrupted. How much per hour?"<br>gpt-oss 20B, reading a reproduction of this page in a real browser, answered <b class="red">$0.57</b> every time. The on-demand price is <b class="grn">$0.99</b>.</p>
<p class="url">github.com/TaeWoo1/daytona-nosana-hackathon · Daytona · Nosana</p></div>
<figure class="ref"><img src="ref_crop.png"><figcaption>daytona.io/pricing, captured 2026-10-18 (data/raw/ref). GPU table opens on <b>Preemptible</b>.</figcaption></figure>
<p class="note">gpt-oss 20B, layout A, q1, {_g['n_runs']} runs: confident-wrong {_k(_g['confident_wrong_rate'])}, clicked the tab {_k(_g['click_rate'])}. Source: results/summary.json → behavior ({HL}).</p></section>""")
slides.append(f"""<section><h2>Human view vs AI view</h2><div class="two">
<figure><img class="shot" src="human_view.png"><figcaption>Human: the pill toggle shows which price is which. Screenshot from Chromium in the Daytona sandbox.</figcaption></figure>
<div><pre class="pre">{html.escape(ai_view)}</pre><p class="cap">AI (gpt-oss 20B): the page's inner_text. "Preemptible" and "On-demand" are just two words; nothing says which list follows.
It answered <b class="red">${_ga.get('usd_per_hour')} "{html.escape(str(_ga.get('pricing_type')))}"</b>.</p></div></div>
<p class="note">Same run: {html.escape(ga['run_id'])} (results/runs_rendered_v2_n10.jsonl, frames in results/frames/). Layout A reproduces the real page structure; it is not the live site.</p></section>""")
slides.append(f"""<section><h2>{len(hl_runs)} real-browser runs in Daytona</h2><img class="stage" src="stage_scene.png">
<p class="cap">results/stage.html (40 s autoplay). Each run: a Daytona sandbox serves the layout, headless Chromium renders it, the reader can <code>click(text)</code>, every step is screenshotted.</p>
<p class="note">{len(hl_runs)} runs in {HL}: A 10 reps × 4 models, C 5 reps × 4 models. {hl_infra} excluded as infra (browser/exec errors, LOG.md); {len(hl_ok)} graded.</p></section>""")
slides.append(f"""<section><h2>Click the tab, or quote the wrong price</h2>
<h3>Layout A · original tabs</h3>{dots("A_original")}
<p class="hlx">Clicked → correct <b class="grn">{_k(_a['correct_given_clicked'])}</b> · no click → correct <b class="red">{_k(_a['correct_given_no_click'])}</b></p>
<div class="three"><div class="big2"><b class="grn">{_k(_c['correct_rate'])}</b><span>layout C (both prices labelled + FAQ + JSON-LD), all 4 models</span></div>
<div class="big2"><b class="red">{np_k}/{np_n}</b><span>No page (answer from memory), q1 fully correct = {np_k / np_n * 100:.0f}%</span></div></div>
<div class="lg"><i class="d correct"></i>correct <i class="d confident_wrong"></i>confident wrong <i class="d not_found"></i>not found</div>
<p class="note">Dots = graded runs, q1 ({HL}; No page from results/summary.json cells_by_question, mode none). Infra-excluded runs not shown.</p></section>""")
slides.append(f"""<section><h2>Computer use: pixels only <span class="n1">qualitative, n=1</span></h2><div class="two">
<figure><img class="shot" src="cu_A_original.png"><figcaption>Claude · layout A · step 3: {cu_line('A_original')}</figcaption></figure>
<figure><img class="shot" src="cu_A_original_gemma.png"><figcaption>Gemma 4 26B · layout A · step 3: {cu_line('A_original_gemma')}</figcaption></figure></div>
<p class="cap">Daytona computer-use desktop + recording API. Screenshot in, <code>click(x,y)</code> out. Claude hit the On-demand pill; Gemma said "switch to On-demand" but clicked the MI355X row. Layout C: {cu_line('C_faq_structured')}.
Coordinate miss may partly be Ollama image resizing (<b>unverified</b>).</p>
<p class="note">results/cu_aside/ (run.json, step PNGs, recording.mp4). One run per cell, not part of the headline numbers.</p></section>""")
slides.append(f"""<section><h2>Pipeline</h2>
<div class="flow"><div>Real page<br><small>+ gold answers</small></div><span>→</span><div>Layouts A / B / C<br><small>same facts</small></div><span>→</span>
<div class="dt">Daytona sandboxes<br><small>serve layout · Chromium · every tool call</small></div><span>→</span>
<div class="ns">Readers<br><small>3 open models on Nosana + Claude</small></div><span>→</span><div>Code grader<br><small>no LLM judge</small></div><span>→</span><div>Dashboard / stage</div></div>
<div class="three"><div class="big2"><b class="dtc">{n_sb}</b><span>Daytona sandboxes</span></div><div class="big2"><b class="dtc">{n_tool}</b><span>tool calls inside sandboxes (median {med_tool:.2f}s)</span></div>
<div class="big2"><b class="nsc">{nosana_runs}</b><span>graded runs on Nosana GPUs (Qwen 3.5 9B, gpt-oss 20B, Gemma 4 26B)</span></div></div>
<p class="note">Counts from results/runs*.jsonl, infra-excluded runs removed. {n_runs} graded runs in total (results/summary.json).</p></section>""")
slides.append(f"""<section><h2>Product, next steps, limits</h2><div class="two">
<div><h3>Product</h3><ul><li>Point it at your page: every AI reader × every layout, graded against your own answer key</li><li>Shows which fact breaks and for which model, with replayable screenshots</li></ul>
<h3>Next</h3><ul><li>Commerce pages, e.g. Naver Smart Store product pages: options and prices behind tabs and selectors</li><li>CI check: "does this layout change break any AI reader?"</li><li>Auto-fix suggestion per failing fact</li></ul></div>
<div><h3>Limits</h3><ul><li>One page, reproduced layouts (not the live site), q1 for the browser runs</li><li>Small n: A 10 reps/model, C 5 reps/model; directional, not proof</li><li>Computer use is n=1</li><li>OpenAI excluded (no API credits)</li></ul></div></div>
<p class="url2">github.com/TaeWoo1/daytona-nosana-hackathon · solo build, GitHub @TaeWoo1</p></section>""")
# --- appendix ---
slides.append(f"""<section class="jc"><h2><span class="apx">Appendix</span> Judging criteria</h2><div class="two">
<div class="card"><h3>Completeness</h3><ul><li>End-to-end: real page → gold → layouts → Daytona sandboxes → reader agents → code grader → dashboard, stage, deck</li>
<li>{n_runs} graded runs committed in results/, so every number can be checked without rerunning</li></ul></div>
<div class="card"><h3>Innovation</h3><ul><li>Measures comprehension accuracy (does the agent get the facts right?), not search visibility</li>
<li>Reading mode as a dimension: crawler text, static visible text, real browser with click, computer use (n=1)</li></ul></div>
<div class="card"><h3>Real-Life Problem Solving</h3><ul><li>Layout reproducing daytona.io/pricing: runs with no click were correct {_k(_a['correct_given_no_click'])}; {_k(_a['confident_wrong_rate'])} runs confident wrong</li>
<li>Same facts, explicit layout C: {_k(_c['correct_rate'])} correct</li></ul></div>
<div class="card"><h3>Sponsored Product Usage</h3><ul><li>Daytona: {n_sb} ephemeral sandboxes; Chromium + every tool call inside the sandbox; computer-use desktop + recording</li>
<li>Nosana: 3 open-weight models (Qwen 3.5 9B, gpt-oss 20B, Gemma 4 26B) on RTX 3090/4090</li></ul></div></div>
<p class="note">Rendered-browser numbers: results/runs_rendered_v2_n10.jsonl, q1, from summary.json → behavior.</p></section>""")
for mode in [m for m in modes[::-1] if m not in ("rendered_text", "rendered_text_v2_n3")]:
    slides.append(f"""<section><h2><span class="apx">Appendix</span> q1 · {mode}</h2>{strict_q(mode, "q1_gpu_ondemand")}
<p class="note">Cell = fully correct runs / runs (gold $0.99/h on-demand); "wrong" = runs with a confident wrong value. Source: results/summary.json (cells_by_question).</p></section>""")
for mode in [m for m in modes if not m.startswith("rendered_text")]:
    slides.append(f"""<section><h2><span class="apx">Appendix</span> All 5 questions · {mode}</h2>{heat(mode)}
<p class="note">Cell = mean share of answer fields matching gold. n = runs (5 questions × 3 reps). Outlined = weakest model per layout. Source: results/summary.json.</p></section>""")
slides.append(f"""<section><h2><span class="apx">Appendix</span> Limitations</h2><ul>
<li>One page; layouts are our reproductions of its structure (v1 plain mirror, v2 styled like the real page), not the live site.</li>
<li>visible_text is a static approximation. Real-browser runs: q1 only, layouts A and C.</li>
<li>Field accuracy gives partial credit; see the "fully correct" tables.</li>
<li>Excluded: {html.escape(json.dumps(excl))}.</li>
<li>Gold ambiguity: "first 5 GiB free" per sandbox or per org? (Both inside the q2 tolerance.)</li></ul></section>""")

doc = f"""<!doctype html><html><head><meta charset="utf-8"><title>AgentReadable deck</title><style>
@page{{size:1280px 720px;margin:0}} body{{margin:0;font:22px/1.45 Inter,system-ui,sans-serif;color:#ededed;background:#0a0a0a}}
section{{width:1280px;height:720px;box-sizing:border-box;padding:48px 64px;page-break-after:always;overflow:hidden;position:relative;background:#0a0a0a}}
h1{{font-size:96px;margin:10px 0 18px;line-height:1}} h2{{font-size:38px;margin:0 0 20px}} h3{{font-size:22px;margin:6px 0;color:#bbb}} .big{{font-size:24px;color:#ccc}}
.red{{color:#ef4444}} .grn{{color:#22c55e}} .dtc{{color:#4ade80}} .nsc{{color:#60a5fa}} b{{color:#fff}}
.note{{font-size:14px;color:#777;position:absolute;bottom:28px;left:64px;right:64px}} code{{background:#1f1f1f;padding:0 4px;border-radius:3px;font-size:.9em}}
.kick{{font:600 20px ui-monospace,monospace;color:#3b82f6;letter-spacing:.1em;margin:40px 0 0}} .url{{font:16px ui-monospace,monospace;color:#888}} .url2{{font:18px ui-monospace,monospace;color:#3b82f6;position:absolute;bottom:56px}}
.hook{{display:grid;grid-template-columns:1fr 1fr;gap:32px}} .ref{{margin:30px 0 0}} .ref img{{width:100%;border:1px solid #333;border-radius:8px}} figcaption,.cap{{font-size:15px;color:#999;margin-top:6px}}
.two{{display:grid;grid-template-columns:1fr 1fr;gap:28px}} .three{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:20px;margin-top:18px}} figure{{margin:0}}
.shot{{max-width:100%;max-height:390px;border:1px solid #333;border-radius:8px}} .pre{{background:#151515;border:1px solid #333;border-radius:8px;padding:10px 16px;font:15px/1.3 ui-monospace,monospace;color:#ddd;margin:0;white-space:pre-wrap}}
.stage{{width:100%;border:1px solid #333;border-radius:8px;max-height:430px;object-fit:contain}}
.dr{{display:flex;align-items:center;gap:14px;margin:6px 0}} .dm{{width:150px;font-size:19px}} .ds{{width:330px;display:flex;gap:6px}} .dn{{font-size:16px;color:#aaa}}
.d{{display:inline-block;width:24px;height:24px;border-radius:50%;vertical-align:middle;margin-right:4px}} .d.correct{{background:#22c55e}} .d.confident_wrong{{background:#ef4444}} .d.not_found{{background:#f59e0b}} .d.invalid{{background:#888}}
.hlx{{font-size:22px;margin:10px 0 0}} .big2{{background:#151515;border:1px solid #333;border-radius:10px;padding:10px 16px}} .big2 b{{font-size:40px;display:block}} .big2 span{{font-size:15px;color:#aaa}}
.lg{{font-size:14px;color:#aaa;margin-top:10px}} .lg .d{{width:14px;height:14px;margin-left:10px}} .n1{{font-size:18px;color:#f59e0b;border:1px solid #f59e0b;border-radius:20px;padding:2px 12px;vertical-align:middle}}
.flow{{display:flex;align-items:center;gap:8px;margin:30px 0 30px}} .flow div{{border:2px solid #444;border-radius:10px;padding:12px 8px;font-size:18px;flex:1;text-align:center}}
.flow small{{display:block;font-size:13px;color:#999}} .dt{{border-color:#22c55e!important}} .ns{{border-color:#3b82f6!important}}
.apx{{font:600 14px ui-monospace,monospace;color:#3b82f6;border:1px solid #3b82f6;border-radius:20px;padding:2px 10px;vertical-align:middle;margin-right:10px}}
.hm{{border-collapse:separate;border-spacing:6px;width:100%}} .hm th{{font-size:18px;text-align:left}} .hm td{{color:#fff;text-align:center;font-size:30px;font-weight:700;border-radius:8px;padding:12px 4px}}
.hm td small{{display:block;font-size:13px;font-weight:400}} .hm td.w{{outline:4px solid #fff}} .card{{border:1px solid #333;border-radius:10px;padding:14px 18px;background:#151515}}
.jc .two{{gap:14px}} .jc .card{{padding:6px 16px}} .jc h3{{margin:4px 0;font-size:22px;color:#fff}} .jc ul{{margin:2px 0 6px;font-size:17px;line-height:1.35;padding-left:20px}}
</style></head><body>{''.join(slides)}</body></html>"""
(ROOT / "deck").mkdir(exist_ok=True)
(ROOT / "deck/deck.html").write_text(doc)
subprocess.run([chrome, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                f"--print-to-pdf={ROOT / 'deck/deck.pdf'}", f"file://{ROOT / 'deck/deck.html'}"],
               check=True, capture_output=True, timeout=120)
print("wrote deck/deck.html, deck/deck.pdf", (ROOT / "deck/deck.pdf").stat().st_size // 1024, "KB")

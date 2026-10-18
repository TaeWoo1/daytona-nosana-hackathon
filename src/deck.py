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
RUNS = [json.loads(l) for f in RUN_FILES for l in open(f) if l.strip()]
OK_RUNS = [r for r in RUNS if not r.get("error") or "XML syntax error" in r["error"]]

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

slides = []
slides.append("""<section class="title"><h1>AgentReadable</h1>
<p class="big">AI agents now read your website for your customers.<br>We measure how accurately your real pages get through to each AI reader,
by layout and by model, and show which layout survives even the weakest model.</p>
<p class="spons">Built on <b>Daytona</b> sandboxes · <b>Nosana</b> GPUs</p></section>""")
slides.append(f"""<section><h2>Problem: the agent quotes the wrong price</h2>
<p>Customer → AI agent: <i>"I need an RTX 4090 that won't be interrupted. How much per hour?"</i></p>
<p>Real page <code>daytona.io/pricing</code> (captured 2026-10-18 15:35 KST): the GPU table opens on the <b>Preemptible</b> tab ($0.57/h).
The <b>On-demand</b> price ($0.99/h) is in a hidden tab panel. "Preemptible" is not defined on the page.</p>
<div class="two">{example('visible_text', 'A_original', 'gpt-oss-20b')}{example('visible_text', 'C_faq_structured', 'gpt-oss-20b')}</div>
<p class="note">Two real runs from results/runs_visible.jsonl (first logged run per layout). Gold: $0.99/h on-demand.</p></section>""")
slides.append("""<section><h2>What we built</h2>
<div class="flow"><div>Real page<br><small>+ gold answer key</small></div><span>→</span><div>Layouts A / B / C<br><small>same facts, different arrangement</small></div><span>→</span>
<div class="dt">Daytona sandboxes<br><small>serve each layout · run every page fetch + extraction, isolated, in parallel</small></div><span>→</span>
<div class="ns">Reader agents<br><small>3 open models on Nosana GPUs + Claude</small></div><span>→</span><div>Code grader<br><small>no LLM judge</small></div><span>→</span><div>Dashboard</div></div>
<ul><li>Same system prompt and one tool, <code>open_page(path)</code>, for every model. Temperature 0. Strict JSON answer + evidence quote + not_found.</li>
<li>Two reader modes: <b>html_text</b> (all HTML text, like a crawler) and <b>visible_text</b> (hidden elements dropped, a static approximation of a browser view).</li>
<li>Control: <b>No page</b>, where the model answers from memory.</li></ul></section>""")
slides.append("""<section><h2>Method and metrics</h2>
<ul><li>Gold answers from the real page, 5 questions: GPU on-demand trap, CPU cost with "first 5 GiB free", card / free credit, billing unit, Windows price.</li>
<li>Per run: each field is graded <b>correct / not found / wrong / invalid</b>. A confident wrong value is worse than "not found".</li>
<li><b>Field accuracy</b>, <b>evidence reach</b> (did the gold text appear in the tool output?), and the headline <b>worst-model accuracy per layout</b>.</li>
<li>3 reps per cell. Small n, so we say "in these runs", not "proven".</li></ul></section>""")
for mode in modes[::-1]:
    slides.append(f"""<section><h2>q1 "won't be interrupted" · {mode}</h2>{strict_q(mode, "q1_gpu_ondemand")}
<p class="note">Cell = fully correct runs / runs (gold $0.99/h on-demand); "wrong" = runs with a confident wrong value. Source: results/summary.json (cells_by_question).</p></section>""")
RENDER_VER = {"rendered_text": ("v1 plain mirror", "results/runs_rendered.jsonl", ("700", "520", "660", "80")),
              "rendered_text_v2": ("v2 styled", "results/runs_rendered_v2.jsonl", ("400", "400", "625", "0"))}
for rmode in [m for m in RENDER_VER if m in modes]:
    ver_label, src_file, (ch, cw, cy, cx) = RENDER_VER[rmode]
    sys.path.insert(0, str(ROOT / "src"))
    import grade as _grade
    rend = [r for r in OK_RUNS if r["mode"] == rmode and r["layout"] == "A_original"]
    rows = []
    for m in MODELS:
        xs = [r for r in rend if r["model"] == m]
        if not xs:
            continue
        clicked = [r for r in xs if any(t["name"] == "click" for t in r["tool_calls"])]
        ok_c = sum(_grade.grade(r)["all_correct"] for r in clicked)
        ok_n = sum(_grade.grade(r)["all_correct"] for r in xs if r not in clicked)
        rows.append(f"<tr><td>{ML[m]}</td><td>{len(clicked)}/{len(xs)}</td><td>{ok_c}/{len(clicked)}</td>"
                    f"<td>{ok_n}/{len(xs) - len(clicked)}</td></tr>")
    ex = next((r for r in rend if any(t["name"] == "click" for t in r["tool_calls"]) and _grade.grade(r)["all_correct"]
               and all(t.get("frame") for t in r["tool_calls"][:2])), None)
    frames = ""
    if ex:
        f1, f2 = ex["tool_calls"][0]["frame"], next(t["frame"] for t in ex["tool_calls"] if t["name"] == "click")
        crops = []
        for k, f in enumerate((f1, f2)):
            # crop the GPU section of the full-page screenshot so it is readable on a slide (macOS sips)
            out = ROOT / "deck" / f"frame_crop_{rmode}_{k + 1}.png"
            subprocess.run(["sips", "-c", ch, cw, "--cropOffset", cy, cx, str(ROOT / "results" / f), "--out", str(out)],
                           check=True, capture_output=True)
            crops.append(out.name)
        f1, f2 = crops
        frames = (f'<div class="frames"><figure><img src="{f1}"><figcaption>step 1 · open_page: Preemptible tab shown</figcaption></figure>'
                  f'<figure><img src="{f2}"><figcaption>after click("On-demand")</figcaption></figure></div>'
                  f'<p class="note2">GPU section cropped from full-page screenshots. Frames: {ML[ex["model"]]}, run {html.escape(ex["run_id"])} (results/frames/).</p>')
    slides.append(f"""<section><h2>Real browser in Daytona · layout A · {ver_label}</h2><div class="two">
<div><table class="ct"><tr><th>model</th><th>clicked On-demand tab</th><th>fully correct | clicked</th><th>fully correct | no click</th></tr>{"".join(rows)}</table>
<p>Chromium runs inside the Daytona sandbox (Playwright). The reader can <code>click(text)</code>; each step is screenshotted.
Agents that clicked the tab could read $0.99. Agents that didn't, couldn't.</p></div><div>{frames}</div></div>
<p class="note">q1 only, layout A, 3 reps per model. Source: {src_file} graded by src/grade.py.</p></section>""")
for mode in [m for m in modes if not m.startswith("rendered_text")]:
    slides.append(f"""<section><h2>All 5 questions · {mode}</h2>{heat(mode)}
<p class="note">Cell = mean share of answer fields matching gold. n = runs (5 questions × 3 reps). Outlined column = weakest model per layout. Source: results/summary.json.</p></section>""")
if "visible_text" in modes:
    slides.append(f"""<section><h2>Which fact breaks (visible_text)</h2>{qbars('visible_text', ['q1_gpu_ondemand', 'q2_cpu_sandbox_cost', 'q3_signup'])}
<div class="lg"><span class="s correct">fully correct</span><span class="s not_found">not found</span><span class="s wrong">wrong value</span><span class="s invalid">invalid JSON</span></div>
<p class="note">All models pooled, runs per layout. Source: results/summary.json (by_question).</p></section>""")
slides.append(f"""<section><h2>Sponsor usage</h2><div class="two">
<div class="card dt"><h3>Daytona</h3><ul><li>{n_sb} ephemeral sandboxes across runs, each serving one layout on localhost:8000</li>
<li>{n_tool} <code>open_page</code> calls executed inside sandboxes (median {med_tool:.2f}s each), with a fresh process per call and no shared state</li>
<li>Parallel fan-out: layouts × workers, all runs from one script</li></ul></div>
<div class="card ns"><h3>Nosana</h3><ul><li>3 open-weight reader models on decentralized GPUs: Qwen 3.5 9B (RTX 3090), gpt-oss 20B and Gemma 4 26B (RTX 4090)</li>
<li>{nosana_runs} graded reader runs served from Nosana</li>
<li>Small open models are exactly the readers that need a robust layout</li></ul></div></div>
<p class="note">Counts from results/runs*.jsonl. Graded runs total: {n_runs}.</p></section>""")
slides.append(f"""<section><h2>Limitations and next steps</h2><ul>
<li>One page, a simplified mirror (A), 3 reps per cell. Directional, not proof.</li>
<li>visible_text is a static approximation (drops hidden elements). rendered_text (real Chromium) was run for q1 only, on layouts A and C, on two site versions: v1 plain mirror and v2 styled like the real page (both are our re-creations, not the live site).</li>
<li>Field accuracy gives partial credit. See the per-question "fully correct" view.</li>
<li>OpenAI excluded: the API key had no credits ({html.escape(json.dumps(excl))}).</li>
<li>Gold ambiguity: "first 5 GiB free" per sandbox or per org? (Both readings are inside the q2 tolerance.)</li>
<li>Next: more pages and verticals, an auto-fix suggestion per failing fact, and a CI check: "does this layout change break any AI reader?"</li></ul></section>""")
slides.append("""<section class="title"><h2>Thanks</h2><p class="big">AgentReadable: make sure every AI reader quotes your page right.</p>
<p>Solo build · GitHub @TaeWoo1</p><p>Repo: github.com/TaeWoo1/daytona-nosana-hackathon</p><p class="spons"><b>Daytona</b> · <b>Nosana</b></p></section>""")

doc = f"""<!doctype html><html><head><meta charset="utf-8"><title>AgentReadable deck</title><style>
@page{{size:1280px 720px;margin:0}} body{{margin:0;font:22px/1.45 system-ui,sans-serif;color:#1d1d1b;background:#fff}}
section{{width:1280px;height:720px;box-sizing:border-box;padding:56px 72px;page-break-after:always;overflow:hidden;position:relative}}
h1{{font-size:72px;margin:120px 0 20px}} h2{{font-size:40px;margin:0 0 24px}} .big{{font-size:28px}} .spons{{position:absolute;bottom:56px;font-size:24px}}
.note{{font-size:15px;color:#666;position:absolute;bottom:36px;left:72px;right:72px}} code{{background:#f2f2ee;padding:0 4px;border-radius:3px}}
.hm{{border-collapse:separate;border-spacing:6px;width:100%}} .hm th{{font-size:18px;text-align:left}} .hm td{{color:#fff;text-align:center;font-size:30px;font-weight:700;border-radius:8px;padding:12px 4px}}
.hm td small{{display:block;font-size:13px;font-weight:400}} .hm td.w{{outline:4px solid #1d1d1b}}
.two{{display:grid;grid-template-columns:1fr 1fr;gap:24px}} .ex,.card{{border:2px solid #ddd;border-radius:10px;padding:14px 18px}} .exh{{font-weight:700}}
.qt{{color:#666;font-style:italic;font-size:18px}} .flow{{display:flex;align-items:center;gap:8px;margin:20px 0 30px}} .flow div{{border:2px solid #ccc;border-radius:10px;padding:10px;font-size:18px;flex:1;text-align:center}}
.flow small{{display:block;font-size:13px;color:#666}} .dt{{border-color:#2a6!important}} .ns{{border-color:#36c!important}}
.q{{margin:8px 0 14px}} .bar{{display:flex;align-items:center;gap:10px;font-size:16px;margin:3px 0}} .bl{{width:240px}} .bn{{width:60px;color:#666}}
.tr{{flex:1;display:flex;height:24px;border-radius:4px;overflow:hidden;background:#eee}} .s{{display:inline-flex;align-items:center;justify-content:center;color:#fff;font-size:13px}}
.ct{{border-collapse:collapse;font-size:18px;margin-bottom:12px}} .ct td,.ct th{{border:1px solid #ccc;padding:4px 8px;text-align:center}}
.frames{{display:grid;grid-template-columns:1fr 1fr;gap:8px}} .frames figure{{margin:0}} .frames img{{width:100%;border:1px solid #ccc}}
.frames figcaption{{font-size:13px;color:#666}} .note2{{font-size:13px;color:#666}}
.correct{{background:hsl(130 55% 36%)}} .not_found{{background:hsl(40 80% 45%)}} .wrong{{background:hsl(0 65% 48%)}} .invalid{{background:#888}} .lg .s{{padding:2px 10px;margin-right:6px}} .tag{{color:#fff;border-radius:4px;padding:1px 8px;font-size:16px;margin-left:6px}} .ok{{background:hsl(130 55% 36%)}} .bad{{background:hsl(0 65% 48%)}}
</style></head><body>{''.join(slides)}</body></html>"""
(ROOT / "deck").mkdir(exist_ok=True)
(ROOT / "deck/deck.html").write_text(doc)
chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
subprocess.run([chrome, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                f"--print-to-pdf={ROOT / 'deck/deck.pdf'}", f"file://{ROOT / 'deck/deck.html'}"],
               check=True, capture_output=True, timeout=120)
print("wrote deck/deck.html, deck/deck.pdf", (ROOT / "deck/deck.pdf").stat().st_size // 1024, "KB")

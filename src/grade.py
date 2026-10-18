"""Code-based grading (no LLM judge). results/runs*.jsonl -> results/graded.jsonl + results/summary.json

usage: .venv/bin/python src/grade.py [runs.jsonl ...]
"""
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GOLD = json.loads((ROOT / "data/gold/daytona_pricing_facts.draft.json").read_text())
QS = {q["id"]: q for q in GOLD["questions"]}

# strings that must appear in tool outputs for "evidence reach"
NEEDLES = {
    "q1_gpu_ondemand": ["$0.99/h"],
    "q2_cpu_sandbox_cost": ["0.0504", "0.0162"],
    "q3_signup": ["no credit card", "$200"],
    "q4_billing": ["per second"],
    "q5_windows": ["0.0858"],
}
NULLISH = (None, "", "unknown", "null")


def grade_field(gold_v, ans_v, tol):
    if ans_v in NULLISH:
        return "not_found"
    if isinstance(gold_v, bool):
        if isinstance(ans_v, str):
            ans_v = {"true": True, "false": False}.get(ans_v.lower(), ans_v)
        return "correct" if ans_v is gold_v else "wrong"
    if isinstance(gold_v, (int, float)):
        try:
            x = float(str(ans_v).replace("$", "").replace(",", ""))
        except ValueError:
            return "wrong"
        t = tol if tol is not None else max(abs(gold_v) * 0.01, 1e-9)
        return "correct" if abs(x - gold_v) <= t else "wrong"
    return "correct" if str(ans_v).strip().lower() == str(gold_v).lower() else "wrong"


def grade(r):
    q = QS[r["question"]]
    gold = {k: v for k, v in q["gold"].items() if k not in ("tolerance", "calc")}
    tol = q["gold"].get("tolerance")
    a = r.get("answer")
    if not isinstance(a, dict):
        fields = {k: "invalid" for k in gold}
    else:
        fields = {k: grade_field(v, a.get(k), tol) for k, v in gold.items()}
    outs = "\n".join(t["output"] or "" for t in r.get("tool_calls", []))
    reach = all(n in outs for n in NEEDLES[r["question"]]) if r["layout"] != "NOPAGE" else None
    n_ok = sum(v == "correct" for v in fields.values())
    return {**{k: r[k] for k in ("batch", "model", "layout", "question", "rep", "mode", "n_tool_calls",
                                 "latency_sec", "error")},
            "usage": r.get("usage"), "fields": fields, "acc": n_ok / len(fields),
            "all_correct": n_ok == len(fields), "any_wrong": any(v == "wrong" for v in fields.values()),
            "evidence_reach": reach, "run_set": r.get("run_set"),
            "clicked": any(t["name"] == "click" for t in r.get("tool_calls", []))}


def summarize(g):
    cells = defaultdict(list)
    for x in g:
        cells[(x["mode"] if x["layout"] != "NOPAGE" else "none", x["layout"], x["model"])].append(x)
    out = {"cells": [], "by_question": [], "worst_model": [], "n_runs": len(g)}
    for (mode, l, m), xs in sorted(cells.items()):
        fc = defaultdict(int)
        for x in xs:
            for v in x["fields"].values():
                fc[v] += 1
        out["cells"].append({
            "mode": mode, "layout": l, "model": m, "n_runs": len(xs),
            "field_accuracy": round(statistics.mean(x["acc"] for x in xs), 4),
            "field_counts": dict(fc),
            "wrong_assertion_rate": round(sum(x["any_wrong"] for x in xs) / len(xs), 4),
            "evidence_reach": (round(sum(bool(x["evidence_reach"]) for x in xs) / len(xs), 4)
                               if l != "NOPAGE" else None),
            "mean_tool_calls": round(statistics.mean(x["n_tool_calls"] for x in xs), 2),
            "mean_latency_sec": round(statistics.mean(x["latency_sec"] for x in xs), 2),
            "errors": sum(bool(x["error"]) for x in xs),
        })
    # stability: per (mode, layout, model, question), fraction of reps that agree with the majority outcome
    bq = defaultdict(lambda: defaultdict(int))
    for x in g:
        mode = x["mode"] if x["layout"] != "NOPAGE" else "none"
        k = "correct" if x["all_correct"] else ("wrong" if x["any_wrong"] else
                                                ("invalid" if "invalid" in x["fields"].values() else "not_found"))
        bq[(mode, x["layout"], x["question"])][k] += 1
    out["by_question"] = [{"mode": mo, "layout": l, "question": q, **dict(c), "n_runs": sum(c.values())}
                          for (mo, l, q), c in sorted(bq.items())]
    # strict per-question view: share of runs with ALL fields correct, per (mode, layout, model, question)
    cq = defaultdict(list)
    for x in g:
        cq[(x["mode"] if x["layout"] != "NOPAGE" else "none", x["layout"], x["model"], x["question"])].append(x)
    out["cells_by_question"] = [
        {"mode": mo, "layout": l, "model": m, "question": q, "n_runs": len(xs),
         "fully_correct": sum(x["all_correct"] for x in xs), "any_wrong": sum(x["any_wrong"] for x in xs),
         "fully_correct_rate": round(sum(x["all_correct"] for x in xs) / len(xs), 4)}
        for (mo, l, m, q), xs in sorted(cq.items())]
    by_layout = defaultdict(list)
    for c in out["cells"]:
        by_layout[(c["mode"], c["layout"])].append(c)
    for (mode, l), cs in sorted(by_layout.items()):
        w = min(cs, key=lambda c: c["field_accuracy"])
        out["worst_model"].append({"mode": mode, "layout": l, "worst_model": w["model"],
                                   "worst_model_accuracy": w["field_accuracy"],
                                   "mean_accuracy": round(statistics.mean(c["field_accuracy"] for c in cs), 4),
                                   "n_models": len(cs), "n_runs_per_model": [c["n_runs"] for c in cs]})
    out["behavior"] = behavior(g)
    out["behavior_headline"] = headline(out["behavior"])
    return out


def headline(rows, run_set="runs_rendered_v2_n10"):
    """One sentence from the headline batch's actual numbers (no hand-typed figures)."""
    get = {(r["run_set"], r["layout"], r["model"]): r for r in rows}
    a, c = get.get((run_set, "A_original", "ALL")), get.get((run_set, "C_faq_structured", "ALL"))
    if not a or not c:
        return None
    f = lambda x: f"{x['k']}/{x['n']}"  # noqa: E731
    return (f"Real browser in Daytona, styled page, q1: on the original tabbed layout A, agents that clicked the On-demand tab "
            f"were fully correct {f(a['correct_given_clicked'])}, agents that didn't click {f(a['correct_given_no_click'])}; "
            f"A overall {f(a['correct_rate'])} correct with {f(a['confident_wrong_rate'])} confident wrong answers, "
            f"while the explicit layout C was {f(c['correct_rate'])} correct.")


def outcome(x):
    return "correct" if x["all_correct"] else ("confident_wrong" if x["any_wrong"] else
                                               ("invalid" if "invalid" in x["fields"].values() else "not_found"))


def rate(k, n):
    return {"k": k, "n": n, "rate": round(k / n, 4) if n else None}


def behavior(g):
    """Rendered (browser + click) runs: per run set (source file) x layout x model (+ ALL pooled):
    click / correct / confident_wrong / not_found / invalid rates, and correct rate given clicked vs not clicked."""
    groups = defaultdict(list)
    for x in g:
        if str(x["mode"]).startswith("rendered_text"):
            groups[(x["run_set"], x["layout"], x["model"])].append(x)
            groups[(x["run_set"], x["layout"], "ALL")].append(x)
    rows = []
    for (rs, l, m), xs in sorted(groups.items()):
        n = len(xs)
        oc = [outcome(x) for x in xs]
        cl = [x for x in xs if x["clicked"]]
        nc = [x for x in xs if not x["clicked"]]
        rows.append({"run_set": rs, "mode": xs[0]["mode"], "layout": l, "model": m, "n_runs": n,
                     "batches": sorted({x["batch"] for x in xs}),
                     "click_rate": rate(len(cl), n),
                     "correct_rate": rate(oc.count("correct"), n),
                     "confident_wrong_rate": rate(oc.count("confident_wrong"), n),
                     "not_found_rate": rate(oc.count("not_found"), n),
                     "invalid_rate": rate(oc.count("invalid"), n),
                     "correct_given_clicked": rate(sum(x["all_correct"] for x in cl), len(cl)),
                     "correct_given_no_click": rate(sum(x["all_correct"] for x in nc), len(nc))})
    return rows


def infra_reason(r):
    """Why a run is excluded as infra (not a reader mistake), or None.
    A tool call that failed because of Daytona/the in-sandbox browser makes the whole run infra:
    exec timeout, Chromium launch crash (render.py traceback), or the browser failing to render the page."""
    if r.get("error"):
        return None if "XML syntax error" in r["error"] else r["error"].split(":")[0]
    for t in r.get("tool_calls", []):
        o = t.get("output") or ""
        if "render.py" in o and "Traceback" in o:
            return "BrowserLaunchCrash"
        # in render.py this line only comes from a browser exception (a bad path is reported as "HTTP 404", not ERROR);
        # in html_text/visible_text the extractor prints ERROR for a wrong path, which IS a reader mistake
        if "ERROR: could not open" in o and str(r.get("mode")).startswith("rendered_text"):
            return "BrowserRenderError"
    return None


def main():
    files = sys.argv[1:] or [str(ROOT / "results/runs.jsonl")]
    runs = [{**json.loads(l), "run_set": Path(f).stem} for f in files for l in open(f) if l.strip()]
    for r in runs:  # the earlier v2 batch (n=3) is kept but summarized separately from the headline v2 batch (n10 file)
        if r["run_set"] == "runs_rendered_v2":
            r["mode"] = "rendered_text_v2_n3"
    # API/infra failures (e.g. 429 no credits, timeouts) are not reader mistakes: excluded and counted separately
    # a malformed tool call rejected by the Ollama server (HTTP 500 "XML syntax error") IS a reader failure -> graded as invalid
    def is_infra(r):
        # Chromium failing to launch in an overloaded sandbox (render.py traceback) is infra too, not a reader mistake
        return bool(infra_reason(r))
    infra = [r for r in runs if is_infra(r)]
    runs = [r for r in runs if not is_infra(r)]
    g = [grade(r) for r in runs]
    with open(ROOT / "results/graded.jsonl", "w") as f:
        for x in g:
            f.write(json.dumps(x) + "\n")
    s = summarize(g)
    ie = defaultdict(int)
    for r in infra:
        ie[f"{r['model']}: {infra_reason(r)}"] += 1
    s["excluded_infra_errors"] = dict(ie)
    by_set = defaultdict(lambda: defaultdict(int))
    for r in infra:
        by_set[r["run_set"]][f"{r['layout']} {r['model']}: {infra_reason(r)}"] += 1
    s["excluded_infra_by_run_set"] = {k: dict(v) for k, v in by_set.items()}
    s["source_files"] = [str(Path(f).relative_to(ROOT)) if Path(f).is_absolute() else f for f in files]
    (ROOT / "results/summary.json").write_text(json.dumps(s, indent=1))
    print(f"graded {len(g)} runs; excluded infra errors: {dict(ie)}")
    for w in s["worst_model"]:
        print(f"  {w['mode']:12s} {w['layout']:16s} mean={w['mean_accuracy']:.2f} worst={w['worst_model_accuracy']:.2f} ({w['worst_model']})")


if __name__ == "__main__":
    main()

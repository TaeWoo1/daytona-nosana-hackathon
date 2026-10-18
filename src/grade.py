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
            "evidence_reach": reach}


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
    return out


def main():
    files = sys.argv[1:] or [str(ROOT / "results/runs.jsonl")]
    runs = [json.loads(l) for f in files for l in open(f) if l.strip()]
    # API/infra failures (e.g. 429 no credits, timeouts) are not reader mistakes: excluded and counted separately
    # a malformed tool call rejected by the Ollama server (HTTP 500 "XML syntax error") IS a reader failure -> graded as invalid
    def is_infra(r):
        return bool(r.get("error")) and "XML syntax error" not in r["error"]
    infra = [r for r in runs if is_infra(r)]
    runs = [r for r in runs if not is_infra(r)]
    g = [grade(r) for r in runs]
    with open(ROOT / "results/graded.jsonl", "w") as f:
        for x in g:
            f.write(json.dumps(x) + "\n")
    s = summarize(g)
    ie = defaultdict(int)
    for r in infra:
        ie[f"{r['model']}: {r['error'].split(':')[0]}"] += 1
    s["excluded_infra_errors"] = dict(ie)
    s["source_files"] = [str(Path(f).relative_to(ROOT)) if Path(f).is_absolute() else f for f in files]
    (ROOT / "results/summary.json").write_text(json.dumps(s, indent=1))
    print(f"graded {len(g)} runs; excluded infra errors: {dict(ie)}")
    for w in s["worst_model"]:
        print(f"  {w['mode']:12s} {w['layout']:16s} mean={w['mean_accuracy']:.2f} worst={w['worst_model_accuracy']:.2f} ({w['worst_model']})")


if __name__ == "__main__":
    main()

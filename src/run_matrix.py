"""Fan out reader runs: layouts x models x questions x reps -> results/runs.jsonl

usage: .venv/bin/python src/run_matrix.py [--models a,b] [--layouts A_original,...] [--questions q1,...]
                                          [--reps 3] [--mode html_text|visible_text] [--workers 2] [--out results/runs.jsonl]
"""
import argparse
import itertools
import json
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import agent
from daytona_pool import Pool

ROOT = Path(__file__).resolve().parent.parent
LAYOUTS = ["A_original", "B_explicit", "C_faq_structured", "NOPAGE"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="")
    ap.add_argument("--layouts", default=",".join(LAYOUTS))
    ap.add_argument("--questions", default="")
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--mode", default="html_text")
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--out", default="results/runs.jsonl")
    a = ap.parse_args()

    gold = json.loads((ROOT / "data/gold/daytona_pricing_facts.draft.json").read_text())
    qs = [q for q in gold["questions"] if not a.questions or any(q["id"].startswith(p) for p in a.questions.split(","))]
    ms = agent.models()
    if a.models:
        ms = {k: v for k, v in ms.items() if k in a.models.split(",")}
    layouts = a.layouts.split(",")
    batch = time.strftime("%H%M%S") + "-" + uuid.uuid4().hex[:4]
    print(f"[batch {batch}] models={list(ms)} layouts={layouts} questions={[q['id'] for q in qs]} reps={a.reps} mode={a.mode}")

    pool = Pool([l for l in layouts if l != "NOPAGE"], a.workers, render=a.mode == "rendered_text")
    out = ROOT / a.out
    out.parent.mkdir(exist_ok=True)
    wlock = threading.Lock()
    try:
        t0 = time.time()
        pool.start()
        print(f"[batch {batch}] {sum(len(v) for v in pool.sandboxes.values())} sandboxes up in {time.time()-t0:.1f}s")

        # interleave models so no model's semaphore starves the thread pool
        per_model = [[(mid, l, q, rep) for rep in range(a.reps) for q in qs for l in layouts] for mid in ms]
        jobs = [j for grp in itertools.zip_longest(*per_model) for j in grp if j]

        def do(job):
            mid, l, q, rep = job
            client, name, extra, _ = ms[mid]
            run_id = f"{batch}-{mid}-{l}-{q['id'][:2]}-r{rep}"
            click_fn = None
            if l == "NOPAGE":
                page_fn, sbid = None, None
            elif a.mode == "rendered_text":
                sb = pool.pick(l)
                sbid = sb.id
                # browser state per run: current path + click history, replayed on each (stateless) sandbox call
                st = {"path": "/pricing", "clicks": [], "step": 0}

                def shot():
                    st["step"] += 1
                    return ROOT / "results/frames" / run_id / f"step_{st['step']}.png"

                def page_fn(p):
                    st["path"], st["clicks"] = p, []
                    return pool.render_page(sb, p, [], shot())

                def click_fn(t):
                    st["clicks"].append(t)
                    return pool.render_page(sb, st["path"], st["clicks"], shot())
            else:
                sb = pool.pick(l)
                sbid = sb.id
                page_fn = lambda p: pool.open_page(sb, p, a.mode)  # noqa: E731
            rec = agent.run(mid, client, name, extra, q, page_fn, click_fn=click_fn)
            rec["run_id"] = run_id
            rec.update({"batch": batch, "layout": l, "rep": rep, "mode": a.mode if l != "NOPAGE" else "none",
                        "sandbox_id": sbid, "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z")})
            with wlock, out.open("a") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            return rec

        done = 0
        # one executor per model (sized to its concurrency cap) so a slow model never blocks the others
        exs = {m: ThreadPoolExecutor(v[3]) for m, v in ms.items()}
        try:
            futs = [exs[j[0]].submit(do, j) for j in jobs]
            for fu in as_completed(futs):
                done += 1
                r = fu.result()
                ans = json.dumps(r["answer"], ensure_ascii=False)[:90] if r["answer"] else (r["error"] or "NO-JSON")
                print(f"[{done:3d}/{len(jobs)}] {r['model']:12s} {r['layout']:16s} {r['question']:20s} rep{r['rep']} "
                      f"tools={r['n_tool_calls']} {r['latency_sec']:5.1f}s  {ans}", flush=True)
        finally:
            for ex in exs.values():
                ex.shutdown(wait=True)
        print(f"[batch {batch}] done {len(jobs)} runs in {time.time()-t0:.1f}s -> {a.out}")
    finally:
        pool.close()


if __name__ == "__main__":
    main()

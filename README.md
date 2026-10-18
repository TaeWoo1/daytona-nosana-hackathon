# AgentReadable

**AI agents now read your website for your customers. We measure how accurately your real pages get through to each AI reader, by layout and by model, and show which layout survives even the weakest model.**

Built at Daytona HackSprint Seoul (2026-10-18) with **Daytona** sandboxes and **Nosana** GPUs.

## The problem

A customer asks an AI agent: *"I need an RTX 4090 that won't be interrupted. How much per hour?"*
The agent opens the vendor's pricing page and answers. On the real `daytona.io/pricing` page (captured 2026-10-18 15:35 KST, `data/raw/`), the GPU table shows the **Preemptible** tab by default ($0.57/h for the RTX 4090). The **On-demand** price ($0.99/h) sits in a hidden tab panel. An agent that sees only the visible text can quote the preemptible price as if it were the guaranteed price.

We don't measure AI *search visibility* (that's what GEO tools do). We measure **comprehension accuracy**: given the page, does the AI reader get the facts right?

## How it works

```
real page ──► gold answer key (data/gold)          ┌─ Nosana GPU: Qwen 3.5 9B
     │                                              ├─ Nosana GPU: gpt-oss 20B
     └─► layouts A / B / C (src/gen_sites.py)       ├─ Nosana GPU: Gemma 4 26B
              │                                     └─ Anthropic API: Claude
              ▼                                               │
   Daytona sandboxes (one per layout × worker)   ◄── open_page tool calls
   each serves its layout on localhost:8000      (exec'd inside the sandbox)
              │
              ▼
   results/runs.jsonl ─► src/grade.py (code, no LLM judge) ─► src/report.py ─► results/dashboard.html
```

- **Layouts** (facts identical, generated from the same gold JSON):
  - **A_original**: mirror of the real page structure: tabbed GPU prices with the On-demand panel `hidden`, and the "*first 5 GiB free" storage footnote.
  - **B_explicit**: one GPU table with both columns visible, labelled "Preemptible (may be interrupted)" and "On-demand (not interrupted)". The storage free tier sits next to the price.
  - **C_faq_structured**: B plus a plain-text FAQ and JSON-LD `Offer` / `UnitPriceSpecification`.
  - **NOPAGE**: no tools at all (memory-only control).
- **Reader agent** (`src/agent.py`): same system prompt and the single tool `open_page(path)` for every model. Temperature 0, at most 6 tool steps. It returns strict JSON with the answer fields, `evidence_quote`, and `not_found`.
- **Reader modes** (`src/sandbox_extract.py`, runs inside the sandbox):
  - `html_text`: all HTML text, including hidden panels (like a crawler).
  - `visible_text`: hidden elements dropped. This is a *static approximation* of a browser view, not a real browser render.
- **Daytona**: every page fetch and text extraction runs inside an isolated, ephemeral Daytona sandbox, with a fresh process per tool call and no shared cookies or state. Fan-out uses several sandboxes per layout in parallel.
- **Nosana**: three open-weight reader models are served with Ollama on Nosana GPUs (RTX 3090 / 4090).

## Questions (gold from the real page)

| id | question | gold |
|---|---|---|
| q1 | RTX 4090 that won't be interrupted, $/h? | 0.99, on_demand |
| q2 | 2 vCPU + 4 GiB RAM + 8 GiB disk, $/h? | 0.165924 (±0.002) |
| q3 | Credit card needed? Free credit? | false, $200 |
| q4 | Billing granularity? | per_second |
| q5 | Windows $/vCPU/h? | 0.0858 |

## Metrics

All metrics are graded by code against the gold key:

- **Field accuracy**: share of answer fields that match gold.
- Each run is counted as **correct / not_found / wrong / invalid**.
- **Wrong** means a confident wrong value, which is worse than not_found.
- **Evidence reach**: did the gold string appear in the tool outputs?
- **Headline: worst-model accuracy per layout.**

## Results

RESULTS_PLACEHOLDER

## Limitations (read before quoting numbers)

- Small n (3 reps per cell, temperature 0). Read the results as "in these runs", not as proof.
- One page (Daytona pricing) and one site mirror. Layout A is a simplified mirror of the real page, not the live page.
- `visible_text` is a static approximation (it drops `hidden` / `display:none`), not a real browser render.
- Field accuracy gives partial credit. For example, on q1 an answer with `pricing_type: on_demand` but no price still gets 1 of 2 fields. The per-question "fully correct" counts are the stricter view.
- OpenAI was configured but excluded: the key had no credits (HTTP 429). Those runs are listed under `excluded_infra_errors`.
- Gold ambiguities: whether "first 5 GiB free" applies per sandbox or per org is not stated (both readings fall inside the q2 tolerance), and "preemptible" is not defined on the page.
- We do not claim any AI search ranking or citation effect.

## Run it

```bash
python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env    # DAYTONA_API_KEY, NOSANA_*_BASE_URL/MODEL, ANTHROPIC_API_KEY, (OPENAI_API_KEY)
.venv/bin/python src/gen_sites.py
.venv/bin/python src/run_matrix.py --mode html_text    --out results/runs.jsonl
.venv/bin/python src/run_matrix.py --mode visible_text --layouts A_original,B_explicit,C_faq_structured --out results/runs_visible.jsonl
.venv/bin/python src/grade.py  results/runs.jsonl results/runs_visible.jsonl
.venv/bin/python src/report.py results/runs.jsonl results/runs_visible.jsonl   # -> results/dashboard.html
```

## Repo

- `data/raw/`: the real page as captured.
- `data/gold/`: facts, questions, and gold answers.
- `sites/`: layouts A, B and C.
- `src/`: agent, Daytona pool, runner, grader and report.
- `results/`: raw runs (full tool transcripts), graded runs, summary, dashboard.
- `LOG.md`: timestamped decisions and failures.

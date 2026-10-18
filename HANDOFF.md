# HANDOFF — Daytona HackSprint Seoul (2026-10-18)

> Written by Aside at 15:40 KST for the local Claude Code session.
> Hacking ends **17:00**, then **3-minute live demo** per team, winners at 17:30.
> Submission: **Git repo + Project Slide Deck PDF (≤10 MB)** via the "Hackathon Project Submission" Google Form. The form fields were not inspected yet, so check them before 16:50.
> Keep `LOG.md` updated (decisions, numbers, failures). It feeds the README and the deck.

---

## 0. One-line pitch

**"AI agents now read your website for your customers. We measure how accurately your real pages get through to each AI, by layout and by model, and show which layout survives even the weakest model."**

- Working title: **AgentReadable** (rename freely)
- Customer-facing frame: *"When my customer asks an AI agent about my service, does the agent get the price and conditions right?"*

---

## 1. Why this hackathon / what the organizers want (design for the audience)

- This is a **marketing event** for Daytona's Asia developer push. Daytona has run it in Singapore, Tokyo, and Seoul (this is Seoul #2). AI Builders posts "standout projects" one-liners afterwards.
- Daytona's message: *"Simple chatbots are over. Agents need to actually do things in isolated sandboxes: sub-second start, full machine, massive parallel fan-out, MCP."*
- Nosana's message: a decentralized GPU cloud running real AI workloads, cheaply. They want open models served on their GPUs.
- Past winners and featured projects all made the sandbox **load-bearing** (isolation, or parallelism that would be impossible without it). Examples: Detonate SG (detonates scam links in a sandbox) and A/B GPT (SF 1st place).
- **Differentiate from A/B GPT and the persona-simulation family.** Those use agents as *proxies for humans*. In our project **the agent IS the customer-facing reader**, and grading is fact-based against a gold answer key, not behavioural. Do NOT use the words "A/B test", "persona", "virtual customer", or "conversion".

## 2. Judging criteria and how we hit each

| Criterion | Our answer |
|---|---|
| Completeness (MVP) | End-to-end: real page → layout variants → parallel agent runs → auto-grading → heatmap. One happy path must work live; also keep a backup recording/screenshots. |
| Innovation | Measures *comprehension accuracy* of the AI reader, not AI search visibility like existing GEO tools (Profound, Scrunch, Peec, Otterly). Layout × model matrix, plus a "worst-model accuracy" metric. |
| Real-life problem | AI agents misquote prices and conditions (e.g., show the preemptible GPU price as the normal price) → wrong expectations and support load. Demo it on a **real public page** (Daytona's own pricing page). |
| Sponsor usage | **Daytona:** every layout variant is served inside sandboxes, and the reader tools execute inside sandboxes with a clean run each time, in parallel fan-out. Optionally one Computer Use recording. **Nosana:** 3 open-weight reader models on Nosana GPUs (Qwen 3.5 9B, gpt-oss 20B, Gemma 4 26B). Say both sponsor names clearly on stage. |

## 2b. Judging (AI + human) -> read docs/JUDGING.md

- The criteria were verified on the Luma page. Judging is reportedly AI + human.
- README and deck must be AI-legible: criterion-named sections, text tables, file:line evidence.
- No prompt-injection tricks.
- **Upgrade:** `visible_text` reading mode (headless Chromium inside the Daytona sandbox) is promoted from stretch to **should-have for q1**.
  - The preemptible/on-demand trap likely only bites readers that see the visible tab.
  - It is also the strongest Daytona usage.

## 3. Claims boundary (important — the user has strict evidence standards)

- We show: *"For the tested models and tools, layout X conveyed facts more accurately."* We do **not** claim AI search ranking or citation gains.
- n is small (3–5 reps), so report n and spread. Don't call it "proven"; say "in N runs".
- The gold answers come from the real page. Two items are ambiguous (see §6), so verify them with Daytona staff on site or exclude them.
- Frame it constructively when using Daytona's page ("here's how agents read your page, and a fix"), not as a gotcha.
- A "no-page baseline" separates memorized knowledge from actually reading the page.

---

## 4. Experiment design

**Target page (real data):** `https://www.daytona.io/pricing`, captured 2026-10-18 15:35 KST → `data/raw/`.

- **Real trap already on the page:** the GPU price table shows the **Preemptible** tab by default. On-demand prices only become visible after a click. **Both are present in the HTML** (grep confirms `0.57/h` and `0.99/h` in both server and rendered HTML).
  - Hypothesis: text-extraction readers see both but may mis-attribute them. Visible-text/browser readers see only the preemptible price.

**Layouts (facts identical, arrangement differs):**

- **A_original:** mirror of the real page (static HTML; keep the tab structure and hidden On-demand panel; keep the "*first 5 free" footnote).
- **B_explicit:** a single GPU table with both columns visible, explicitly labelled "Preemptible (may be interrupted)" and "On-demand". The storage free-tier text sits next to the price (not as a footnote).
- **C_faq_structured:** B, plus an FAQ block in plain Q&A text, plus JSON-LD (`Offer` / `PriceSpecification`).
- **NOPAGE baseline:** the model answers without any page (memory only).

**Reader models (OpenAI-compatible except Anthropic):**

| id | where | env |
|---|---|---|
| qwen3.5:9b | Nosana RTX 3090 | `NOSANA_QWEN_BASE_URL`, `NOSANA_QWEN_MODEL` |
| gpt-oss:20b | Nosana RTX 4090 | `NOSANA_GPTOSS_BASE_URL`, `NOSANA_GPTOSS_MODEL` |
| gemma4:26b (MoE) | Nosana RTX 4090 | `NOSANA_GEMMA_BASE_URL`, `NOSANA_GEMMA_MODEL` |
| OpenAI | API | `OPENAI_API_KEY`, `OPENAI_MODEL` (placeholder `gpt-4.1-mini`; change to your choice) |
| Anthropic | API | `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL` (placeholder `claude-sonnet-4-5`; verify exact model id) |

**Questions:** `data/gold/daytona_pricing_facts.draft.json`, 5 questions (q1 GPU on-demand trap, q2 CPU sandbox cost with free-storage footnote, q3 signup/credit, q4 billing granularity, q5 Windows).
- If time is short, use **q1, q2, q3** only.

**Reps:** 3 per cell (5 if time allows).

**Matrix size:** 4 page conditions × 5 models × 3 questions × 3 reps = 180 runs. Most are short, and NOPAGE is a single call.

**Reader agent protocol (same for every model):**

- System prompt: "You are an AI assistant helping a customer. Use the tools to read the website. Answer ONLY from what the site says."
- Tools:
  - `open_page(path)` → page text from inside the Daytona sandbox
  - optional `list_links()`
- Final answer = **strict JSON** matching the question's `answer_schema`, plus `"evidence_quote"`, plus `"not_found": bool`.
- Max ~6 tool steps. Temperature 0 where supported. Log the full transcript and tool calls per run (JSONL).

**Reading modes:**

- v1 (must): `html_text`. Fetch HTML inside the sandbox and extract all text with BeautifulSoup (includes hidden panels, like a crawler).
- v2 (stretch): `visible_text`. Playwright in the sandbox, `page.inner_text("body")` (visible only, like a browser agent).
  - The default Daytona snapshot has `/usr/bin/chromium`. Run `pip install playwright`, then `chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])`.

## 5. Metrics (objective; graded by code, no LLM judge for headline numbers)

Per run, compare the JSON fields to gold. Numbers use a tolerance (q2 ±0.002); enums and booleans use exact match.

1. **Fact accuracy:** correct fields ÷ total fields (mean over reps)
2. **Wrong-assertion rate:** a confident wrong value (worse than `not_found`). Report correct / not_found / wrong separately.
3. **Evidence reach:** did the transcript actually open or see the text segment containing the gold value? (Check tool outputs for the gold string.)
4. **Stability:** agreement across reps
5. **Headline: worst-model accuracy per layout** ("does the layout survive the weakest AI?")
6. Cost/efficiency (optional): tool calls, tokens, latency per run

## 6. Visualizations (dashboard = single static HTML, generated from results JSONL)

1. **Heatmap:** rows = A / B / C / NOPAGE, cols = 5 models; cell = accuracy % with n; last col = worst-model accuracy.
2. **Per-fact stacked bars:** correct / not_found / wrong per question (shows *which* fact breaks, e.g., the q1 preemptible trap).
3. **Path replay:** for one question, side-by-side tool-call timeline for A vs C (pages opened, quote used). Optional: a Daytona Computer Use mp4 of a browser agent on A vs C.
4. Live during the run: a grid of Daytona sandboxes filling up (labels: layout/model/rep). Good on stage for Daytona.

**Ambiguities to verify (or exclude):**
- "*Price per GiB after first 5 free" — is that per sandbox or per org? This affects q2.
- The page does not define "preemptible".

---

## 7. Architecture and Daytona constraints (Tier 1 — confirmed in dashboard)

- **Tier 1 limits:** 10 vCPU / 10 GiB RAM / 30 GiB disk total. Sandbox creation 300/min.
- **Internet restricted** on Tier 1 and 2: an allowlist only (OpenAI, Anthropic, PyPI, npm, GitHub, … ). **Nosana endpoints are NOT on the allowlist**, and other sandboxes' preview URLs likely aren't either.
- **Preview links** show a warning page on Tier 1 and 2. Bypass it with the header `X-Daytona-Skip-Preview-Warning: true`.
- Credits: $200 free (confirmed in wallet). Expected spend is under $10.

**Therefore:**
- **The LLM agent loop runs on the laptop.** It calls Nosana, OpenAI, and Anthropic directly.
- **Each layout is served inside Daytona sandboxes on `localhost:8000`** (`python3 -m http.server`). The reader tools run inside the sandbox via `sandbox.process.exec(...)`, using curl or a python extract script. No cross-sandbox networking is needed.
- **Sandbox pool:** e.g., 3 layouts × 3 workers = 9 small sandboxes (each 1 vCPU, which fits Tier 1). Label them `{layout, worker}`.
  - Each tool call is stateless (fresh process, no cookies), which keeps each run clean.
- One extra public preview link per layout, used only for judges and for the Aside/Claude/Codex qualitative runs (signed URL, warning header).

**SDK (daytona==0.225.0, already in `.venv`):**
- `Daytona().create(CreateSandboxFromSnapshotParams(snapshot=..., labels=..., ephemeral=True, auto_stop_interval=...))`
- `sandbox.fs.upload_file(bytes, path)` / `upload_files([FileUpload(...)])`
- `sandbox.process.create_session` + `execute_session_command(SessionExecuteRequest(command=..., run_async=True))` for the http server
- `sandbox.process.exec(cmd, timeout=...)` → `.exit_code`, `.result`
- `sandbox.get_preview_link(8000)` / `create_signed_preview_url(8000, expires_in_seconds=3600)`
- `sandbox.computer_use.start()` / `.recording.start/stop/download`
- `daytona.delete(sandbox)`

Verify these signatures against the installed SDK before relying on them. Always delete sandboxes in `finally:` and run `daytona.list()` cleanup at the end.

> Note: Aside could not execute `.venv` Python (sandbox policy). **All Python runs happen in your local terminal / Claude Code.**

## 8. Infra status (as of 15:40)

| Resource | Status |
|---|---|
| `DAYTONA_API_KEY` | created 15:1x ("hacksprint-aeo", Sandboxes scope), REST check 200 OK |
| `NOSANA_API_KEY` | created 15:16 ("hacksprint-aeo", full access, expires 10/25) |
| `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` | **user pastes into `.env`** |
| Nosana qwen3.5:9b | deployment `G3yXSbA6uGCXNBCXbsTabTyLw4visAC6w9DJ9FWJ7YED`, 3090, ctx 32768, tool calls OK |
| Nosana gpt-oss:20b | deployment `SYJodXW3neMA3RVUCLwxFqVN6sw27t2K2jJHnU8xQRw`, 4090, ctx 32768, tool calls OK |
| Nosana gemma4:26b | deployment `EKN7XzSipeuNnhtWJyyHcPpNwTzChHwLvKXLEUpTJaEY`, 4090, ctx 32768, READY 15:45 |

**Nosana gotchas**

- The template's Ollama resource did NOT preload models (`/api/tags` returned empty), so models were pulled manually.
- Endpoints are **public, no auth**. Never commit or share them (they live only in `.env`).
- Deployment timeouts: qwen and gpt-oss 150 min (started ~15:15), gemma 120 min (started ~15:33). Cost ≈ $0.19 + $0.36 + $0.36 per hour.

**Commands**

```bash
# check a model is loaded (replace URL from .env, strip /v1)
curl -s $BASE/api/tags        # should list the model
curl -s $BASE/api/ps          # shows context_length (expect 32768)
# if the model list is empty -> pull again (server keeps pulling):
curl -s -N -X POST $BASE/api/pull -d '{"model":"gemma4:26b"}' | tail -c 300
# smoke test all reader models
.venv/bin/python check_models.py   # add gemma + anthropic entries to it
.venv/bin/python smoke_test.py     # Daytona
# STOP Nosana deployments after the demo (refunds unused reserve)
curl -s -X POST -H "Authorization: Bearer $NOSANA_API_KEY" https://api.nosana.com/deployments/<ID>/stop
```

**Notes**

- gpt-oss, Qwen, and Gemma may emit reasoning tokens. Give them a generous `max_tokens` and parse the JSON robustly (take the last `{...}` block).
- Ollama `OLLAMA_NUM_PARALLEL=4` per endpoint. Cap concurrency per Nosana model at 4.

## 8b. Measured latency + time budget (15:45, single call, ~860 prompt tokens = real page text)

| model | warm call | completion tokens | note |
|---|---|---|---|
| qwen3.5:9b | 3.6-3.9 s | 184 | |
| gpt-oss:20b | 2.9-3.0 s | 157 | |
| gemma4:26b | 7.2 s (first call 70 s = load) | 629 | wraps JSON in ```json fences -> parse last {...} |

- Deployment expiry: qwen/gpt-oss ~17:45, gemma ~17:33. Finish the full matrix by ~16:30 and keep results; live demo = small rerun or replay.
- Estimate (unmeasured parts: Daytona create/exec): 1 page-run = 2-3 LLM calls + 1-2 sandbox exec = ~8-25 s.
  Per model 27 page-runs + 9 NOPAGE calls; Nosana models run in parallel (own GPU each, <=4 concurrent).
  Full matrix (3 questions) ~ 6-12 min wall clock + ~2 min sandbox setup. 5 questions ~ 10-20 min.
- Status: `scripts/nosana_status.sh` (downloaded + GPU-loaded models, no URLs printed). Progress: `wc -l results/runs.jsonl`.

## 9. Qualitative column: real agent products (n=1, NOT in the heatmap)

- Run Aside, Claude, and Codex/ChatGPT agent on the **A vs C public preview links** with question q1, and capture screenshots.
- Label it "qualitative, n=1, products differ in hidden prompts/tools". Aside (in the user's browser) can run its part on request.

## 10. Priority list and cut lines (now → 17:00)

1. **15:40–16:00** Build layouts A/B/C as static HTML (`sites/A_original`, `sites/B_explicit`, `sites/C_faq_structured`).
   - A mirrors the real page structure, simplified HTML is OK, but keep the hidden on-demand panel and the footnote.
   - Then build a runner MVP with 1 model × 1 layout × q1 end-to-end through Daytona.
2. **16:00–16:20** Run the full matrix (html_text mode) → `results/runs.jsonl`.
3. **16:20–16:35** `report.py` → `results/dashboard.html` (heatmap, per-fact bars, path replay). No external CDN needed (inline SVG/HTML).
4. **16:35–16:50**
   - README (what/why/how to run/results/limitations + sponsor usage)
   - Deck PDF (≤10 MB)
   - Qualitative agent screenshots
5. **16:50–17:00** Backup screenshots/video, push the repo, submit the form.

- **Stretch:** `visible_text` mode via Playwright; Daytona Computer Use recording; Claude/OpenAI computer-use API driving a Daytona desktop.
- **Cut first if late:** q4/q5, the Anthropic column, path replay.

## 11. Deliverables

**Repo layout (suggested)**

```
README.md            # pitch, method, results table, how to run, limitations, sponsors
HANDOFF.md LOG.md
data/raw/ data/gold/
sites/A_original/ sites/B_explicit/ sites/C_faq_structured/
src/agent.py         # reader loop + tools (model-agnostic)
src/daytona_pool.py  # create/serve/exec/cleanup
src/run_matrix.py    # fan-out, writes results/runs.jsonl
src/grade.py src/report.py
results/runs.jsonl results/summary.json results/dashboard.html
deck/deck.pdf
```

- `.env` is gitignored. Double-check that no keys or Nosana URLs appear in commits (run the secret-pattern `git grep` from CLAUDE.md before pushing).
- Make the repo public only if the form requires it.

**Deck (8–10 slides, PDF ≤ 10 MB)**

1. Title + one-line pitch
2. Problem: customers ask AI agents → agents read your pages → misquotes (show the real preemptible vs on-demand example)
3. What we built (pipeline diagram: real page → layouts → Daytona fan-out → Nosana/OpenAI/Anthropic readers → grader → dashboard)
4. Method and objective metrics (gold from the real page, JSON answers, code grading, n reps, NOPAGE control)
5. Results heatmap (layout × model, worst-model column)
6. Which fact breaks (per-fact bars) + one path replay
7. Sponsor usage (Daytona: sandboxes, isolation, parallel fan-out, numbers; Nosana: 3 open models on decentralized GPUs, cost)
8. Limitations and next steps (more pages, visible-text/computer-use readers, datasets like WebSRC for external validation)
9. Team / repo link

**Demo script (3 min)**

- 0:00 problem in one sentence + the real Daytona page
- 0:30 fire the run: sandbox grid fills up
- 1:15 heatmap: A fails on q1 for small models, C fixes it, NOPAGE shows memory isn't enough
- 2:15 sponsor callouts + close

## 12. Working rules for this session

- **Language:** reply to the user in Korean (casual 반말).
- Never print, log, or commit secrets. `.env` only.
- Evidence standards:
  - Every number in the README or deck must come from `results/` files.
  - State n.
  - Separate findings from conclusions.
  - Mark unverified items.
- Log every decision, failure, and fix in `LOG.md` with a timestamp (feeds the deck and README).
- Don't expand scope. If behind schedule, cut by the order in §10.

## 13. Plan from 15:58 (agreed with user) — supersedes §10

State at 15:57:
- The html_text matrix is done: 291 runs, with 60 OpenAI runs excluded (429, no credits).
- visible_text API models are done: 90 runs.
- visible_text Nosana models (qwen, gemma) are running: 90 runs.
- Headline so far: visible_text A_original q1 got 0/6 correct (3 wrong, 3 not_found). B and C got q1 6/6 and 7/7. NOPAGE is 0–20%.

1. **15:58–16:10 Finish visible_text Nosana.** Don't start other Nosana-heavy jobs meanwhile. Then rerun grade.py and report.py.
2. **16:10–16:20 Interpretation fixes (no new runs).**
   - Show `invalid` (malformed tool call or JSON) separately in the heatmap or tooltip. The html_text drop for qwen on B (50%) comes from 3 invalid q1 outputs, not from the layout. Say so.
   - Drop the OpenAI column and mention it in Limitations ("API credits exhausted, 60 runs excluded"). Do NOT top up.
   - Headline = visible_text q1: A vs B/C per model, with n.
3. **16:20–16:40 README per docs/JUDGING.md + deck polish** (numbers only from results/, n everywhere).
4. **16:40–16:50**
   - Screenshots (dashboard, Daytona sandboxes page, Nosana deployments page).
   - Backup screen recording of a live q1 rerun (A vs C, one model, visible_text, ~30 s).
   - Secret grep.
   - Push.
5. **16:50–17:00** Submit the form. **Freeze: no new experiments after 16:40.**

Expansion:
- **IN:** visible_text for all 4 models.
- **OPTIONAL:**
  - Aside does a qualitative n=1 run on public preview URLs if they're provided by 16:30.
  - Aside builds a Level-0 access check in parallel (pure HTTP, no repo conflict: `results/access_check.json`).
- **OUT:** OpenAI column, Computer Use recording, computer-use API agents, more pages, more reps.
- Keep the Nosana deployments running until the demos end (~17:30, gemma expires ~17:33), then stop all 3.

#!/usr/bin/env bash
# Live stage demo (~30 s): q1 on layouts A vs C, visible_text reader, Claude + gpt-oss (Nosana), fresh Daytona sandboxes.
# Writes to results/demo_live.jsonl (NOT used for headline numbers).
cd "$(dirname "$0")"
.venv/bin/python -u src/run_matrix.py --models claude,gpt-oss-20b --layouts A_original,C_faq_structured \
  --questions q1 --reps 2 --workers 1 --mode visible_text --out results/demo_live.jsonl

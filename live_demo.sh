#!/usr/bin/env bash
# LIVE computer-use demo in one command:  ./live_demo.sh
# Round 1 = layout A (original tabs), Round 2 = layout C (explicit labels). Claude vs Gemma 4 (Nosana), live via Daytona noVNC.
cd "$(dirname "$0")"

echo "== 1/5 Cleaning up old live sandboxes"
python3 src/cu_live.py cleanup >/dev/null 2>&1

echo "== 2/5 Preparing 2 Daytona desktops (~40s)"
python3 src/cu_live.py prepare || { echo "prepare failed"; exit 1; }

echo "== 3/5 Opening live view"
(cd results && python3 -m http.server 8770 --bind 127.0.0.1 >/dev/null 2>&1 &)
sleep 1
open "http://127.0.0.1:8770/live/live.html"

read -r -p ">> In BOTH panes, click 'I Understand, Continue'. Then press Enter to start ROUND 1 (layout A)... "
python3 src/cu_live.py go A_original

read -r -p ">> Press Enter to start ROUND 2 (layout C)... "
python3 src/cu_live.py go C_faq_structured

read -r -p ">> Press Enter to delete the sandboxes (or Ctrl+C to keep them)... "
python3 src/cu_live.py cleanup

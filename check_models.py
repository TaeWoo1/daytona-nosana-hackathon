"""Smoke test: every reader model answers + returns a tool call (OpenAI-compatible).

Run:  .venv/bin/python check_models.py
"""
import json
import os
import time

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

MODELS = [
    ("nosana-qwen3.5-9b", os.getenv("NOSANA_QWEN_BASE_URL"), "x", os.getenv("NOSANA_QWEN_MODEL")),
    ("nosana-gpt-oss-20b", os.getenv("NOSANA_GPTOSS_BASE_URL"), "x", os.getenv("NOSANA_GPTOSS_MODEL")),
    ("openai", None, os.getenv("OPENAI_API_KEY"), os.getenv("OPENAI_MODEL", "gpt-4.1-mini")),
]

TOOLS = [{
    "type": "function",
    "function": {
        "name": "open_page",
        "description": "Open a page of the website and return its visible text.",
        "parameters": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "e.g. /pricing"}},
            "required": ["path"],
        },
    },
}]

for label, base_url, key, model in MODELS:
    if not key or not model or (label.startswith("nosana") and not base_url):
        print(f"[skip] {label}: missing env")
        continue
    client = OpenAI(base_url=base_url, api_key=key) if base_url else OpenAI(api_key=key)
    t = time.time()
    try:
        r = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "How much does the Pro plan cost? Check the /pricing page."}],
            tools=TOOLS,
            timeout=120,
        )
        msg = r.choices[0].message
        calls = [(c.function.name, json.loads(c.function.arguments)) for c in (msg.tool_calls or [])]
        print(f"[ok] {label} ({model}) {time.time()-t:.1f}s tool_calls={calls} text={(msg.content or '')[:80]!r}")
    except Exception as e:  # noqa: BLE001
        print(f"[fail] {label} ({model}) {type(e).__name__}: {e}")

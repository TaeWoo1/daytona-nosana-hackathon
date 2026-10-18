"""Model-agnostic reader agent. The LLM loop runs on the laptop; open_page executes inside a Daytona sandbox."""
import json
import os
import re
import time

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

SYSTEM_PAGE = (
    "You are an AI assistant helping a customer of the company Daytona. Use the tools to read the company website "
    "(start with open_page('/pricing')). Answer ONLY from what the site says."
)
SYSTEM_NOPAGE = (
    "You are an AI assistant helping a customer of the company Daytona (daytona.io, a sandbox/compute platform). "
    "You have no tools. Answer from your own knowledge."
)

TOOLS = [{
    "type": "function",
    "function": {
        "name": "open_page",
        "description": "Open a page of the company website and return its text.",
        "parameters": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "URL path, e.g. /pricing"}},
            "required": ["path"],
        },
    },
}]


def models():
    """Reader models that have env configured. id -> (client, model_name, extra_kwargs, concurrency)."""
    out = {}
    nos = [("qwen3.5-9b", "QWEN"), ("gpt-oss-20b", "GPTOSS"), ("gemma4-26b", "GEMMA")]
    for mid, k in nos:
        url, name = os.getenv(f"NOSANA_{k}_BASE_URL"), os.getenv(f"NOSANA_{k}_MODEL")
        if url and name:
            out[mid] = (OpenAI(base_url=url, api_key="x", timeout=300, max_retries=1), name, {"max_tokens": 8192}, 4)
    if os.getenv("ANTHROPIC_API_KEY"):
        out["claude"] = (OpenAI(base_url="https://api.anthropic.com/v1/", api_key=os.getenv("ANTHROPIC_API_KEY"),
                                timeout=120, max_retries=2),
                         os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5"), {"max_tokens": 2048}, 4)
    if os.getenv("OPENAI_API_KEY"):
        out["openai"] = (OpenAI(api_key=os.getenv("OPENAI_API_KEY"), timeout=120, max_retries=2),
                         os.getenv("OPENAI_MODEL", "gpt-4.1-mini"), {"max_tokens": 2048}, 4)
    return out


def format_instructions(q):
    def hint(v):
        if "|" in v and v.split("|")[0] not in ("number", "boolean", "string"):
            return "one of " + " / ".join(f'"{x}"' for x in v.split("|")) + " (a JSON string)"
        return v.replace("|", " or ")
    fields = ", ".join(f'"{k}": {hint(v)}' for k, v in q["answer_schema"].items())
    return (
        f"Customer question: {q['user_question']}\n\n"
        "When you are done, reply with ONLY one JSON object (no markdown) with these keys:\n"
        f"{{{fields}, \"evidence_quote\": string (exact text you relied on, or \"\"), \"not_found\": boolean}}\n"
        "Use null and not_found=true if the information is not available."
    )


def parse_json(text):
    if not text:
        return None
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S)
    # lenient: quote bare enum words like `: unknown,`
    text = re.sub(r':\s*(preemptible|on_demand|unknown|per_hour|per_minute|per_second)\s*([,}])', r': "\1"\2', text)
    cands = re.findall(r"\{.*\}", text, flags=re.S)
    for c in reversed(cands):
        # try progressively from each '{' so we get the last complete object
        for i in [m.start() for m in re.finditer(r"\{", c)]:
            try:
                return json.loads(c[i:])
            except json.JSONDecodeError:
                continue
    return None


def run(model_id, client, model_name, extra, q, page_fn=None, max_steps=6):
    """page_fn(path) -> text, or None for NOPAGE. Returns a run record (without grading)."""
    t0 = time.time()
    msgs = [{"role": "system", "content": SYSTEM_PAGE if page_fn else SYSTEM_NOPAGE},
            {"role": "user", "content": format_instructions(q)}]
    tool_log, usage, final, err, nudged = [], {"prompt": 0, "completion": 0}, None, None, False
    try:
        for step in range(max_steps + 1):
            kw = dict(model=model_name, messages=msgs, temperature=0, **extra)
            if page_fn and step < max_steps:
                kw["tools"] = TOOLS
            elif page_fn:
                msgs.append({"role": "user", "content": "Stop using tools now and reply with the JSON object only."})
            r = client.chat.completions.create(**kw)
            if r.usage:
                usage["prompt"] += r.usage.prompt_tokens or 0
                usage["completion"] += r.usage.completion_tokens or 0
            m = r.choices[0].message
            calls = m.tool_calls or []
            if not calls:
                final = m.content or ""
                if parse_json(final) is None and step < max_steps:
                    # reasoning models sometimes end with empty/invalid content: one nudge without tools
                    msgs.append({"role": "assistant", "content": final})
                    msgs.append({"role": "user", "content": "Reply now with the JSON object only, valid JSON, no other text."})
                    r = client.chat.completions.create(model=model_name, messages=msgs, temperature=0, **extra)
                    if r.usage:
                        usage["prompt"] += r.usage.prompt_tokens or 0
                        usage["completion"] += r.usage.completion_tokens or 0
                    final = r.choices[0].message.content or ""
                    nudged = True
                break
            msgs.append({"role": "assistant", "content": m.content or "",
                         "tool_calls": [{"id": c.id, "type": "function",
                                         "function": {"name": c.function.name, "arguments": c.function.arguments}}
                                        for c in calls]})
            for c in calls:
                try:
                    args = json.loads(c.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}
                path = args.get("path", "/pricing")
                ts = time.time()
                out = page_fn(path) if c.function.name == "open_page" else f"ERROR: unknown tool {c.function.name}"
                tool_log.append({"name": c.function.name, "path": path, "output": out, "sec": round(time.time() - ts, 2)})
                msgs.append({"role": "tool", "tool_call_id": c.id, "content": out})
    except Exception as e:  # noqa: BLE001
        err = f"{type(e).__name__}: {str(e)[:300]}"
    return {
        "model": model_id, "model_name": model_name, "question": q["id"],
        "answer": parse_json(final), "final_text": final, "tool_calls": tool_log,
        "n_tool_calls": len(tool_log), "nudged": nudged, "usage": usage, "latency_sec": round(time.time() - t0, 2), "error": err,
    }

"""Computer-use demo (qualitative, n=1 per layout). Python stdlib only (REST, no SDK).

Daytona sandbox desktop (Xvfb) -> Chromium shows our styled site -> screenshot (pixels only) ->
Claude (vision) chooses click(x,y) / scroll / answer -> Daytona mouse API executes -> repeat.
The whole session is recorded with the Daytona recording API (mp4).

usage: python3 src/cu_demo_stdlib.py A_original|C_faq_structured
outputs: results/cu_aside/<layout>/step_N.png, run.json, recording.mp4
"""
import base64, io, json, os, sys, tarfile, time, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV = {}
for ln in open(os.path.join(ROOT, ".env")):
    if "=" in ln and not ln.lstrip().startswith("#"):
        k, v = ln.strip().split("=", 1); ENV[k] = v
DK, AK = ENV["DAYTONA_API_KEY"], ENV["ANTHROPIC_API_KEY"]
MODEL = ENV.get("ANTHROPIC_MODEL", "claude-sonnet-4-5")
API = "https://app.daytona.io/api"
LAYOUT = sys.argv[1] if len(sys.argv) > 1 else "A_original"
READER = sys.argv[2] if len(sys.argv) > 2 else "claude"  # claude | gemma (Nosana, OpenAI-compatible vision)
if READER == "gemma":
    MODEL = ENV.get("NOSANA_GEMMA_MODEL", "gemma4:26b")
OUT = os.path.join(ROOT, "results", "cu_aside", LAYOUT + ("" if READER == "claude" else "_" + READER)); os.makedirs(OUT, exist_ok=True)
Q = "I need an RTX 4090 GPU sandbox that will not be interrupted. How much per hour?"


def req(method, url, body=None, headers=None, raw=False, timeout=60):
    h = {"Authorization": f"Bearer {DK}", "Content-Type": "application/json"}
    h.update(headers or {})
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            b = resp.read()
            return b if raw else (json.loads(b) if b else {})
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{method} {url} -> {e.code} {e.read()[:300]!r}")


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


# 1) sandbox
sb = req("POST", f"{API}/sandbox", {"snapshot": "daytona-medium", "labels": {"app": "agentreadable", "kind": "computer-use", "layout": LAYOUT}, "autoStopInterval": 15})
sid = sb["id"]; log("sandbox", sid)
for _ in range(60):
    sb = req("GET", f"{API}/sandbox/{sid}")
    if sb.get("state") == "started": break
    time.sleep(2)
TB = (sb.get("toolboxProxyUrl") or "https://proxy.app.daytona.io/toolbox").rstrip("/") + f"/{sid}"
log("state", sb.get("state"))


def ex(cmd, timeout=30):
    return req("POST", f"{TB}/process/execute", {"command": cmd, "timeout": timeout}, timeout=timeout + 15)


run = {"layout": LAYOUT, "model": MODEL, "sandbox_id": sid, "question": Q, "steps": [], "answer": None, "error": None}
try:
    # 2) upload site (tar.gz via base64) + serve
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        tf.add(os.path.join(ROOT, "sites_v2", LAYOUT), arcname="site")
    b64 = base64.b64encode(buf.getvalue()).decode()
    ex(f"bash -c 'mkdir -p /tmp/w && echo {b64} | base64 -d | tar xz -C /tmp/w'")
    ex("bash -c 'cd /tmp/w/site && (setsid nohup python3 -m http.server 8000 >/tmp/http.log 2>&1 &)'")
    time.sleep(1)
    log("serve check", str(ex("curl -s -o /dev/null -w %{http_code} http://localhost:8000/pricing/"))[:120])

    # 3) desktop + browser + recording
    log("cu start", str(req("POST", f"{TB}/computeruse/start", {}))[:160])
    time.sleep(4)
    ex("bash -c 'export DISPLAY=:0; (setsid nohup chromium --no-sandbox --no-first-run --disable-infobars --start-maximized --window-position=0,0 --window-size=1280,800 --app=http://localhost:8000/pricing/ >/tmp/chr.log 2>&1 &)'")
    time.sleep(6)
    rec = req("POST", f"{TB}/computeruse/recordings/start", {"label": f"agentreadable-{LAYOUT}"})
    rec_id = rec.get("id"); log("recording", rec_id)
    time.sleep(1)

    tools = [
        {"name": "click", "description": "Left-click at pixel (x, y) of the screenshot.",
         "input_schema": {"type": "object", "properties": {"x": {"type": "integer"}, "y": {"type": "integer"}, "why": {"type": "string"}}, "required": ["x", "y"]}},
        {"name": "scroll", "description": "Scroll the page down or up by a few notches at the screen center.",
         "input_schema": {"type": "object", "properties": {"direction": {"type": "string", "enum": ["down", "up"]}, "amount": {"type": "integer"}}, "required": ["direction"]}},
        {"name": "answer", "description": "Give the final answer to the customer.",
         "input_schema": {"type": "object", "properties": {"usd_per_hour": {"type": ["number", "null"]}, "pricing_type": {"type": "string", "enum": ["preemptible", "on_demand", "unknown"]}, "evidence": {"type": "string"}}, "required": ["usd_per_hour", "pricing_type"]}},
    ]
    system = ("You are an AI assistant helping a customer by operating a web browser. You only see screenshots of the screen. "
              "Use click/scroll to navigate the website shown, then call answer. Answer ONLY from what the site shows. Max 6 actions.")
    msgs = []
    for step in range(1, 8):
        shot = req("GET", f"{TB}/computeruse/screenshot?showCursor=true")
        png_b64 = shot["screenshot"]
        open(os.path.join(OUT, f"step_{step}.png"), "wb").write(base64.b64decode(png_b64))
        content = [{"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": png_b64}}]
        if step == 1:
            content.append({"type": "text", "text": f"Customer question: {Q}"})
        if msgs and msgs[-1]["role"] == "user":
            msgs[-1]["content"].extend(content)
        else:
            msgs.append({"role": "user", "content": content})
        t0 = time.time()
        if READER == "gemma":
            oa_tools = [{"type": "function", "function": {"name": t["name"], "description": t["description"], "parameters": t["input_schema"]}} for t in tools]
            oa_msgs = [{"role": "system", "content": system}]
            for m in msgs:
                if m["role"] == "assistant":
                    oa_msgs.append(m["oa"])
                    continue
                parts = []
                for c in m["content"]:
                    if c["type"] == "image":
                        parts.append({"type": "image_url", "image_url": {"url": "data:image/png;base64," + c["source"]["data"]}})
                    elif c["type"] == "text":
                        parts.append({"type": "text", "text": c["text"]})
                    elif c["type"] == "tool_result":
                        oa_msgs.append({"role": "tool", "tool_call_id": c["tool_use_id"], "content": c["content"]})
                if parts:
                    oa_msgs.append({"role": "user", "content": parts})
            base = ENV["NOSANA_GEMMA_BASE_URL"].rstrip("/")
            o = req("POST", base + "/chat/completions", {"model": MODEL, "temperature": 0, "messages": oa_msgs, "tools": oa_tools}, headers={"Authorization": "Bearer x"}, timeout=180)
            om = o["choices"][0]["message"]
            content = []
            if om.get("content"):
                content.append({"type": "text", "text": om["content"]})
            for tc in (om.get("tool_calls") or []):
                content.append({"type": "tool_use", "id": tc["id"], "name": tc["function"]["name"], "input": json.loads(tc["function"]["arguments"] or "{}")})
            resp = {"content": content}
            msgs.append({"role": "assistant", "content": content, "oa": {"role": "assistant", "content": om.get("content") or "", "tool_calls": om.get("tool_calls") or []}})
        else:
          resp = req("POST", "https://api.anthropic.com/v1/messages",
                   {"model": MODEL, "max_tokens": 800, "temperature": 0, "system": system, "tools": tools, "messages": msgs},
                   headers={"Authorization": "", "x-api-key": AK, "anthropic-version": "2023-06-01"}, timeout=120)
          msgs.append({"role": "assistant", "content": resp["content"]})
        uses = [c for c in resp["content"] if c["type"] == "tool_use"]
        text = " ".join(c.get("text", "") for c in resp["content"] if c["type"] == "text")
        if not uses:
            run["steps"].append({"step": step, "frame": f"step_{step}.png", "action": "none", "text": text}); break
        u = uses[0]; act = u["name"]; inp = u["input"]
        run["steps"].append({"step": step, "frame": f"step_{step}.png", "action": act, "input": inp, "text": text, "llm_sec": round(time.time() - t0, 2)})
        log(f"step {step}: {act} {json.dumps(inp)[:160]}")
        results = []
        if act == "answer":
            run["answer"] = inp; break
        if act == "click":
            req("POST", f"{TB}/computeruse/mouse/click", {"x": int(inp["x"]), "y": int(inp["y"]), "button": "left"})
        elif act == "scroll":
            req("POST", f"{TB}/computeruse/mouse/scroll", {"x": 640, "y": 400, "direction": inp.get("direction", "down"), "amount": int(inp.get("amount", 3))})
        time.sleep(1.2)
        for x in uses:
            results.append({"type": "tool_result", "tool_use_id": x["id"], "content": "done; new screenshot follows" if x is u else "ignored (one action per step)"})
        msgs.append({"role": "user", "content": results})
    time.sleep(1.5)
    try:
        req("POST", f"{TB}/computeruse/recordings/stop", {"id": rec_id})
        time.sleep(2)
        mp4 = req("GET", f"{TB}/computeruse/recordings/{rec_id}/download", raw=True, timeout=120)
        open(os.path.join(OUT, "recording.mp4"), "wb").write(mp4); log("recording bytes", len(mp4))
    except Exception as e:  # noqa: BLE001
        run["recording_error"] = str(e)[:300]; log("recording error", e)
except Exception as e:  # noqa: BLE001
    run["error"] = str(e)[:500]; log("ERROR", e)
finally:
    a = run["answer"] or {}
    run["verdict"] = "correct" if (a.get("usd_per_hour") == 0.99 and a.get("pricing_type") == "on_demand") else ("not_found" if a.get("usd_per_hour") is None else "wrong")
    json.dump(run, open(os.path.join(OUT, "run.json"), "w"), indent=2)
    log("verdict", run["verdict"], json.dumps(a)[:200])
    try:
        req("DELETE", f"{API}/sandbox/{sid}")
    except Exception as e:  # noqa: BLE001
        log("delete error", e)

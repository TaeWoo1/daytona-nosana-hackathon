"""LIVE computer-use demo: 4 Daytona desktops (Claude/Gemma x layout A/C) you can watch in real time.

  python3 src/cu_live.py prepare   # ~40 s: create 4 public sandboxes, serve sites, start desktop + Chromium (kiosk)
                                   #        writes results/live/state.json and results/live/live.html
  (open live.html via:  cd results && python3 -m http.server 8770  ->  http://127.0.0.1:8770/live/live.html
   click "I Understand, Continue" once in each of the 4 panes, before going on stage)
  python3 src/cu_live.py go A_original   # round 1, then: go C_faq_structured  # round 2. On stage: 4 agents act in parallel; panes show cursor + clicks live,
                                   #           captions/verdicts update from results/live/events.json
  python3 src/cu_live.py cleanup   # delete the 4 sandboxes

Python stdlib only (Daytona REST + Anthropic API + Nosana OpenAI-compatible). Qualitative demo, n=1 per pane.
"""
import base64, io, json, os, sys, tarfile, threading, time, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV = {}
for ln in open(os.path.join(ROOT, ".env")):
    if "=" in ln and not ln.lstrip().startswith("#"):
        k, v = ln.strip().split("=", 1); ENV[k] = v
DK, AK = ENV["DAYTONA_API_KEY"], ENV.get("ANTHROPIC_API_KEY", "")
API = "https://app.daytona.io/api"
LIVE = os.path.join(ROOT, "results", "live"); os.makedirs(LIVE, exist_ok=True)
STATE, EVENTS = os.path.join(LIVE, "state.json"), os.path.join(LIVE, "events.json")
Q = "I need an RTX 4090 GPU sandbox that will not be interrupted. How much per hour?"
PANES = [("claude", "both"), ("gemma", "both")]  # 2 panes (Tier 1: 10 GiB RAM total); each serves both layouts
LAYOUTS = ["A_original", "C_faq_structured"]
W, H = 1024, 768
LOCK = threading.Lock()


def req(method, url, body=None, headers=None, raw=False, timeout=60):
    h = {"Authorization": f"Bearer {DK}", "Content-Type": "application/json"}
    h.update(headers or {})
    r = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            b = resp.read()
            return b if raw else (json.loads(b) if b else {})
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{method} {url.split('?')[0]} -> {e.code} {e.read()[:200]!r}")


def tb(sid):
    return f"https://proxy.app.daytona.io/toolbox/{sid}"


def ex(sid, cmd, timeout=30):
    return req("POST", f"{tb(sid)}/process/execute", {"command": cmd, "timeout": timeout}, timeout=timeout + 15)


def emit(key, **kw):
    with LOCK:
        ev = json.load(open(EVENTS)) if os.path.exists(EVENTS) else {}
        if kw.pop("steps_reset", False):
            ev[key] = {"steps": []}
        ev.setdefault(key, {"steps": []})
        if "step" in kw:
            ev[key]["steps"].append(kw["step"])
        for k, v in kw.items():
            if k != "step":
                ev[key][k] = v
        ev["_updated"] = time.strftime("%H:%M:%S")
        json.dump(ev, open(EVENTS + ".tmp", "w")); os.replace(EVENTS + ".tmp", EVENTS)


def open_layout(sid, layout):
    ex(sid, "bash -c 'pkill -x chromium; pkill -x chrome; true'")
    time.sleep(1)
    ex(sid, "bash -c 'export DISPLAY=:0; (setsid nohup chromium --no-sandbox --test-type --no-first-run "
            f"--kiosk --user-data-dir=/tmp/chr-{layout} http://localhost:{8000 + LAYOUTS.index(layout)}/pricing/ >/tmp/chr.log 2>&1 &)'")


def prepare_one(reader, layout):
    sb = req("POST", f"{API}/sandbox", {"snapshot": "daytona-medium", "public": True, "autoStopInterval": 30,
                                       "labels": {"app": "agentreadable", "kind": "live-cu", "pane": f"{reader}-{layout}"}})
    sid = sb["id"]
    for _ in range(60):
        if req("GET", f"{API}/sandbox/{sid}").get("state") == "started": break
        time.sleep(2)
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        for L in LAYOUTS:
            tf.add(os.path.join(ROOT, "sites_v2", L), arcname=L)
    ex(sid, f"bash -c 'mkdir -p /tmp/w && echo {base64.b64encode(buf.getvalue()).decode()} | base64 -d | tar xz -C /tmp/w'")
    for i, L in enumerate(LAYOUTS):  # each layout at its own root so absolute links (/pricing/) work
        ex(sid, f"bash -c 'cd /tmp/w/{L} && (setsid nohup python3 -m http.server {8000 + i} >/tmp/http{i}.log 2>&1 &)'")
    req("POST", f"{tb(sid)}/computeruse/start", {}); time.sleep(4)
    open_layout(sid, "A_original")
    pv = req("GET", f"{API}/sandbox/{sid}/ports/6080/preview-url")
    vnc = pv["url"] + "/vnc.html?autoconnect=true&resize=scale&view_only=true&show_dot=true"
    return {"reader": reader, "layout": layout, "sid": sid, "vnc": vnc}


LIVE_HTML = r"""<!doctype html><html><head><meta charset="utf-8"><title>AgentReadable LIVE</title>
<style>body{margin:0;background:#0a0a0a;color:#eee;font-family:Inter,system-ui,sans-serif}
h1{margin:10px 18px 4px;font-size:22px}.sub{margin:0 18px 8px;color:#999;font-size:14px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;padding:0 12px 12px}
.pane{background:#151515;border:1px solid #2a2a2a;border-radius:10px;overflow:hidden;position:relative}
.hdr{display:flex;justify-content:space-between;align-items:center;padding:6px 10px;font-size:14px}
.tag{font-weight:700}.v{padding:2px 8px;border-radius:6px;font-weight:700;font-size:13px}
.ok{background:#2e7d32}.bad{background:#c62828}.nf{background:#b26a00}.run{background:#333}
iframe{width:100%;aspect-ratio:4/3;border:0;display:block;background:#000}
.cap{background:#1d1d1d;border-top:1px solid #2a2a2a;padding:8px 10px;font-size:16px;min-height:22px;color:#ffd27a}
</style></head><body>
<h1>LIVE · AI agents operating real browsers inside Daytona sandboxes</h1>
<div class="sub">Q: "I need an RTX 4090 that will not be interrupted. How much per hour?" · gold $0.99/h on-demand · agents see only screenshots and click by pixel</div>
<div class="grid" id="g"></div>
<script>
const S = __STATE__;
const names={claude:"Claude (API)",gemma:"Gemma 4 26B · open model on Nosana GPU"}, lays={A_original:"Round 1 · Layout A (original tabs)",C_faq_structured:"Round 2 · Layout C (explicit labels)"};
const g=document.getElementById('g');
S.forEach(p=>{const k=p.reader;g.insertAdjacentHTML('beforeend',
 `<div class="pane"><div class="hdr"><span class="tag">${names[p.reader]} <span id="l-${k}" style="color:#9ab"></span></span><span class="v run" id="v-${k}">ready</span></div>
  <iframe src="${p.vnc}"></iframe><div class="cap" id="c-${k}">waiting…</div></div>`)});
async function tick(){try{const r=await fetch('events.json?'+Date.now());const ev=await r.json();
 S.forEach(p=>{const k=p.reader,e=ev[k];if(!e)return;if(e.layout)document.getElementById('l-'+k).textContent='· '+lays[e.layout];const st=e.steps[e.steps.length-1];
  if(st)document.getElementById('c-'+k).textContent=`step ${st.n}: ${st.text}`;
  const v=document.getElementById('v-'+k);
  if(e.verdict){v.textContent=e.verdict==='correct'?'✓ $0.99 correct':(e.verdict==='wrong'?'✗ '+(e.answer_text||'wrong'):'∅ no answer');v.className='v '+(e.verdict==='correct'?'ok':e.verdict==='wrong'?'bad':'nf');}
  else {v.textContent='running…';v.className='v run'}})}catch(e){}}
setInterval(tick,700);
</script></body></html>"""


def prepare():
    if os.path.exists(EVENTS): os.remove(EVENTS)
    out = [None] * len(PANES)
    def w(i, p):
        out[i] = prepare_one(*p); print("ready", p, out[i]["sid"], flush=True)
    ts = [threading.Thread(target=w, args=(i, p)) for i, p in enumerate(PANES)]
    [t.start() for t in ts]; [t.join() for t in ts]
    json.dump(out, open(STATE, "w"), indent=2)
    open(os.path.join(LIVE, "live.html"), "w").write(LIVE_HTML.replace("__STATE__", json.dumps(out)))
    print("open: cd results && python3 -m http.server 8770  ->  http://127.0.0.1:8770/live/live.html")


TOOLS = [
    {"name": "click", "description": f"Left-click at pixel (x, y). The screenshot is exactly {W}x{H} pixels; (0,0) is top-left.",
     "input_schema": {"type": "object", "properties": {"x": {"type": "integer"}, "y": {"type": "integer"}, "why": {"type": "string"}}, "required": ["x", "y", "why"]}},
    {"name": "scroll", "description": "Scroll the page.", "input_schema": {"type": "object", "properties": {"direction": {"type": "string", "enum": ["down", "up"]}, "why": {"type": "string"}}, "required": ["direction"]}},
    {"name": "answer", "description": "Final answer to the customer.",
     "input_schema": {"type": "object", "properties": {"usd_per_hour": {"type": ["number", "null"]}, "pricing_type": {"type": "string", "enum": ["preemptible", "on_demand", "unknown"]}, "evidence": {"type": "string"}}, "required": ["usd_per_hour", "pricing_type"]}},
]
SYSTEM = (f"You are an AI assistant helping a customer by operating a web browser. You only see screenshots ({W}x{H} pixels). "
          "Use click/scroll to navigate, then call answer. Answer ONLY from what the site shows. One action per turn, max 6 actions.")


def llm(reader, msgs):
    if reader == "claude":
        r = req("POST", "https://api.anthropic.com/v1/messages",
                {"model": ENV.get("ANTHROPIC_MODEL", "claude-sonnet-4-5"), "max_tokens": 600, "temperature": 0, "system": SYSTEM, "tools": TOOLS, "messages": msgs},
                headers={"Authorization": "", "x-api-key": AK, "anthropic-version": "2023-06-01"}, timeout=120)
        return r["content"], {"role": "assistant", "content": r["content"]}
    oa = [{"role": "system", "content": SYSTEM}]
    for m in msgs:
        if m["role"] == "assistant":
            oa.append(m["oa"]); continue
        parts = []
        for c in m["content"]:
            if c["type"] == "image":
                parts.append({"type": "image_url", "image_url": {"url": "data:image/png;base64," + c["source"]["data"]}})
            elif c["type"] == "text":
                parts.append({"type": "text", "text": c["text"]})
            elif c["type"] == "tool_result":
                oa.append({"role": "tool", "tool_call_id": c["tool_use_id"], "content": c["content"]})
        if parts:
            oa.append({"role": "user", "content": parts})
    tools = [{"type": "function", "function": {"name": t["name"], "description": t["description"], "parameters": t["input_schema"]}} for t in TOOLS]
    o = req("POST", ENV["NOSANA_GEMMA_BASE_URL"].rstrip("/") + "/chat/completions",
            {"model": ENV.get("NOSANA_GEMMA_MODEL", "gemma4:26b"), "temperature": 0, "messages": oa, "tools": tools},
            headers={"Authorization": "Bearer x"}, timeout=180)["choices"][0]["message"]
    content = ([{"type": "text", "text": o["content"]}] if o.get("content") else []) + [
        {"type": "tool_use", "id": tc["id"], "name": tc["function"]["name"], "input": json.loads(tc["function"]["arguments"] or "{}")} for tc in (o.get("tool_calls") or [])]
    return content, {"role": "assistant", "content": content, "oa": {"role": "assistant", "content": o.get("content") or "", "tool_calls": o.get("tool_calls") or []}}


def run_pane(p, layout):
    key, sid = p["reader"], p["sid"]
    outdir = os.path.join(LIVE, f"{p['reader']}_{layout}"); os.makedirs(outdir, exist_ok=True)
    rec = {}
    try:
        rec = req("POST", f"{tb(sid)}/computeruse/recordings/start", {"label": key})
    except Exception:  # noqa: BLE001
        pass
    emit(key, verdict=None, layout=layout, steps_reset=True)
    msgs, answer = [], None
    try:
        for n in range(1, 8):
            png = req("GET", f"{tb(sid)}/computeruse/screenshot?showCursor=true")["screenshot"]
            open(os.path.join(outdir, f"step_{n}.png"), "wb").write(base64.b64decode(png))
            content = [{"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": png}}]
            if n == 1:
                content.append({"type": "text", "text": f"Customer question: {Q}"})
            if msgs and msgs[-1]["role"] == "user":
                msgs[-1]["content"].extend(content)
            else:
                msgs.append({"role": "user", "content": content})
            emit(key, step={"n": n, "text": "looking at the screen…"})
            content, amsg = llm(p["reader"], msgs); msgs.append(amsg)
            uses = [c for c in content if c["type"] == "tool_use"]
            if not uses:
                emit(key, step={"n": n, "text": "(no action)"}); break
            u = uses[0]; a, inp = u["name"], u["input"]
            if a == "answer":
                answer = inp
                emit(key, step={"n": n, "text": f"answer: ${inp.get('usd_per_hour')} ({inp.get('pricing_type')})"}); break
            if a == "click":
                emit(key, step={"n": n, "text": f"click ({inp.get('x')},{inp.get('y')}) — {inp.get('why', '')[:90]}"})
                req("POST", f"{tb(sid)}/computeruse/mouse/click", {"x": int(inp["x"]), "y": int(inp["y"]), "button": "left"})
            else:
                emit(key, step={"n": n, "text": f"scroll {inp.get('direction', 'down')}"})
                req("POST", f"{tb(sid)}/computeruse/mouse/scroll", {"x": W // 2, "y": H // 2, "direction": inp.get("direction", "down"), "amount": 3})
            time.sleep(1.0)
            msgs.append({"role": "user", "content": [{"type": "tool_result", "tool_use_id": x["id"], "content": "done; new screenshot follows" if x is u else "ignored"} for x in uses]})
    except Exception as e:  # noqa: BLE001
        emit(key, step={"n": 0, "text": f"error: {str(e)[:120]}"})
    a = answer or {}
    verdict = "correct" if (a.get("usd_per_hour") == 0.99 and a.get("pricing_type") == "on_demand") else ("no_answer" if a.get("usd_per_hour") is None else "wrong")
    emit(key, verdict=verdict, answer=a, answer_text=f"${a.get('usd_per_hour')} '{a.get('pricing_type')}'")
    try:
        if rec.get("id"):
            req("POST", f"{tb(sid)}/computeruse/recordings/stop", {"id": rec["id"]}); time.sleep(2)
            open(os.path.join(outdir, "recording.mp4"), "wb").write(req("GET", f"{tb(sid)}/computeruse/recordings/{rec['id']}/download", raw=True, timeout=120))
    except Exception:  # noqa: BLE001
        pass
    json.dump({"pane": key, "answer": a, "verdict": verdict}, open(os.path.join(outdir, "run.json"), "w"))
    print(key, verdict, json.dumps(a)[:120], flush=True)


def go():
    layout = sys.argv[2] if len(sys.argv) > 2 else "A_original"
    st = json.load(open(STATE))
    for p in st:  # fresh browser on the requested layout
        open_layout(p["sid"], layout)
    time.sleep(5)
    ts = [threading.Thread(target=run_pane, args=(p, layout)) for p in st]
    [t.start() for t in ts]; [t.join() for t in ts]


def cleanup():
    for p in json.load(open(STATE)):
        try:
            req("DELETE", f"{API}/sandbox/{p['sid']}"); print("deleted", p["sid"])
        except Exception as e:  # noqa: BLE001
            print("delete error", e)


if __name__ == "__main__":
    {"prepare": prepare, "go": go, "cleanup": cleanup}[sys.argv[1] if len(sys.argv) > 1 else "prepare"]()

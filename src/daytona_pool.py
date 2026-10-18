"""Daytona sandbox pool: one or more sandboxes per layout, each serving that layout on localhost:8000.

Reader tools run inside the sandbox via process.exec (fresh process per call, no cookies).
"""
import itertools
import threading
import time
from pathlib import Path

from daytona import CreateSandboxFromSnapshotParams, Daytona, FileUpload, SessionExecuteRequest

ROOT = Path(__file__).resolve().parent.parent
SITE_DIR = "/home/daytona/site"
EXTRACT = "/home/daytona/extract.py"
RENDER = "/home/daytona/render.py"


class Pool:
    def __init__(self, layouts, workers_per_layout=2, log=print, render=False, sites_dir="sites"):
        self.render = render
        self.sites_dir = sites_dir
        self.d = Daytona()
        self.layouts = layouts
        self.workers = workers_per_layout
        self.log = log
        self.sandboxes = {}  # layout -> [sandbox]
        self._rr = {}
        self._lock = threading.Lock()

    def _make(self, layout, w):
        t = time.time()
        sb = self.d.create(CreateSandboxFromSnapshotParams(
            language="python",
            labels={"project": "agentreadable", "layout": layout, "worker": str(w)},
            ephemeral=True, auto_stop_interval=30,
        ), timeout=120)
        site = ROOT / self.sites_dir / layout
        files = [FileUpload(source=str(p), destination=f"{SITE_DIR}/{p.relative_to(site)}") for p in site.rglob("*.html")]
        files.append(FileUpload(source=str(ROOT / "src/sandbox_extract.py"), destination=EXTRACT))
        files.append(FileUpload(source=str(ROOT / "src/sandbox_render.py"), destination=RENDER))
        sb.fs.upload_files(files)
        if self.render:
            r = sb.process.exec("pip install -q playwright", timeout=240)
            if r.exit_code != 0:
                raise RuntimeError(f"playwright install failed in {layout}/{w}: {r.result[-300:]}")
        sb.process.create_session("http")
        sb.process.execute_session_command("http", SessionExecuteRequest(
            command=f"cd {SITE_DIR} && python3 -m http.server 8000", run_async=True))
        for _ in range(20):
            r = sb.process.exec("curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/pricing/", timeout=10)
            if r.result.strip().endswith("200"):
                break
            time.sleep(0.5)
        else:
            raise RuntimeError(f"server not up in sandbox {layout}/{w}")
        self.log(f"[sandbox] {layout}/w{w} ready id={sb.id[:8]} in {time.time()-t:.1f}s")
        return sb

    def start(self):
        from concurrent.futures import ThreadPoolExecutor
        jobs = [(l, w) for l in self.layouts for w in range(self.workers)]
        with ThreadPoolExecutor(len(jobs)) as ex:
            for (l, w), sb in zip(jobs, ex.map(lambda j: self._make(*j), jobs)):
                self.sandboxes.setdefault(l, []).append(sb)
        self._rr = {l: itertools.cycle(sbs) for l, sbs in self.sandboxes.items()}

    def pick(self, layout):
        with self._lock:
            return next(self._rr[layout])

    def open_page(self, sb, path, mode="html_text"):
        path = str(path).replace("'", "")
        r = sb.process.exec(f"python3 {EXTRACT} '{path}' {mode}", timeout=30)
        return r.result

    def render_page(self, sb, path, clicks, local_png):
        """Real Chromium render inside the sandbox; replays clicks; downloads the full-page screenshot."""
        import json
        import shlex
        import uuid
        remote = f"/tmp/shot_{uuid.uuid4().hex[:8]}.png"
        cmd = f"python3 {RENDER} {shlex.quote(str(path))} {shlex.quote(json.dumps(clicks))} {remote}"
        r = sb.process.exec(cmd, timeout=60)
        frame = None
        try:
            Path(local_png).parent.mkdir(parents=True, exist_ok=True)
            Path(local_png).write_bytes(sb.fs.download_file(remote))
            frame = str(Path(local_png).relative_to(ROOT / "results"))
        except Exception as e:  # noqa: BLE001
            self.log(f"[sandbox] screenshot download failed: {type(e).__name__}")
        return r.result, frame

    def close(self):
        for sbs in self.sandboxes.values():
            for sb in sbs:
                try:
                    self.d.delete(sb)
                except Exception as e:  # noqa: BLE001
                    self.log(f"[sandbox] delete failed {sb.id[:8]}: {e}")
        self.sandboxes = {}


def cleanup_all(log=print):
    d = Daytona()
    from daytona import ListSandboxesQuery
    n = 0
    for sb in d.list(ListSandboxesQuery(labels={"project": "agentreadable"})):
        d.delete(sb)
        n += 1
    log(f"[sandbox] cleanup deleted {n}")


if __name__ == "__main__":
    p = Pool(["A_original"], 1)
    try:
        p.start()
        sb = p.pick("A_original")
        print(p.open_page(sb, "/pricing")[:400])
        print("--- visible ---")
        print(p.open_page(sb, "/pricing", "visible_text")[-600:])
    finally:
        p.close()

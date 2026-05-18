#!/usr/bin/env python3
"""server.py — mcstory web API: 一句话 → 触发 cli_full 后端 build scene → 返回 viewer URL"""
import os, sys, json, subprocess, time, uuid, threading
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler

ROOT = Path(__file__).resolve().parent
JOBS = {}  # job_id → {status, sample_id, viewer_url, error}

def render_job(job_id, prompt):
    """后台跑 cli_full"""
    try:
        # 杀掉之前的 viewer
        subprocess.run(["pkill", "-f", "_vd_|viewer_director|puppeteer"], capture_output=True)
        time.sleep(2)
        JOBS[job_id]["status"] = "running"
        # 跑 cli_full
        r = subprocess.run(
            ["python3", str(ROOT/"scripts/cli_full.py"), prompt],
            capture_output=True, text=True, timeout=240, cwd=str(ROOT)
        )
        if r.returncode == 0:
            # parse output 找 final.mp4 path
            for line in r.stdout.split("\n"):
                if "DONE:" in line and "/final.mp4" in line:
                    path = line.split("DONE: ")[1].split(" (")[0].strip()
                    JOBS[job_id]["mp4"] = path
                    break
            JOBS[job_id]["status"] = "done"
            JOBS[job_id]["viewer_url"] = "http://localhost:3007"
        else:
            JOBS[job_id]["status"] = "fail"
            JOBS[job_id]["error"] = r.stderr[-500:]
    except subprocess.TimeoutExpired:
        JOBS[job_id]["status"] = "timeout"
    except Exception as e:
        JOBS[job_id]["status"] = "fail"
        JOBS[job_id]["error"] = str(e)

class Handler(BaseHTTPRequestHandler):
    def _set(self, code=200, ctype="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def do_OPTIONS(self):
        self._set()

    def do_GET(self):
        if self.path == "/":
            self._set(ctype="text/html")
            self.wfile.write(open(ROOT/"index.html","rb").read() if (ROOT/"index.html").exists() else (ROOT/"landing.html").read_bytes())
        elif self.path.startswith("/api/status/"):
            job_id = self.path.split("/")[-1]
            self._set()
            self.wfile.write(json.dumps(JOBS.get(job_id, {"status":"unknown"})).encode())
        elif self.path == "/api/samples":
            self._set()
            samples = [f.stem for f in (ROOT/"samples").glob("*.json")]
            self.wfile.write(json.dumps(samples).encode())
        else:
            self._set(404)

    def do_POST(self):
        if self.path == "/api/render":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
            prompt = body.get("prompt", "")
            sample = body.get("sample", "")  # alt: 预设 sample id
            if sample:
                inp = str(ROOT/"samples"/f"{sample}.json")
            else:
                inp = prompt
            if not inp:
                self._set(400); self.wfile.write(b'{"error":"prompt or sample required"}'); return
            job_id = str(uuid.uuid4())[:8]
            JOBS[job_id] = {"status":"queued","input":inp[:80]}
            threading.Thread(target=render_job, args=(job_id, inp), daemon=True).start()
            self._set()
            self.wfile.write(json.dumps({"job_id":job_id,"status":"queued","viewer_url":"http://localhost:3007"}).encode())
        else:
            self._set(404)

    def log_message(self, fmt, *args): pass  # 静默

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"mcstory server: http://localhost:{port}")
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()

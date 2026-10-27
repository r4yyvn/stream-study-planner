"""Local helper for the Stream & Study Planner.

Serves the planner at http://localhost:8765 so you can edit it on this PC.
Every change is written to schedule.json; "publish" commits that file and
pushes it to GitHub, where GitHub Pages serves the read-only phone copy.

Run it with "Start planner.bat" (or: python server.py). Uses only the
Python standard library.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import threading
import webbrowser
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "schedule.json")
HOST, PORT = "127.0.0.1", 8765
MAX_BODY = 1_000_000
MAX_BLOCKS = 500

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
TYPES = {"stream", "study", "break", "other"}
TIME = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$|^24:00$")

lock = threading.Lock()


def git(*args, timeout=120):
    return subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=timeout
    )


def git_ready():
    """True when this folder is a git repo with a remote to push to."""
    if not shutil.which("git"):
        return False
    try:
        inside = git("rev-parse", "--is-inside-work-tree", timeout=10)
        remotes = git("remote", timeout=10)
    except (OSError, subprocess.SubprocessError):
        return False
    return inside.returncode == 0 and bool(remotes.stdout.strip())


def unpublished():
    """True when schedule.json has changes that are not on GitHub yet."""
    try:
        dirty = git("status", "--porcelain", "--", "schedule.json", timeout=10).stdout.strip()
        ahead = git("rev-list", "--count", "@{u}..HEAD", timeout=10)
    except (OSError, subprocess.SubprocessError):
        return False
    return bool(dirty) or (ahead.returncode == 0 and ahead.stdout.strip() not in ("", "0"))


def text(value, limit):
    return value[:limit] if isinstance(value, str) else ""


def to_minutes(t):
    h, m = t.split(":")
    return int(h) * 60 + int(m)


def clean_schedule(payload):
    if not isinstance(payload, dict) or not isinstance(payload.get("blocks"), list):
        raise ValueError("expected an object with a 'blocks' list")
    if len(payload["blocks"]) > MAX_BLOCKS:
        raise ValueError(f"too many blocks (max {MAX_BLOCKS})")
    blocks = []
    for i, b in enumerate(payload["blocks"]):
        if not isinstance(b, dict):
            raise ValueError(f"block {i} is not an object")
        day, start, end = b.get("day"), b.get("start"), b.get("end")
        if day not in DAYS:
            raise ValueError(f"block {i}: day must be one of {', '.join(DAYS)}")
        if not (isinstance(start, str) and TIME.match(start) and isinstance(end, str) and TIME.match(end)):
            raise ValueError(f"block {i}: start and end must look like 19:30")
        if to_minutes(end) <= to_minutes(start):
            raise ValueError(f"block {i}: end must be after start")
        out = {
            "id": text(b.get("id"), 60) or f"b{i}",
            "day": day,
            "start": start,
            "end": end,
            "type": b.get("type") if b.get("type") in TYPES else "other",
            "title": text(b.get("title"), 80) or "Untitled",
            "tag": text(b.get("tag"), 60),
            "notes": text(b.get("notes"), 500),
            "doneWeek": text(b.get("doneWeek"), 10),
        }
        if b.get("example") is True:
            out["example"] = True
        blocks.append(out)
    blocks.sort(key=lambda b: (DAYS.index(b["day"]), b["start"]))
    return {
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "timezone": text(payload.get("timezone"), 60),
        "blocks": blocks,
    }


def write_schedule(data):
    tmp = DATA + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, DATA)


def publish():
    if not git_ready():
        return False, "publishing isn't set up yet (see README.md)"
    git("add", "schedule.json")
    staged = git("diff", "--cached", "--quiet", "--", "schedule.json")
    if staged.returncode == 1:
        c = git("commit", "-m", "Update schedule", "--", "schedule.json")
        if c.returncode != 0:
            return False, (c.stderr or c.stdout).strip()[-300:]
    p = git("push")
    if p.returncode != 0:
        return False, (p.stderr or p.stdout).strip()[-300:]
    return True, ""


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def log_message(self, fmt, *args):
        if "/api/" in (self.path or ""):
            sys.stderr.write("%s  %s\n" % (self.log_date_time_string(), fmt % args))

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def send_json(self, status, obj):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def same_origin(self):
        # Only this page may change the schedule, not other websites open in your browser.
        origin = self.headers.get("Origin")
        return origin in (None, f"http://localhost:{PORT}", f"http://127.0.0.1:{PORT}")

    def do_GET(self):
        if self.path.split("?")[0] == "/api/status":
            ready = git_ready()
            return self.send_json(200, {"editable": True, "git": ready, "unpublished": ready and unpublished()})
        return super().do_GET()

    def do_PUT(self):
        if self.path.split("?")[0] != "/api/schedule":
            return self.send_json(404, {"ok": False, "error": "not found"})
        if not self.same_origin():
            return self.send_json(403, {"ok": False, "error": "forbidden"})
        try:
            length = int(self.headers.get("Content-Length") or 0)
            if length <= 0 or length > MAX_BODY:
                raise ValueError("request is empty or too large")
            data = clean_schedule(json.loads(self.rfile.read(length).decode("utf-8")))
        except (ValueError, json.JSONDecodeError) as e:
            return self.send_json(400, {"ok": False, "error": str(e)})
        with lock:
            write_schedule(data)
        return self.send_json(200, {"ok": True, "updated": data["updated"]})

    def do_POST(self):
        if self.path.split("?")[0] != "/api/publish":
            return self.send_json(404, {"ok": False, "error": "not found"})
        if not self.same_origin():
            return self.send_json(403, {"ok": False, "error": "forbidden"})
        with lock:
            try:
                ok, err = publish()
            except (OSError, subprocess.SubprocessError) as e:
                ok, err = False, str(e)
        return self.send_json(200 if ok else 500, {"ok": ok, "error": err})


def main():
    url = f"http://localhost:{PORT}/"
    try:
        server = ThreadingHTTPServer((HOST, PORT), Handler)
    except OSError:
        print(f"The planner is already running. Opening {url}")
        webbrowser.open(url)
        return
    print("Stream & Study Planner is running.")
    print(f"  Edit it here:  {url}")
    print(f"  Publishing to phone: {'ready' if git_ready() else 'not set up yet (see README.md)'}")
    print("Keep this window open while you edit. Close it when you're done.")
    if "--no-browser" not in sys.argv:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

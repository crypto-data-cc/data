from __future__ import annotations

import argparse
import json
import subprocess
import sys
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


BASE_DIR = Path(__file__).resolve().parent
WEB_DIR = BASE_DIR / "web"
DATA_FILE = WEB_DIR / "dashboard-data.js"
DEFAULT_MAX_AGE_HOURS = 24

UPDATE_LOCK = threading.Lock()
LAST_ERROR: str | None = None


def data_age_seconds() -> float | None:
    if not DATA_FILE.exists():
        return None
    return time.time() - DATA_FILE.stat().st_mtime


def is_stale(max_age_hours: float) -> bool:
    age = data_age_seconds()
    if age is None:
        return True
    return age > max_age_hours * 3600


def run_step(args: list[str]) -> None:
    subprocess.run(args, cwd=BASE_DIR, check=True)


def refresh_data(force: bool, max_age_hours: float) -> bool:
    global LAST_ERROR
    if not force and not is_stale(max_age_hours):
        return False

    with UPDATE_LOCK:
        if not force and not is_stale(max_age_hours):
            return False
        try:
            run_step([sys.executable, "main.py"])
            run_step([sys.executable, "tokenized_stocks.py"])
            run_step([sys.executable, "build_dashboard.py"])
            LAST_ERROR = None
            return True
        except subprocess.CalledProcessError as exc:
            LAST_ERROR = f"Update failed at command: {' '.join(exc.cmd)}"
            print(LAST_ERROR, file=sys.stderr)
            return False


class DashboardHandler(SimpleHTTPRequestHandler):
    max_age_hours = DEFAULT_MAX_AGE_HOURS

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        force = query.get("refresh", ["0"])[0] in {"1", "true", "yes"}

        if parsed.path in {"/", "/index.html", "/dashboard-data.js", "/status.json"}:
            refresh_data(force=force, max_age_hours=self.max_age_hours)

        if parsed.path == "/status.json":
            self.send_status()
            return

        clean_path = parsed.path
        if parsed.query:
            self.path = clean_path
        super().do_GET()

    def send_status(self) -> None:
        age = data_age_seconds()
        payload = {
            "data_exists": DATA_FILE.exists(),
            "age_seconds": age,
            "max_age_hours": self.max_age_hours,
            "stale": is_stale(self.max_age_hours),
            "last_error": LAST_ERROR,
        }
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve dashboard and refresh stale data on access.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--max-age-hours", type=float, default=DEFAULT_MAX_AGE_HOURS)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    DashboardHandler.max_age_hours = args.max_age_hours
    server = ThreadingHTTPServer((args.host, args.port), DashboardHandler)
    print(f"Serving dashboard at http://{args.host}:{args.port}/")
    print(f"Data refresh threshold: {args.max_age_hours} hours")
    server.serve_forever()


if __name__ == "__main__":
    main()

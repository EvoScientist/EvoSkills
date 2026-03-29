#!/usr/bin/env python3
"""
PPT Viewer Server - Local HTTP server for slide review and feedback.

Serves the generated slides with an interactive viewer. Users can write
feedback per slide and save it directly back to slides_plan.json.

Usage:
  python skills/nano-banana/scripts/serve_viewer.py \
    --dir ppt_output \
    --plan slides_plan.json \
    --port 8080
"""

import argparse
import json
import os
import sys
import webbrowser
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent


class ViewerHandler(SimpleHTTPRequestHandler):
    """HTTP handler that serves slides and handles feedback save."""

    def __init__(self, *args, plan_path=None, output_dir=None, **kwargs):
        self.plan_path = plan_path
        self.output_dir = output_dir
        super().__init__(*args, directory=output_dir, **kwargs)

    def do_POST(self):
        if self.path == "/save-feedback":
            self._handle_save_feedback()
        else:
            self.send_error(404)

    def do_GET(self):
        if self.path == "/api/feedback":
            self._handle_get_feedback()
        else:
            super().do_GET()

    def _handle_save_feedback(self):
        """Save feedback to slides_plan.json."""
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            feedback = json.loads(body)

            # Read current plan
            with open(self.plan_path, "r", encoding="utf-8") as f:
                plan = json.load(f)

            # Update feedback fields
            for slide in plan["slides"]:
                num = str(slide["slide_number"])
                if num in feedback and feedback[num].strip():
                    slide["feedback"] = feedback[num].strip()
                elif "feedback" in slide:
                    del slide["feedback"]

            # Write back
            with open(self.plan_path, "w", encoding="utf-8") as f:
                json.dump(plan, f, ensure_ascii=False, indent=2)

            count = sum(1 for s in plan["slides"] if s.get("feedback"))
            self._json_response({"status": "ok", "count": count})

        except Exception as e:
            self._json_response({"status": "error", "message": str(e)}, 500)

    def _handle_get_feedback(self):
        """Load existing feedback from slides_plan.json."""
        try:
            with open(self.plan_path, "r", encoding="utf-8") as f:
                plan = json.load(f)

            feedback = {}
            for slide in plan["slides"]:
                fb = slide.get("feedback", "")
                if fb:
                    feedback[str(slide["slide_number"])] = fb

            self._json_response(feedback)

        except Exception as e:
            self._json_response({"status": "error", "message": str(e)}, 500)

    def _json_response(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        """Minimal logging for agent consumption."""
        if "POST" in str(args):
            print(f"[server] {args[0]}")


def main():
    parser = argparse.ArgumentParser(description="PPT Viewer Server")
    parser.add_argument("--dir", required=True, help="Output directory with images/")
    parser.add_argument("--plan", required=True, help="Path to slides_plan.json")
    parser.add_argument(
        "--port", type=int, default=8080, help="Server port (default: 8080)"
    )
    parser.add_argument(
        "--no-open", action="store_true", help="Don't auto-open browser"
    )
    parser.add_argument(
        "--pid-file", help="Write server PID to file (for later cleanup)"
    )
    args = parser.parse_args()

    if not os.path.isdir(args.dir):
        print(f"Error: {args.dir} not found")
        sys.exit(1)
    if not os.path.isfile(args.plan):
        print(f"Error: {args.plan} not found")
        sys.exit(1)

    handler = partial(ViewerHandler, plan_path=args.plan, output_dir=args.dir)
    server = HTTPServer(("localhost", args.port), handler)

    # Write PID file so other scripts can stop this server
    if args.pid_file:
        with open(args.pid_file, "w") as f:
            f.write(str(os.getpid()))

    url = f"http://localhost:{args.port}"
    print(f"Serving at {url} (PID: {os.getpid()})")
    print(f"Plan: {args.plan}")

    if not args.no_open:
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")
        server.server_close()
    finally:
        if args.pid_file and os.path.exists(args.pid_file):
            os.remove(args.pid_file)


if __name__ == "__main__":
    main()

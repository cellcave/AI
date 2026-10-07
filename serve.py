"""Preview the current build, including a GitHub Pages repository base path."""
import argparse
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

parser = argparse.ArgumentParser()
parser.add_argument('--port', type=int, default=4173)
parser.add_argument('--qa', action='store_true')
args = parser.parse_args()
ROOT = Path(__file__).resolve().parent / (".qa-dist" if args.qa else "dist")
info = json.loads((ROOT / "build-info.json").read_text(encoding="utf-8"))
BASE = info["base"]

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        path = urlsplit(self.path).path
        if BASE != "/":
            if path in ("/", BASE.rstrip("/")):
                self.send_response(302)
                self.send_header("Location", BASE)
                self.end_headers()
                return
            if not path.startswith(BASE):
                self.send_error(404)
                return
            self.path = "/" + self.path[len(BASE):]
        super().do_GET()

    def send_error(self, code, message=None, explain=None):
        if code == 404:
            page = (ROOT / "404.html").read_bytes()
            self.send_response(404)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(page)))
            self.end_headers()
            self.wfile.write(page)
        else:
            super().send_error(code, message, explain)

print(f"Preview: http://127.0.0.1:{args.port}{BASE}", flush=True)
ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()

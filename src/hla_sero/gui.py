"""
gui.py — local copy-paste window.

Runs a small web server on 127.0.0.1 (this computer only) and opens it in the
default browser. Nothing typed into the window is sent anywhere else; the only
network traffic is the IMGT/HLA update check to GitHub.
"""

from __future__ import annotations

import json
import socket
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib import resources

from . import __version__, imgt
from .cli import load_overrides, provenance
from .engine import convert_text

MAX_BODY = 2_000_000  # 2 MB of pasted text is plenty


class App:
    def __init__(self, release: str | None):
        self.release = release
        self.lock = threading.Lock()
        self.log: list[str] = []
        self.db = None
        self.error = ""
        self.reload(update=True)

    def _log(self, msg: str) -> None:
        print(msg)
        self.log.append(msg)

    def reload(self, update: bool, force: bool = False) -> None:
        with self.lock:
            try:
                if force:
                    imgt.check_and_update(force=True, release=self.release, log=self._log)
                self.db = imgt.load_database(release=self.release, update=update and not force, log=self._log)
                self.error = ""
            except imgt.UpdateError as e:
                self.error = str(e)
                self._log(f"Error: {e}")

    def status(self) -> dict:
        cfg = imgt.load_config()
        return {
            "app_version": __version__,
            "release": self.db.version if self.db else None,
            "date": self.db.date if self.db else None,
            "alleles": len(self.db.alleles) if self.db else 0,
            "provenance": provenance(self.db) if self.db else "",
            "auto_update": cfg["auto_update"],
            "pinned": cfg.get("pinned_release"),
            "installed": imgt.installed_releases(),
            "error": self.error,
            "log": self.log[-8:],
        }


def make_handler(app: App, port_holder: dict):
    page = resources.files("hla_sero").joinpath("web/index.html").read_bytes()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a):          # keep the terminal quiet
            pass

        def _send(self, code: int, body: bytes, ctype: str = "application/json") -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, obj, code: int = 200) -> None:
            self._send(code, json.dumps(obj).encode("utf-8"))

        def _same_origin(self) -> bool:
            # Block other websites from posting into this local app
            origin = self.headers.get("Origin")
            port = port_holder["port"]
            return origin in (None, f"http://127.0.0.1:{port}", f"http://localhost:{port}")

        def do_GET(self):
            if self.path in ("/", "/index.html"):
                self._send(200, page, "text/html; charset=utf-8")
            elif self.path == "/api/status":
                self._json(app.status())
            else:
                self._send(404, b"not found", "text/plain")

        def do_POST(self):
            if not self._same_origin():
                return self._json({"error": "forbidden"}, 403)
            length = int(self.headers.get("Content-Length") or 0)
            if length > MAX_BODY:
                return self._json({"error": "input too large"}, 413)
            try:
                data = json.loads(self.rfile.read(length) or b"{}")
            except ValueError:
                return self._json({"error": "bad request"}, 400)

            if self.path == "/api/convert":
                if not app.db:
                    return self._json({"error": app.error or "no IMGT/HLA data loaded"}, 503)
                rows = convert_text(app.db, str(data.get("text", "")), load_overrides())
                return self._json({"rows": rows, "provenance": provenance(app.db)})
            if self.path == "/api/update":
                app.reload(update=True, force=True)
                return self._json(app.status())
            if self.path == "/api/quit":
                self._json({"ok": True})
                threading.Thread(target=self.server.shutdown, daemon=True).start()
                return None
            return self._json({"error": "not found"}, 404)

    return Handler


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def serve(port: int = 0, open_browser: bool = True, release: str | None = None) -> int:
    app = App(release)
    port = port or _free_port()
    holder = {"port": port}
    server = ThreadingHTTPServer(("127.0.0.1", port), make_handler(app, holder))
    url = f"http://127.0.0.1:{port}/"
    print(f"HLA Serology Converter running at {url}")
    print("Close it with the Quit button in the window, or Ctrl+C here.")
    if open_browser:
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0

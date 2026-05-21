"""BPLog server entry point.

Resolves paths, loads settings, binds to the configured Meshnet IP
(falling back to 127.0.0.1 on bind failure), starts the reminder
scheduler, opens the user's browser, and serves Flask via the stdlib
WSGI server (no Werkzeug reloader).
"""
from __future__ import annotations

import logging
import os
import socket
import subprocess
import sys
import threading
import webbrowser
from socketserver import ThreadingMixIn
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer, make_server

from .app import create_app
from .config import FALLBACK_BIND_ADDRESS, default_paths
from .reminders import ReminderScheduler, ReminderState
from .settings import load as load_settings

log = logging.getLogger("bplog")


class _ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
    daemon_threads = True


class _FastWSGIRequestHandler(WSGIRequestHandler):
    """Skip the reverse-DNS lookup that BaseHTTPRequestHandler does for logging.

    On Meshnet / Tailscale IPs the lookup blocks for the OS resolver timeout
    (often 5–10s) on every request, which makes the first page load feel
    glacial and serializes against the WSGI handler since the lookup runs
    inside the request thread.
    """

    def address_string(self) -> str:
        return self.client_address[0]


def _pick_port(host: str) -> int:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind((host, 0))
        return s.getsockname()[1]
    finally:
        s.close()


def _resolve_bind(preferred: str) -> str:
    """Return preferred host if it's usable, else the fallback."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((preferred, 0))
        s.close()
        return preferred
    except OSError as exc:
        log.warning("Could not bind to %s (%s); falling back to %s.", preferred, exc, FALLBACK_BIND_ADDRESS)
        return FALLBACK_BIND_ADDRESS


def _is_wsl() -> bool:
    if sys.platform != "linux":
        return False
    try:
        with open("/proc/version", "r", encoding="utf-8") as fh:
            return "microsoft" in fh.read().lower()
    except OSError:
        return False


def _open_in_default_browser(url: str) -> None:
    """Open the URL in the user's system default browser.

    On WSL, defer to the Windows shell so the Windows default browser is used
    rather than whatever Python's webbrowser module discovers inside the
    Linux userland.
    """
    try:
        if _is_wsl():
            for cmd in (["wslview", url], ["cmd.exe", "/c", "start", "", url]):
                try:
                    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return
                except FileNotFoundError:
                    continue
        webbrowser.open(url)
    except Exception:
        log.warning("Could not open browser for %s", url, exc_info=True)


def _copy_to_clipboard(text: str) -> None:
    """Best-effort cross-platform clipboard copy. Silent on failure."""
    try:
        if sys.platform == "win32":
            import subprocess
            subprocess.run(["clip"], input=text, text=True, check=False)
        elif sys.platform == "darwin":
            import subprocess
            subprocess.run(["pbcopy"], input=text, text=True, check=False)
        else:
            # WSL: prefer clip.exe so the URL lands in the Windows clipboard.
            for cmd in (["clip.exe"], ["wl-copy"], ["xclip", "-selection", "clipboard"]):
                try:
                    import subprocess
                    subprocess.run(cmd, input=text, text=True, check=True)
                    return
                except (FileNotFoundError, Exception):
                    continue
    except Exception:
        pass


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    paths = default_paths()
    paths.ensure()

    settings = load_settings(paths.settings)

    preferred = os.environ.get("BPLOG_BIND") or settings.server.bind_address
    host = _resolve_bind(preferred)
    port = _pick_port(host)

    state = ReminderState()
    scheduler = ReminderScheduler(settings, state)
    scheduler.start()

    app = create_app(
        paths=paths,
        settings=settings,
        reminder_state=state,
        reminder_scheduler=scheduler,
    )

    url = f"http://{host}:{port}/"
    log.info("BPLog serving at %s", url)
    _copy_to_clipboard(url)

    threading.Timer(0.75, lambda: _open_in_default_browser(url)).start()

    try:
        with make_server(
            host,
            port,
            app,
            server_class=_ThreadingWSGIServer,
            handler_class=_FastWSGIRequestHandler,
        ) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        log.info("Shutting down.")
    finally:
        scheduler.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

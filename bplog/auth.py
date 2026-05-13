"""Per-startup URL token guard.

Every route except /healthz and /static/* requires `?t=<token>` to
match the token chosen at startup. This is not real auth — it's a
trivial barrier so a scan of the Meshnet IP can't trip the app.
"""
from __future__ import annotations

from flask import Flask, abort, current_app, request

_EXEMPT_PATHS = {"/healthz"}


def _is_exempt(path: str) -> bool:
    if path in _EXEMPT_PATHS:
        return True
    if path.startswith("/static/"):
        return True
    return False


def register_token_check(app: Flask) -> None:
    @app.before_request
    def _check_token():
        expected = current_app.config.get("bplog_url_token")
        if not expected:
            return  # token disabled (tests/dev)
        if _is_exempt(request.path):
            return
        provided = request.args.get("t") or request.headers.get("X-BPLog-Token")
        if provided != expected:
            abort(403)

from __future__ import annotations

from datetime import datetime, time

from flask import Blueprint, current_app, redirect, render_template, request, url_for

from .. import settings as settings_mod
from ..config import Paths

bp = Blueprint("settings_ui", __name__)


def _paths() -> Paths:
    return current_app.config["bplog_paths"]


def _settings() -> settings_mod.Settings:
    return current_app.config["bplog_settings"]


def _parse_time(value: str) -> time | None:
    value = (value or "").strip()
    if not value:
        return None
    try:
        return datetime.strptime(value, "%H:%M").time()
    except ValueError:
        return None


@bp.get("/settings")
def edit():
    return render_template("settings.html", settings=_settings())


@bp.post("/settings")
def save():
    s = _settings()
    s.user_name = (request.form.get("user_name") or "").strip()
    bd = request.form.get("birth_date") or ""
    s.birth_date = datetime.strptime(bd, "%Y-%m-%d") if bd else None

    s.server.bind_address = (request.form.get("bind_address") or s.server.bind_address).strip()
    s.vision_model = (request.form.get("vision_model") or s.vision_model).strip()

    s.reminders.enabled = request.form.get("reminders_enabled") == "on"
    raw_times = request.form.get("reminder_times", "")
    parsed = [t for t in (_parse_time(x) for x in raw_times.split(",")) if t]
    if parsed:
        s.reminders.times = parsed

    settings_mod.save(_paths().settings, s)
    return redirect(url_for("readings.index", t=current_app.config.get("bplog_url_token")))

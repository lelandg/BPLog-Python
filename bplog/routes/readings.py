from __future__ import annotations

from datetime import datetime, time
from typing import Optional

from flask import Blueprint, current_app, redirect, render_template, request, url_for

from .. import repository, settings as settings_mod
from ..config import Paths
from ..images import save_image_for_reading, delete_image_for_reading

bp = Blueprint("readings", __name__)


def _paths() -> Paths:
    return current_app.config["bplog_paths"]


def _settings() -> settings_mod.Settings:
    return current_app.config["bplog_settings"]


def _save_settings() -> None:
    settings_mod.save(_paths().settings, _settings())


def _parse_int(value: Optional[str]) -> Optional[int]:
    if value is None or value.strip() == "":
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _parse_reading_datetime(date_str: str, time_str: str) -> datetime:
    d = datetime.strptime(date_str, "%Y-%m-%d").date()
    if time_str:
        try:
            t = datetime.strptime(time_str, "%H:%M").time()
        except ValueError:
            t = datetime.strptime(time_str, "%H:%M:%S").time()
    else:
        t = time(0, 0)
    return datetime.combine(d, t)


def _redirect_root():
    return redirect(url_for("readings.index"))


@bp.get("/")
def index():
    paths = _paths()
    s = _settings()
    records = repository.list_readings(paths.db)
    edit_id = _parse_int(request.args.get("edit"))
    editing = repository.get_reading(paths.db, edit_id) if edit_id else None
    primary_user = repository.get_primary_user(paths.db)
    display_name = s.user_name or (primary_user.name if primary_user else "")
    display_birthdate = s.birth_date or (primary_user.birthdate if primary_user else None)
    return render_template(
        "index.html",
        records=records,
        editing=editing,
        settings=s,
        display_name=display_name,
        display_birthdate=display_birthdate,
        now=datetime.now(),
    )


@bp.post("/readings")
def add_or_update():
    paths = _paths()
    s = _settings()

    systolic = _parse_int(request.form.get("systolic"))
    diastolic = _parse_int(request.form.get("diastolic"))
    pulse = _parse_int(request.form.get("pulse"))
    standing = request.form.get("standing") == "on"
    date_str = request.form.get("reading_date", "")
    time_str = request.form.get("reading_time", "")
    edit_id = _parse_int(request.form.get("edit_id"))

    if not (systolic and diastolic and pulse and date_str):
        return _redirect_root()

    reading_dt = _parse_reading_datetime(date_str, time_str)

    name = (request.form.get("user_name") or s.user_name or "").strip()
    bd_str = request.form.get("birth_date") or (
        s.birth_date.strftime("%Y-%m-%d") if s.birth_date else ""
    )
    if not name or not bd_str:
        # No identity yet — bounce to settings.
        return redirect(url_for("settings_ui.edit"))

    birthdate = datetime.strptime(bd_str, "%Y-%m-%d")
    user_id = repository.upsert_user(paths.db, name, birthdate)

    if edit_id:
        repository.update_reading(paths.db, edit_id, systolic, diastolic, pulse, reading_dt, standing)
        new_id = edit_id
    else:
        new_id = repository.add_reading(paths.db, user_id, systolic, diastolic, pulse, reading_dt, standing)

    # Optional image attachment
    file = request.files.get("image")
    if file and file.filename:
        save_image_for_reading(paths.images_dir, new_id, file.stream, file.filename)

    # Persist identity to settings so the form can prefill next time.
    s.user_name = name
    s.birth_date = birthdate
    _save_settings()

    return _redirect_root()


@bp.post("/readings/<int:reading_id>/delete")
def delete(reading_id: int):
    paths = _paths()
    repository.delete_reading(paths.db, reading_id)
    delete_image_for_reading(paths.images_dir, reading_id)
    return _redirect_root()


@bp.post("/readings/<int:reading_id>/set-last-export")
def set_last_export(reading_id: int):
    paths = _paths()
    s = _settings()
    record = repository.get_reading(paths.db, reading_id)
    if record is not None:
        s.last_export_date_time = record.reading_time
        s.export_start_date_time = record.reading_time
        _save_settings()
    return _redirect_root()

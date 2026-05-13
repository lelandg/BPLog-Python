from __future__ import annotations

from datetime import datetime

from flask import Blueprint, Response, current_app

from .. import exporters, repository, settings as settings_mod
from ..config import Paths

bp = Blueprint("exports", __name__)


def _paths() -> Paths:
    return current_app.config["bplog_paths"]


def _settings() -> settings_mod.Settings:
    return current_app.config["bplog_settings"]


def _save_settings() -> None:
    settings_mod.save(_paths().settings, _settings())


def _records_for_export():
    paths = _paths()
    s = _settings()
    all_records = repository.list_readings(paths.db)
    return exporters.filter_after(all_records, s.export_start_date_time)


@bp.get("/export/text")
def text():
    s = _settings()
    records = _records_for_export()
    body = exporters.to_text(records, s.user_name, s.birth_date)
    s.last_export_date_time = datetime.now()
    _save_settings()
    filename = f"{datetime.now():%Y-%m-%d}_bp_readings.txt"
    return Response(
        body,
        mimetype="text/plain",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@bp.get("/export/html")
def html():
    s = _settings()
    records = _records_for_export()
    body = exporters.to_html(records, s.user_name, s.birth_date)
    s.last_export_date_time = datetime.now()
    _save_settings()
    filename = f"{datetime.now():%Y-%m-%d}_bp_readings.html"
    return Response(
        body,
        mimetype="text/html",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

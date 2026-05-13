"""Unified settings.json read/write.

Backward-compatible with the .NET app's Newtonsoft serialization for
the keys we care about (UserName, BirthDate, LastExportDateTime,
ExportStartDateTime). Adds a `server` and `reminders` sub-object the
.NET app simply ignores.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, time
from pathlib import Path
from typing import Any, Optional

from dateutil import parser as date_parser

from .config import DEFAULT_BIND_ADDRESS


@dataclass
class ReminderSettings:
    enabled: bool = True
    times: list[time] = field(default_factory=lambda: [time(7, 0), time(15, 0)])
    has_taken_first_reading: bool = False


@dataclass
class ServerSettings:
    bind_address: str = DEFAULT_BIND_ADDRESS


@dataclass
class Settings:
    user_name: str = ""
    birth_date: Optional[datetime] = None
    last_export_date_time: Optional[datetime] = None
    export_start_date_time: Optional[datetime] = None
    server: ServerSettings = field(default_factory=ServerSettings)
    reminders: ReminderSettings = field(default_factory=ReminderSettings)
    vision_model: str = "claude-haiku-4-5"


def _parse_dt(value: Any) -> Optional[datetime]:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    return date_parser.parse(str(value))


def _parse_time(value: Any) -> time:
    if isinstance(value, time):
        return value
    s = str(value)
    # Accept "HH:MM", "HH:MM:SS", or ISO time
    parts = s.split(":")
    h = int(parts[0])
    m = int(parts[1]) if len(parts) > 1 else 0
    sec = int(parts[2]) if len(parts) > 2 else 0
    return time(h, m, sec)


def load(path: Path) -> Settings:
    if not path.exists():
        return Settings()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return Settings()
    s = Settings()
    s.user_name = str(raw.get("UserName", "") or "")
    s.birth_date = _parse_dt(raw.get("BirthDate"))
    s.last_export_date_time = _parse_dt(raw.get("LastExportDateTime"))
    s.export_start_date_time = _parse_dt(raw.get("ExportStartDateTime"))

    server = raw.get("server") or {}
    s.server = ServerSettings(
        bind_address=str(server.get("bind_address", DEFAULT_BIND_ADDRESS)),
    )

    rem = raw.get("reminders") or {}
    times_raw = rem.get("times") or []
    s.reminders = ReminderSettings(
        enabled=bool(rem.get("enabled", True)),
        times=[_parse_time(t) for t in times_raw] or ReminderSettings().times,
        has_taken_first_reading=bool(rem.get("has_taken_first_reading", False)),
    )

    s.vision_model = str(raw.get("vision_model", "claude-haiku-4-5"))
    return s


def save(path: Path, s: Settings) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "UserName": s.user_name,
        "BirthDate": s.birth_date.isoformat() if s.birth_date else None,
        "LastExportDateTime": s.last_export_date_time.isoformat() if s.last_export_date_time else None,
        "ExportStartDateTime": s.export_start_date_time.isoformat() if s.export_start_date_time else None,
        "server": {"bind_address": s.server.bind_address},
        "reminders": {
            "enabled": s.reminders.enabled,
            "times": [t.strftime("%H:%M") for t in s.reminders.times],
            "has_taken_first_reading": s.reminders.has_taken_first_reading,
        },
        "vision_model": s.vision_model,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

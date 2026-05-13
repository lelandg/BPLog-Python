import json
from datetime import datetime, time
from pathlib import Path

from bplog import settings


def test_load_missing_file_returns_defaults(tmp_path: Path):
    s = settings.load(tmp_path / "nope.json")
    assert s.user_name == ""
    assert s.birth_date is None
    assert s.reminders.enabled is True
    assert len(s.reminders.times) == 2
    assert s.server.bind_address == settings.DEFAULT_BIND_ADDRESS


def test_load_dotnet_shaped_fixture(tmp_path: Path):
    fixture = {
        "UserName": "Alice",
        "BirthDate": "1970-01-01T00:00:00",
        "LastExportDateTime": "2026-05-10T12:34:56",
        "ExportStartDateTime": "2026-05-09T00:00:00",
        "Readings": [],  # extra .NET field we should silently ignore
    }
    p = tmp_path / "settings.json"
    p.write_text(json.dumps(fixture))
    s = settings.load(p)
    assert s.user_name == "Alice"
    assert s.birth_date == datetime(1970, 1, 1)
    assert s.last_export_date_time == datetime(2026, 5, 10, 12, 34, 56)
    assert s.export_start_date_time == datetime(2026, 5, 9, 0, 0, 0)


def test_round_trip_preserves_known_keys(tmp_path: Path):
    p = tmp_path / "settings.json"
    s_in = settings.Settings(
        user_name="Bob",
        birth_date=datetime(1980, 6, 15),
        last_export_date_time=datetime(2026, 5, 13, 9, 0, 0),
        export_start_date_time=datetime(2026, 5, 1, 0, 0, 0),
    )
    s_in.reminders.times = [time(8, 30), time(20, 0)]
    settings.save(p, s_in)
    s_out = settings.load(p)
    assert s_out.user_name == "Bob"
    assert s_out.birth_date == datetime(1980, 6, 15)
    assert s_out.last_export_date_time == datetime(2026, 5, 13, 9, 0, 0)
    assert s_out.export_start_date_time == datetime(2026, 5, 1, 0, 0, 0)
    assert s_out.reminders.times == [time(8, 30), time(20, 0)]


def test_load_handles_corrupt_json(tmp_path: Path):
    p = tmp_path / "settings.json"
    p.write_text("{this is not json")
    s = settings.load(p)
    assert s.user_name == ""

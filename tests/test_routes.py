from datetime import datetime

from bplog import repository


def test_index_renders_empty(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"No readings yet" in resp.data


def test_add_reading_via_form(client, paths):
    resp = client.post(
        "/readings",
        data={
            "user_name": "Alice",
            "birth_date": "1970-01-01",
            "systolic": "120",
            "diastolic": "80",
            "pulse": "65",
            "reading_date": "2026-05-13",
            "reading_time": "09:30",
            "standing": "on",
        },
    )
    assert resp.status_code in (302, 303)
    rows = repository.list_readings(paths.db)
    assert len(rows) == 1
    assert rows[0].systolic == 120
    assert rows[0].standing is True


def test_delete_reading(client, paths):
    uid = repository.upsert_user(paths.db, "Alice", datetime(1970, 1, 1))
    rid = repository.add_reading(paths.db, uid, 120, 80, 65, datetime(2026, 5, 13, 9, 0), False)

    resp = client.post(f"/readings/{rid}/delete")
    assert resp.status_code in (302, 303)
    assert repository.list_readings(paths.db) == []


def test_healthz_ok(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


def test_export_text_filters_after_export_start(client, paths, app):
    uid = repository.upsert_user(paths.db, "Alice", datetime(1970, 1, 1))
    repository.add_reading(paths.db, uid, 120, 80, 65, datetime(2026, 5, 13, 8, 0), False)
    repository.add_reading(paths.db, uid, 125, 82, 68, datetime(2026, 5, 13, 10, 0), False)

    s = app.config["bplog_settings"]
    s.export_start_date_time = datetime(2026, 5, 13, 9, 0)

    resp = client.get("/export/text")
    assert resp.status_code == 200
    body = resp.data.decode("utf-8")
    assert "10:00" in body
    assert "08:00" not in body


def test_settings_get_then_post(client, paths, app):
    resp = client.get("/settings")
    assert resp.status_code == 200
    assert b"Identity" in resp.data

    resp = client.post(
        "/settings",
        data={
            "user_name": "Bob",
            "birth_date": "1980-06-15",
            "bind_address": "127.0.0.1",
            "reminders_enabled": "on",
            "reminder_times": "08:00, 20:00",
            "vision_model": "claude-haiku-4-5",
        },
    )
    assert resp.status_code in (302, 303)
    assert app.config["bplog_settings"].user_name == "Bob"

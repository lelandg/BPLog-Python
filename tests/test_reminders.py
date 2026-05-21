from datetime import datetime, time

from bplog import db, settings as settings_mod
from bplog.app import create_app
from bplog.config import Paths
from bplog.reminders import ReminderScheduler, ReminderState, fake_trigger_now


def test_state_round_trip():
    state = ReminderState()
    assert state.banner_message() is None
    state.trigger("07:00")
    assert "07:00" in (state.banner_message() or "")
    state.dismiss()
    assert state.banner_message() is None


def test_scheduler_installs_jobs_for_each_time():
    s = settings_mod.Settings()
    s.reminders.times = [time(7, 0), time(15, 0)]
    state = ReminderState()
    sched = ReminderScheduler(s, state)
    sched.start()
    try:
        jobs = sched._scheduler.get_jobs()  # type: ignore[attr-defined]
        assert len(jobs) == 2
    finally:
        sched.stop()


def test_scheduler_disabled_installs_no_jobs():
    s = settings_mod.Settings()
    s.reminders.enabled = False
    state = ReminderState()
    sched = ReminderScheduler(s, state)
    sched.start()
    try:
        assert sched._scheduler.get_jobs() == []  # type: ignore[attr-defined]
    finally:
        sched.stop()


def test_banner_renders_when_triggered(tmp_path):
    paths = Paths(
        db=tmp_path / "bp.db",
        settings=tmp_path / "settings.json",
        images_dir=tmp_path / "images",
    )
    paths.ensure()
    db.initialize(paths.db)
    s = settings_mod.Settings(user_name="Alice", birth_date=datetime(1970, 1, 1))
    state = ReminderState()
    sched = ReminderScheduler(s, state)
    app = create_app(paths=paths, settings=s, reminder_state=state, reminder_scheduler=sched)

    fake_trigger_now(state, datetime(2026, 5, 13, 7, 0))
    with app.test_client() as client:
        resp = client.get("/")
        assert b"Time to take your blood pressure" in resp.data

        resp = client.post("/reminders/dismiss")
        assert resp.status_code in (302, 303)
        assert state.banner_message() is None

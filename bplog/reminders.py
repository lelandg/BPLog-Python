"""Background reminder scheduler using APScheduler.

Fires while the server is running. The UI surfaces pending reminders
as a banner via a Flask context processor (see ReminderState.banner_message).
"""
from __future__ import annotations

import logging
from datetime import datetime
from threading import Lock

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from .settings import Settings

log = logging.getLogger(__name__)


class ReminderState:
    """Process-wide reminder status surfaced in templates."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._pending_message: str | None = None

    def trigger(self, label: str) -> None:
        with self._lock:
            self._pending_message = f"Time to take your blood pressure ({label})."
        log.info("Reminder fired: %s", label)

    def banner_message(self) -> str | None:
        with self._lock:
            return self._pending_message

    def dismiss(self) -> None:
        with self._lock:
            self._pending_message = None


class ReminderScheduler:
    def __init__(self, settings: Settings, state: ReminderState) -> None:
        self._settings = settings
        self._state = state
        self._scheduler = BackgroundScheduler(daemon=True)
        self._started = False

    def start(self) -> None:
        if self._started:
            return
        self._install_jobs()
        self._scheduler.start()
        self._started = True
        log.info("ReminderScheduler started with %d times.", len(self._settings.reminders.times))

    def stop(self) -> None:
        if not self._started:
            return
        self._scheduler.shutdown(wait=False)
        self._started = False

    def _install_jobs(self) -> None:
        if not self._settings.reminders.enabled:
            return
        for t in self._settings.reminders.times:
            label = t.strftime("%H:%M")
            self._scheduler.add_job(
                self._state.trigger,
                CronTrigger(hour=t.hour, minute=t.minute),
                args=[label],
                id=f"reminder-{label}",
                replace_existing=True,
            )

    def reload(self) -> None:
        """Re-read times from settings (call after the settings form is saved)."""
        for job in list(self._scheduler.get_jobs()):
            self._scheduler.remove_job(job.id)
        self._install_jobs()


def register_reminders(app, scheduler: ReminderScheduler, state: ReminderState) -> None:
    """Wire the reminder banner + dismiss endpoint into the Flask app."""
    from flask import redirect, request, url_for

    app.config["bplog_reminder_state"] = state
    app.config["bplog_reminder_scheduler"] = scheduler

    @app.context_processor
    def _inject_banner():
        return {"reminder_banner": state.banner_message()}

    @app.post("/reminders/dismiss")
    def _dismiss():
        state.dismiss()
        token = app.config.get("bplog_url_token")
        next_url = request.form.get("next") or url_for("readings.index", t=token)
        return redirect(next_url)


# Helper used at startup
def fake_trigger_now(state: ReminderState, when: datetime | None = None) -> None:
    """Test/debug helper: fire a reminder immediately."""
    label = (when or datetime.now()).strftime("%H:%M")
    state.trigger(label)

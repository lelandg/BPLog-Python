from datetime import datetime

from bplog import db, settings as settings_mod
from bplog.app import create_app
from bplog.config import Paths


def _make_app(tmp_path, token: str):
    paths = Paths(
        db=tmp_path / "bp.db",
        settings=tmp_path / "settings.json",
        images_dir=tmp_path / "images",
    )
    paths.ensure()
    db.initialize(paths.db)
    s = settings_mod.Settings(user_name="Alice", birth_date=datetime(1970, 1, 1))
    return create_app(paths=paths, settings=s, url_token=token).test_client()


def test_missing_token_rejected(tmp_path):
    client = _make_app(tmp_path, "secret-token")
    resp = client.get("/")
    assert resp.status_code == 403


def test_wrong_token_rejected(tmp_path):
    client = _make_app(tmp_path, "secret-token")
    resp = client.get("/?t=nope")
    assert resp.status_code == 403


def test_correct_token_accepted(tmp_path):
    client = _make_app(tmp_path, "secret-token")
    resp = client.get("/?t=secret-token")
    assert resp.status_code == 200


def test_healthz_token_exempt(tmp_path):
    client = _make_app(tmp_path, "secret-token")
    resp = client.get("/healthz")
    assert resp.status_code == 200


def test_no_token_configured_allows_all(tmp_path):
    client = _make_app(tmp_path, "")
    resp = client.get("/")
    assert resp.status_code == 200

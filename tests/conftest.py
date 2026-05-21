from pathlib import Path
from typing import Iterator

import pytest

from bplog import db, settings as settings_mod
from bplog.app import create_app
from bplog.config import Paths


@pytest.fixture
def paths(tmp_path: Path) -> Paths:
    p = Paths(
        db=tmp_path / "bp.db",
        settings=tmp_path / "settings.json",
        images_dir=tmp_path / "images",
    )
    p.ensure()
    db.initialize(p.db)
    return p


@pytest.fixture
def app(paths: Paths) -> Iterator:
    settings = settings_mod.Settings(
        user_name="Alice",
        birth_date=__import__("datetime").datetime(1970, 1, 1),
    )
    settings_mod.save(paths.settings, settings)
    flask_app = create_app(paths=paths, settings=settings)
    flask_app.config["TESTING"] = True
    yield flask_app


@pytest.fixture
def client(app):
    return app.test_client()

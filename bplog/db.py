"""SQLite connection helper and idempotent schema bootstrap.

Schema mirrors the .NET WPF BPLog app exactly so both apps read/write
the same database file. Do not add columns here without checking the
migration plan.
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

_USERS_DDL = """
CREATE TABLE IF NOT EXISTS Users (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    Name TEXT NOT NULL,
    Birthdate TEXT NOT NULL
)
"""

_READINGS_DDL = """
CREATE TABLE IF NOT EXISTS Readings (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    UserId INTEGER NOT NULL,
    Systolic INTEGER NOT NULL,
    Diastolic INTEGER NOT NULL,
    Pulse INTEGER NOT NULL,
    ReadingTime TEXT NOT NULL,
    Position TEXT NOT NULL,
    FOREIGN KEY(UserId) REFERENCES Users(Id)
)
"""


def initialize(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with connect(db_path) as conn:
        conn.execute(_USERS_DDL)
        conn.execute(_READINGS_DDL)
        conn.commit()


@contextmanager
def connect(db_path: Path) -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        conn.close()

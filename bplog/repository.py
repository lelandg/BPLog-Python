"""All SQL lives here. Thin wrapper over sqlite3."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from dateutil import parser as date_parser

from .db import connect
from .models import HealthRecord, User

# Format the .NET app writes for ReadingTime when a DateTime is bound via
# AddWithValue. Microsoft.Data.Sqlite renders DateTime as ISO with a space.
_DATETIME_FMT = "%Y-%m-%d %H:%M:%S"
_DATE_FMT = "%Y-%m-%d"


def _parse_datetime(value: str) -> datetime:
    """Tolerant parse: ISO, .NET 'yyyy-MM-dd HH:mm:ss', or anything dateutil can read."""
    try:
        return datetime.strptime(value, _DATETIME_FMT)
    except ValueError:
        return date_parser.parse(value)


def _parse_date(value: str) -> datetime:
    try:
        return datetime.strptime(value, _DATE_FMT)
    except ValueError:
        return date_parser.parse(value)


def upsert_user(db_path: Path, name: str, birthdate: datetime) -> int:
    """Return the user id, inserting if (name, birthdate) is new."""
    bd_str = birthdate.strftime(_DATE_FMT)
    with connect(db_path) as conn:
        row = conn.execute(
            "SELECT Id FROM Users WHERE Name = ? AND Birthdate = ?",
            (name, bd_str),
        ).fetchone()
        if row is not None:
            return int(row["Id"])
        cur = conn.execute(
            "INSERT INTO Users (Name, Birthdate) VALUES (?, ?)",
            (name, bd_str),
        )
        conn.commit()
        assert cur.lastrowid is not None
        return int(cur.lastrowid)


def get_primary_user(db_path: Path) -> Optional[User]:
    """Return the most recently inserted user, or None if the table is empty."""
    with connect(db_path) as conn:
        row = conn.execute(
            "SELECT Id, Name, Birthdate FROM Users ORDER BY Id DESC LIMIT 1"
        ).fetchone()
    if row is None:
        return None
    return User(id=int(row["Id"]), name=row["Name"], birthdate=_parse_date(row["Birthdate"]))


def add_reading(
    db_path: Path,
    user_id: int,
    systolic: int,
    diastolic: int,
    pulse: int,
    reading_time: datetime,
    standing: bool,
) -> int:
    position = "Standing" if standing else "Sitting"
    with connect(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO Readings (UserId, Systolic, Diastolic, Pulse, ReadingTime, Position)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                systolic,
                diastolic,
                pulse,
                reading_time.strftime(_DATETIME_FMT),
                position,
            ),
        )
        conn.commit()
        assert cur.lastrowid is not None
        return int(cur.lastrowid)


def update_reading(
    db_path: Path,
    reading_id: int,
    systolic: int,
    diastolic: int,
    pulse: int,
    reading_time: datetime,
    standing: bool,
) -> None:
    position = "Standing" if standing else "Sitting"
    with connect(db_path) as conn:
        conn.execute(
            """
            UPDATE Readings
               SET Systolic = ?, Diastolic = ?, Pulse = ?, ReadingTime = ?, Position = ?
             WHERE Id = ?
            """,
            (systolic, diastolic, pulse, reading_time.strftime(_DATETIME_FMT), position, reading_id),
        )
        conn.commit()


def delete_reading(db_path: Path, reading_id: int) -> int:
    with connect(db_path) as conn:
        cur = conn.execute("DELETE FROM Readings WHERE Id = ?", (reading_id,))
        conn.commit()
        return cur.rowcount


def list_readings(db_path: Path) -> list[HealthRecord]:
    with connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT r.Id, r.UserId, u.Name, u.Birthdate,
                   r.Systolic, r.Diastolic, r.Pulse, r.ReadingTime, r.Position
              FROM Readings r
              JOIN Users u ON u.Id = r.UserId
             ORDER BY r.ReadingTime DESC
            """
        ).fetchall()
    return [
        HealthRecord(
            id=int(r["Id"]),
            user_id=int(r["UserId"]),
            name=r["Name"],
            birthdate=_parse_date(r["Birthdate"]),
            systolic=int(r["Systolic"]),
            diastolic=int(r["Diastolic"]),
            pulse=int(r["Pulse"]),
            reading_time=_parse_datetime(r["ReadingTime"]),
            standing=(r["Position"] == "Standing"),
        )
        for r in rows
    ]


def get_reading(db_path: Path, reading_id: int) -> Optional[HealthRecord]:
    with connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT r.Id, r.UserId, u.Name, u.Birthdate,
                   r.Systolic, r.Diastolic, r.Pulse, r.ReadingTime, r.Position
              FROM Readings r
              JOIN Users u ON u.Id = r.UserId
             WHERE r.Id = ?
            """,
            (reading_id,),
        ).fetchone()
    if row is None:
        return None
    return HealthRecord(
        id=int(row["Id"]),
        user_id=int(row["UserId"]),
        name=row["Name"],
        birthdate=_parse_date(row["Birthdate"]),
        systolic=int(row["Systolic"]),
        diastolic=int(row["Diastolic"]),
        pulse=int(row["Pulse"]),
        reading_time=_parse_datetime(row["ReadingTime"]),
        standing=(row["Position"] == "Standing"),
    )

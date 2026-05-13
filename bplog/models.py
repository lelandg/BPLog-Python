"""Domain models. Plain dataclasses, no ORM."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class User:
    id: Optional[int]
    name: str
    birthdate: datetime


@dataclass
class HealthRecord:
    id: Optional[int]
    user_id: int
    name: str
    birthdate: datetime
    systolic: int
    diastolic: int
    pulse: int
    reading_time: datetime
    standing: bool

    @property
    def position(self) -> str:
        return "Standing" if self.standing else "Sitting"


@dataclass
class ReadingDraft:
    """Result of a vision extraction, before user confirmation."""
    systolic: Optional[int] = None
    diastolic: Optional[int] = None
    pulse: Optional[int] = None
    confidence: float = 0.0
    raw_response: str = ""
    notes: list[str] = field(default_factory=list)

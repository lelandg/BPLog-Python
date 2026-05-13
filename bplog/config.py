"""Path resolution and runtime config for BPLog.

Reuses the same on-disk locations as the .NET WPF BPLog app so users
can switch between the two without migrating data.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

DEFAULT_BIND_ADDRESS = "100.71.212.38"
FALLBACK_BIND_ADDRESS = "127.0.0.1"


def documents_dir() -> Path:
    """Cross-platform 'Documents' folder.

    On Windows we read the same shell folder the .NET app uses
    (Environment.SpecialFolder.MyDocuments). On WSL/Linux/macOS we
    fall back to $HOME/Documents.
    """
    if sys.platform == "win32":
        import ctypes
        from ctypes import wintypes

        CSIDL_PERSONAL = 5
        SHGFP_TYPE_CURRENT = 0
        buf = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
        ctypes.windll.shell32.SHGetFolderPathW(
            None, CSIDL_PERSONAL, None, SHGFP_TYPE_CURRENT, buf
        )
        return Path(buf.value)
    return Path.home() / "Documents"


def appdata_dir() -> Path:
    """Cross-platform per-user app config dir.

    Windows: %APPDATA%\\BPLog  (matches the .NET app exactly)
    macOS/Linux/WSL: $XDG_CONFIG_HOME/BPLog or ~/.config/BPLog
    """
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming")))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))
    return base / "BPLog"


@dataclass(frozen=True)
class Paths:
    db: Path
    settings: Path
    images_dir: Path

    def ensure(self) -> None:
        self.db.parent.mkdir(parents=True, exist_ok=True)
        self.settings.parent.mkdir(parents=True, exist_ok=True)
        self.images_dir.mkdir(parents=True, exist_ok=True)


def default_paths() -> Paths:
    bp_dir = documents_dir() / "BPReadings"
    return Paths(
        db=bp_dir / "bloodpressure.db",
        settings=appdata_dir() / "settings.json",
        images_dir=bp_dir / "images",
    )

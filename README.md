# BPLog (Python)

Local blood pressure log with an HTML UI. Python port of the .NET WPF
[BPLog](../.Net/BPLog) app — reuses the same SQLite database and (a unified
form of) the same settings file, so you can switch over without losing data.

> **Status:** Scaffold only. See `../.Net/BPLog/Docs/plans/python-port-plan.md`
> for the full build plan. v0.1.0 is not yet runnable.

## Running (once implemented)

```bash
python -m venv .venv && source .venv/bin/activate   # Linux/macOS/WSL
# or: py -m venv .venv && .venv\Scripts\activate    # Windows PowerShell
pip install -e ".[dev]"
bplog
```

A browser tab opens at `http://127.0.0.1:<random-port>/`.

## Data locations (preserved from .NET app)

| What | Path |
|---|---|
| Readings DB | `~/Documents/BPReadings/bloodpressure.db` |
| Settings | `%APPDATA%/BPLog/settings.json` (Windows) or `~/.config/BPLog/settings.json` (Linux/macOS) |

## License

MIT — see [LICENSE](LICENSE).

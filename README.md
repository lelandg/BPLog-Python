# BPLog (Python)

Local blood pressure log with an HTML UI. Python port of the .NET WPF
[BPLog](../.Net/BPLog) app.

- **Same SQLite database** as the .NET app (`~/Documents/BPReadings/bloodpressure.db`),
  so you can switch between the two without migrating data.
- **Settings** live in the same `%APPDATA%/BPLog/settings.json` (Windows) or
  `~/.config/BPLog/settings.json` (Linux/WSL/macOS), with the same key names
  for `UserName`, `BirthDate`, `LastExportDateTime`, and `ExportStartDateTime`.
  A `server`, `reminders`, and `vision_model` sub-object are added on top — the
  .NET app ignores keys it doesn't know about.
- **AI image recognition.** Snap a photo of your BP monitor; Claude reads it,
  the form pre-fills, you confirm and save.
- **Reminders** via APScheduler, surfaced as a top-of-page banner.
- **NordVPN Meshnet friendly.** The server binds to the configured Meshnet IP
  so you can hit it from your phone over the secure overlay network.

## Install

```bash
# Linux / WSL / macOS
python3 -m venv .venv_linux
source .venv_linux/bin/activate
pip install -e ".[dev]"

# Windows PowerShell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

## Run

```bash
export ANTHROPIC_API_KEY=sk-ant-...   # required for photo extraction
bplog
```

On startup the server:

1. Resolves paths (DB at `~/Documents/BPReadings/bloodpressure.db`, images at
   `~/Documents/BPReadings/images/`, settings under `BPLog/settings.json`).
2. Picks a random free port.
3. Binds to the Meshnet IP from `settings.json` → `server.bind_address`
   (default `100.71.212.38`). Override with `BPLOG_BIND=<ip>`. If the bind
   fails (Meshnet adapter down), it falls back to `127.0.0.1`.
4. Generates a per-startup URL token and copies the full URL
   (`http://<host>:<port>/?t=<token>`) to your clipboard.
5. Opens the URL in your default browser.

To use it from your phone over Meshnet, paste the URL the app printed into
the phone's browser. Use the **Capture from photo** widget to snap the BP
monitor — the form pre-fills and you tap **Add**.

## Configuration

| Setting | Where | Notes |
|---|---|---|
| `ANTHROPIC_API_KEY` | env var | Required for photo extraction. Never put it in `settings.json`. |
| `BPLOG_BIND` | env var | Overrides the bind address. |
| `server.bind_address` | `settings.json` | Default Meshnet IP. |
| `vision_model` | `settings.json` / Settings page | Defaults to `claude-haiku-4-5`. |
| `reminders.times` | `settings.json` / Settings page | Comma-separated `HH:MM` list. |

## Data locations

| What | Path |
|---|---|
| Readings DB | `~/Documents/BPReadings/bloodpressure.db` |
| Capture images | `~/Documents/BPReadings/images/<reading-id>.jpg` |
| Settings | `%APPDATA%/BPLog/settings.json` (Windows) or `~/.config/BPLog/settings.json` |

## Switching between the .NET and Python apps

You can run one or the other at a time (single-user assumption — don't run
both simultaneously). Either reads/writes the same database; the Python app
adds extra keys to `settings.json` that the .NET app silently ignores. The
.NET app's separate reminder file (next to its binary) is no longer used by
the Python app — reminder state lives in the unified `settings.json`.

## Development

```bash
.venv_linux/bin/pytest -q
```

45 tests cover the repository layer, settings serialization, exporters, web
routes, URL-token middleware, reminder scheduling, and mocked vision
extraction.

## License

MIT — see [LICENSE](LICENSE).

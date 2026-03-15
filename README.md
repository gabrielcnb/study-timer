# study-timer-pomodoro

Desktop study timer with Pomodoro mode, per-subject tracking, session history, and chart reports.

## Screenshot

![Study Timer UI](docs/screenshot.png)

*No screenshot available yet. Place a screenshot at `docs/screenshot.png`.*

## Features

- Continuous timer mode and Pomodoro mode (configurable number of focus/break cycles, default: 4)
- Per-subject time tracking with built-in subjects (General, Math, Portuguese, English, History, Science) plus user-defined subjects added at runtime
- Daily target with progress bar showing completion toward the configured goal (default: 60 minutes)
- Session history persisted to `historico.csv` with columns: date, subject, duration, mode
- Manual session entry for logging study time without running the timer
- Bar chart reports via matplotlib showing time invested per subject
- Data export to JSON
- System tray integration (minimize to tray, restore on click)
- Theme switcher: dark-blue, green, purple, light

## Stack

| Component | Library | Purpose |
|---|---|---|
| UI framework | customtkinter | Main window, tabs, buttons, progress bar |
| Charts | matplotlib (TkAgg backend) | Session history bar charts |
| System tray | pystray | Minimize-to-tray icon |
| Icon rendering | Pillow | Dynamic tray icon generation |
| Session history | csv (stdlib) | Persistent session log |
| Data export | json (stdlib) | JSON export of all session data |

## Setup / Installation

**Requirements:** Python 3.9+

```bash
git clone https://github.com/gabrielcnb/study-timer-pomodoro.git
cd study-timer-pomodoro
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install customtkinter matplotlib pystray Pillow
python main.py
```

## Usage

```bash
python main.py
```

**Continuous mode:**
1. Select a subject from the dropdown.
2. Click "Start". The timer counts up.
3. Click "Stop" to end the session. The duration is saved to `historico.csv`.

**Pomodoro mode:**
1. Go to the "Settings" tab and click "Activate Pomodoro Mode".
2. Set the number of cycles in the "Pomodoro Cycles" field.
3. Return to the "Study" tab and click "Start". The timer alternates between focus and break intervals automatically.

**Manual entry:**
Click "Register Manually" to log a study duration without running the timer — useful for sessions tracked on paper or offline.

**Reports:**
Go to the "Reports" tab and click "Generate Chart" to see a bar chart of total time per subject.

**Export:**
In the "Settings" tab, click "Export Data (JSON)" to dump all session records to a JSON file.

**Session history file:**
```
historico.csv   (created automatically in the working directory on first run)
```

## File Structure

```
study-timer-pomodoro/
├── main.py          # Full application: timer logic, UI, CSV persistence, chart reports
├── historico.csv    # Auto-generated session log
├── app_icon.ico     # Optional window icon (place in project root)
└── README.md
```

# Study Timer Pomodoro

[![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![CustomTkinter](https://img.shields.io/badge/UI-CustomTkinter-orange)](https://github.com/TomSchimansky/CustomTkinter)

Desktop study timer with Pomodoro mode, per-subject tracking, session history, and chart reports.

## Features

- Continuous timer mode (count-up) and Pomodoro mode with configurable focus/break cycles
- Per-subject time tracking with built-in subjects (Geral, Matematica, Portugues, Ingles, Historia, Ciencias) and custom subjects added at runtime
- Daily target with progress bar showing completion toward a configurable goal (default: 60 min)
- Session history persisted to CSV with date, subject, duration, and mode
- Manual session entry for logging study time without running the timer
- Bar chart reports via matplotlib showing daily study hours (last 7 days)
- Gamification levels: Beginner, Advanced, Study Master based on total hours
- Full session history viewer in a separate window
- Data export to JSON
- System tray integration via pystray (minimize to tray, restore on click)
- Theme switcher: dark-blue, green, purple, light
- Tabbed interface: Study, Reports, Settings
- Auto-saves session on window close if timer is running

## Stack

| Component | Library | Purpose |
|---|---|---|
| UI framework | customtkinter | Main window, tabs, buttons, progress bar |
| Charts | matplotlib (TkAgg) | Daily study hours bar charts |
| System tray | pystray | Minimize-to-tray icon |
| Icon rendering | Pillow | Dynamic tray icon generation |
| Session history | csv (stdlib) | Persistent session log (`historico.csv`) |
| Data export | json (stdlib) | JSON export of all session data |

## Setup

**Requirements:** Python 3.9+

```bash
git clone https://github.com/gabrielcnb/study-timer-pomodoro.git
cd study-timer-pomodoro
pip install -r requirements.txt
```

Or install manually:

```bash
pip install customtkinter matplotlib pystray pillow
```

## Usage

```bash
python main.py
```

**Continuous mode:**
1. Select a subject from the dropdown.
2. Click "Start". The timer counts up.
3. Click "Pause" to stop. The duration is saved to `historico.csv`.

**Pomodoro mode:**
1. Go to "Settings" tab and click "Enable Pomodoro Mode".
2. Set the number of cycles (default: 4).
3. Return to "Study" tab and click "Start". Focus and break intervals alternate automatically based on the daily target.

**Manual entry:** Click "Log Manually" to log minutes without running the timer.

**Reports:** Go to "Reports" tab and click "Generate Chart" to see a bar chart of daily study hours.

**Export:** In "Settings", click "Export Data (JSON)" to save all records to `historico.json`.

## File Structure

```
study-timer-pomodoro/
├── main.py           # Full application: timer, UI, CSV persistence, charts
├── app_icon.ico      # Window icon
├── requirements.txt  # pip dependencies
├── LICENSE           # MIT
└── README.md
```

## License

[MIT](LICENSE)

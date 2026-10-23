# JASS LifeOS v0.3.0 — Advanced Productivity Edition

A local-first personal command center for Windows, built with Python, PySide6, and SQLite.

## Features
- Dashboard with open tasks, due-today tasks, notes, habits, and priority focus.
- Tasks with priorities, categories, due dates, completion state, and daily/weekly/monthly recurrence.
- Searchable, editable notes with pinning.
- Calendar view with task creation for a selected date.
- Habit check-ins and seven-day activity counts.
- Focus timer with configurable duration, pause/resume, and completion alert.
- Document/file/folder shortcuts that never move or delete original files.
- Productivity analytics, completion rate, overdue count, and category breakdown.
- Export tasks to UTF-8 CSV and notes to Markdown.
- Persistent light/dark appearance setting.
- In-app due-today/overdue status reminders while the app is running.
- SQLite backup and restore with a safety copy before restore.
- Keyboard shortcuts: Ctrl+N, Ctrl+F, Ctrl+Shift+B.
- Local-first storage; no account, telemetry, or cloud sync.

## Run (no virtual environment required)
Install Python 3.10+ and run in PowerShell from the project directory:

```powershell
python -m pip install -r requirements.txt
python run.py
```

Alternatively, double-click `Launch-LifeOS.bat` after installing the dependency.

## Safe upgrade procedure
1. In your current LifeOS, open **Settings & backup → Create backup**.
2. Extract this release into a separate folder and test it first.
3. The app uses the same data folder as prior versions. For an isolated test, use a separate Windows user profile or a test copy configured in `app/database.py`.
4. Only replace your working source after verifying the new version. Keep your backup.

Database location on Windows: `%LOCALAPPDATA%\JASS Digital\LifeOS\lifeos.sqlite`

The migration adds settings and completion-timestamp columns without deleting existing records. Old completed tasks have no historical completion timestamp, so they won't count in the new "completed this week" metric unless completed again after this version.

## Reminder limitation
Reminders appear in the LifeOS status bar while the app is open. They are not Windows notifications when the app is closed.

## Optional standalone Windows executable
Install PyInstaller, then run:

```powershell
python -m pip install pyinstaller
pyinstaller --noconfirm --windowed --name JASS-LifeOS run.py
```

The executable will be created in `dist\JASS-LifeOS`. Test the packaged executable before distributing it.

## Release validation
Python syntax and database migration tests are included. Complete GUI validation on Windows before publishing.

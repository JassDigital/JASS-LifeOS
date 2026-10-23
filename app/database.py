import os
import sqlite3
from pathlib import Path

if os.name == "nt":
    APP_DIR = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "JASS Digital" / "LifeOS"
else:
    APP_DIR = Path.home() / ".local" / "share" / "jass-lifeos"
DB_PATH = APP_DIR / "lifeos.sqlite"


def connect():
    APP_DIR.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def _add_column(con, table, column, definition):
    columns = {row["name"] for row in con.execute(f"PRAGMA table_info({table})")}
    if column not in columns:
        con.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def initialize():
    with connect() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            details TEXT NOT NULL DEFAULT '',
            priority TEXT NOT NULL DEFAULT 'Normal',
            due_date TEXT NOT NULL DEFAULT '',
            done INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            body TEXT NOT NULL DEFAULT '',
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            label TEXT NOT NULL,
            path TEXT NOT NULL,
            added_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS habits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS habit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            habit_id INTEGER NOT NULL REFERENCES habits(id) ON DELETE CASCADE,
            log_date TEXT NOT NULL,
            UNIQUE(habit_id, log_date)
        );
        CREATE TABLE IF NOT EXISTS app_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        """)
        _add_column(con, "tasks", "category", "TEXT NOT NULL DEFAULT 'Personal'")
        _add_column(con, "tasks", "recurrence", "TEXT NOT NULL DEFAULT 'Never'")
        _add_column(con, "tasks", "completed_at", "TEXT NOT NULL DEFAULT ''")
        _add_column(con, "notes", "pinned", "INTEGER NOT NULL DEFAULT 0")

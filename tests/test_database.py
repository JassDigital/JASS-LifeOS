import sqlite3
import tempfile
import unittest
from pathlib import Path

import app.database as database


class DatabaseMigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.original_app_dir = database.APP_DIR
        self.original_db_path = database.DB_PATH
        database.APP_DIR = Path(self.temp.name)
        database.DB_PATH = database.APP_DIR / "lifeos.sqlite"

    def tearDown(self):
        database.APP_DIR = self.original_app_dir
        database.DB_PATH = self.original_db_path
        self.temp.cleanup()

    def test_initialize_creates_tables_and_columns(self):
        database.initialize()
        with database.connect() as con:
            tables = {r["name"] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            self.assertTrue({"tasks", "notes", "documents", "habits", "habit_logs", "app_settings"}.issubset(tables))
            task_columns = {r["name"] for r in con.execute("PRAGMA table_info(tasks)")}
            self.assertTrue({"category", "recurrence", "completed_at"}.issubset(task_columns))
            note_columns = {r["name"] for r in con.execute("PRAGMA table_info(notes)")}
            self.assertIn("pinned", note_columns)

    def test_migration_preserves_existing_v02_data(self):
        database.APP_DIR.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(database.DB_PATH) as con:
            con.executescript("""
                CREATE TABLE tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    details TEXT NOT NULL DEFAULT '',
                    priority TEXT NOT NULL DEFAULT 'Normal',
                    due_date TEXT NOT NULL DEFAULT '',
                    done INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    category TEXT NOT NULL DEFAULT 'Personal',
                    recurrence TEXT NOT NULL DEFAULT 'Never'
                );
                CREATE TABLE notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    body TEXT NOT NULL DEFAULT '',
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    pinned INTEGER NOT NULL DEFAULT 0
                );
                INSERT INTO tasks(title, details) VALUES ('Preserve me', 'Existing task');
                INSERT INTO notes(title, body) VALUES ('Existing note', 'Existing body');
            """)
        database.initialize()
        with database.connect() as con:
            task = con.execute("SELECT title, completed_at FROM tasks WHERE id=1").fetchone()
            note = con.execute("SELECT title FROM notes WHERE id=1").fetchone()
            self.assertEqual(task["title"], "Preserve me")
            self.assertEqual(task["completed_at"], "")
            self.assertEqual(note["title"], "Existing note")

    def test_settings_upsert(self):
        database.initialize()
        with database.connect() as con:
            con.execute("INSERT INTO app_settings(key,value) VALUES('dark_mode','1')")
            con.execute("INSERT INTO app_settings(key,value) VALUES('dark_mode','0') ON CONFLICT(key) DO UPDATE SET value=excluded.value")
            self.assertEqual(con.execute("SELECT value FROM app_settings WHERE key='dark_mode'").fetchone()["value"], "0")


if __name__ == "__main__":
    unittest.main()

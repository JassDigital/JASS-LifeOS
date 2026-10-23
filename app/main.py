import os
import sys
import shutil
import subprocess
import csv
import re
from pathlib import Path
from datetime import date, datetime, timedelta

from PySide6.QtCore import Qt, QDate, QTimer
from PySide6.QtGui import QAction, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QStackedWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QLineEdit, QTextEdit, QComboBox, QDateEdit, QMessageBox,
    QDialog, QFormLayout, QDialogButtonBox, QFileDialog, QListWidget,
    QListWidgetItem, QAbstractItemView, QSplitter, QCalendarWidget,
    QSpinBox, QCheckBox, QInputDialog, QProgressBar
)
from .database import initialize, connect, DB_PATH, APP_DIR

STYLE = """
QWidget { background:#f4f6fb; color:#182238; font-family:'Segoe UI'; font-size:10pt; }
QMainWindow { background:#f4f6fb; }
QFrame#Sidebar { background:#111827; border:0; }
QLabel#Brand { color:#fff; font-size:18pt; font-weight:700; padding:8px 4px 2px; }
QLabel#BrandSub { color:#9ca9c0; font-size:8pt; padding:0 4px 12px; }
QPushButton#NavButton { color:#cbd5e1; background:transparent; border:0; text-align:left; padding:11px 12px; border-radius:9px; font-weight:600; }
QPushButton#NavButton:hover { background:#253147; color:white; }
QPushButton#NavButton:checked { background:#3157d5; color:white; }
QLabel#PageTitle { font-size:22pt; font-weight:700; color:#111827; }
QLabel#Muted { color:#68758b; }
QFrame#Panel, QFrame#StatCard { background:#fff; border:1px solid #e5eaf2; border-radius:14px; }
QLabel#StatNumber { font-size:25pt; font-weight:700; color:#172033; }
QLabel#StatLabel { color:#68758b; font-weight:600; }
QPushButton { background:#3157d5; color:white; border:0; border-radius:8px; padding:9px 13px; font-weight:600; }
QPushButton:hover { background:#2648bc; }
QPushButton#Secondary { background:#e9eef8; color:#24324c; }
QPushButton#Secondary:hover { background:#dce5f5; }
QPushButton#Danger { background:#fff0f0; color:#a32626; }
QLineEdit, QTextEdit, QComboBox, QDateEdit, QSpinBox { background:white; border:1px solid #d8dfeb; border-radius:8px; padding:8px; selection-background-color:#3157d5; }
QTableWidget, QListWidget, QCalendarWidget { background:white; border:1px solid #e5eaf2; border-radius:10px; gridline-color:#edf0f6; }
QHeaderView::section { background:#f0f3f9; color:#536078; border:0; padding:9px; font-weight:700; }
QTableWidget::item { padding:5px; }
QProgressBar { border:0; border-radius:5px; background:#e8edf7; text-align:center; height:10px; }
QProgressBar::chunk { border-radius:5px; background:#3157d5; }
QDialog { background:#f4f6fb; }
"""

def lbl(text, name=None):
    w = QLabel(text)
    if name: w.setObjectName(name)
    return w

def panel():
    f = QFrame()
    f.setObjectName("Panel")
    return f

def confirm(parent, title, message):
    return QMessageBox.question(parent, title, message) == QMessageBox.StandardButton.Yes


DARK_STYLE = """
QWidget { background:#171b26; color:#e8ecf5; font-family:'Segoe UI'; font-size:10pt; }
QMainWindow { background:#171b26; }
QFrame#Sidebar { background:#0b1020; border:0; }
QLabel#Brand { color:#fff; font-size:18pt; font-weight:700; padding:8px 4px 2px; }
QLabel#BrandSub { color:#9ca9c0; font-size:8pt; padding:0 4px 12px; }
QPushButton#NavButton { color:#cbd5e1; background:transparent; border:0; text-align:left; padding:11px 12px; border-radius:9px; font-weight:600; }
QPushButton#NavButton:hover { background:#273247; color:white; }
QPushButton#NavButton:checked { background:#3157d5; color:white; }
QLabel#PageTitle { font-size:22pt; font-weight:700; color:#f4f6fb; }
QLabel#Muted { color:#a2aec4; }
QFrame#Panel, QFrame#StatCard { background:#222938; border:1px solid #343d50; border-radius:14px; }
QLabel#StatNumber { font-size:25pt; font-weight:700; color:#f4f6fb; }
QLabel#StatLabel { color:#a2aec4; font-weight:600; }
QPushButton { background:#4169e1; color:white; border:0; border-radius:8px; padding:9px 13px; font-weight:600; }
QPushButton:hover { background:#3157d5; }
QPushButton#Secondary { background:#30394c; color:#e5eaf5; }
QPushButton#Secondary:hover { background:#3b465c; }
QPushButton#Danger { background:#482c35; color:#ffb7bd; }
QLineEdit, QTextEdit, QComboBox, QDateEdit, QSpinBox { background:#202737; color:#f0f3fa; border:1px solid #3c465a; border-radius:8px; padding:8px; selection-background-color:#4169e1; }
QTableWidget, QListWidget, QCalendarWidget { background:#202737; color:#e8ecf5; border:1px solid #343d50; border-radius:10px; gridline-color:#343d50; }
QHeaderView::section { background:#2a3345; color:#cbd5e1; border:0; padding:9px; font-weight:700; }
QTableWidget::item { padding:5px; }
QProgressBar { border:0; border-radius:5px; background:#30394c; text-align:center; height:10px; }
QProgressBar::chunk { border-radius:5px; background:#4169e1; }
QDialog { background:#171b26; }
"""

class TaskDialog(QDialog):
    def __init__(self, parent=None, row=None):
        super().__init__(parent)
        self.setWindowTitle("Edit task" if row else "New task")
        self.setMinimumWidth(470)
        self.title = QLineEdit()
        self.details = QTextEdit()
        self.details.setMaximumHeight(95)
        self.priority = QComboBox(); self.priority.addItems(["Low","Normal","High","Urgent"])
        self.category = QComboBox(); self.category.setEditable(True)
        self.category.addItems(["Personal","Work","Family","Finance","Health","Learning","Errands","Other"])
        self.recurrence = QComboBox(); self.recurrence.addItems(["Never","Daily","Weekly","Monthly"])
        self.no_due = QCheckBox("No due date")
        self.due = QDateEdit(); self.due.setCalendarPopup(True); self.due.setDisplayFormat("yyyy-MM-dd"); self.due.setDate(QDate.currentDate())
        self.no_due.toggled.connect(self.due.setDisabled)
        form = QFormLayout()
        form.addRow("Task title", self.title); form.addRow("Details", self.details)
        form.addRow("Priority", self.priority); form.addRow("Category", self.category)
        form.addRow("Repeat", self.recurrence); form.addRow("Due date", self.due); form.addRow("", self.no_due)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject)
        lay = QVBoxLayout(self); lay.addLayout(form); lay.addWidget(buttons)
        if row:
            self.title.setText(row["title"]); self.details.setPlainText(row["details"])
            self.priority.setCurrentText(row["priority"]); self.category.setCurrentText(row["category"] or "Personal")
            self.recurrence.setCurrentText(row["recurrence"] or "Never")
            if row["due_date"]:
                qd = QDate.fromString(row["due_date"], "yyyy-MM-dd")
                if qd.isValid(): self.due.setDate(qd)
            else: self.no_due.setChecked(True)
    def values(self):
        return (self.title.text().strip(), self.details.toPlainText().strip(),
                self.priority.currentText(), self.category.currentText().strip() or "Personal",
                "" if self.no_due.isChecked() else self.due.date().toString("yyyy-MM-dd"),
                self.recurrence.currentText())

class NoteDialog(QDialog):
    def __init__(self, parent=None, row=None):
        super().__init__(parent); self.setWindowTitle("Edit note" if row else "New note"); self.setMinimumSize(540,430)
        self.title = QLineEdit(); self.body = QTextEdit(); self.pinned = QCheckBox("Pin this note")
        lay = QVBoxLayout(self); lay.addWidget(lbl("Title")); lay.addWidget(self.title); lay.addWidget(self.pinned)
        lay.addWidget(lbl("Note")); lay.addWidget(self.body,1)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject); lay.addWidget(buttons)
        if row:
            self.title.setText(row["title"]); self.body.setPlainText(row["body"]); self.pinned.setChecked(bool(row["pinned"]))
    def values(self): return self.title.text().strip(), self.body.toPlainText().strip(), int(self.pinned.isChecked())

class HabitDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent); self.setWindowTitle("Add habit")
        self.name = QLineEdit(); self.description = QLineEdit()
        form = QFormLayout(self); form.addRow("Habit", self.name); form.addRow("Why it matters", self.description)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject); form.addRow(buttons)

class LifeOS(QMainWindow):
    NAV = [("◈   Overview",0),("✓   Tasks",1),("✎   Notes",2),("▦   Calendar",3),("↗   Habits",4),("▣   Documents",5),("◷   Focus timer",6),("▥   Analytics",7),("⚙   Settings & backup",8)]
    TITLES = [
        ("Good day","Your personal overview for today."),
        ("Tasks","Prioritize, categorize, and track your work."),
        ("Notes","Capture ideas. Pin the ones that matter."),
        ("Calendar","See tasks by date and plan the days ahead."),
        ("Habits","Build consistency one day at a time."),
        ("Documents","Local file shortcuts. Your originals stay in place."),
        ("Focus timer","Protect time for meaningful work."),
        ("Analytics","Understand your productivity patterns."),
        ("Settings & backup","Personalize LifeOS and protect your data.")
    ]
    def __init__(self):
        super().__init__()
        self.setWindowTitle("JASS LifeOS")
        self.resize(1280,820); self.setMinimumSize(1020,680)
        self.nav_buttons=[]; self.current_note_id=None; self.focus_seconds=25*60; self.remaining=self.focus_seconds; self.timer_running=False
        self.timer=QTimer(self); self.timer.setInterval(1000); self.timer.timeout.connect(self.tick)
        self.dark_mode = self.get_setting("dark_mode", "0") == "1"
        self.reminder_timer=QTimer(self); self.reminder_timer.setInterval(5*60*1000); self.reminder_timer.timeout.connect(self.check_reminders)
        self.reminder_timer.start()
        self._reminder_signature = ""
        root=QWidget(); self.setCentralWidget(root); outer=QHBoxLayout(root); outer.setContentsMargins(0,0,0,0); outer.setSpacing(0)
        sidebar=QFrame(); sidebar.setObjectName("Sidebar"); sidebar.setFixedWidth(226)
        sl=QVBoxLayout(sidebar); sl.setContentsMargins(16,20,16,18); sl.setSpacing(5)
        sl.addWidget(lbl("JASS LifeOS","Brand")); sl.addWidget(lbl("YOUR PERSONAL COMMAND CENTER","BrandSub"))
        for text,i in self.NAV:
            b=QPushButton(text); b.setObjectName("NavButton"); b.setCheckable(True); b.clicked.connect(lambda checked=False, idx=i:self.navigate(idx))
            self.nav_buttons.append(b); sl.addWidget(b)
        sl.addStretch(1); sl.addWidget(lbl("LOCAL-FIRST  •  PRIVATE BY DESIGN","BrandSub"))
        outer.addWidget(sidebar)
        content=QWidget(); self.content=QVBoxLayout(content); self.content.setContentsMargins(26,22,26,20); self.content.setSpacing(16); outer.addWidget(content,1)
        head=QHBoxLayout(); titlebox=QVBoxLayout(); titlebox.setSpacing(2)
        self.page_title=lbl("Good day","PageTitle"); self.page_sub=lbl("Your personal overview for today.","Muted")
        titlebox.addWidget(self.page_title); titlebox.addWidget(self.page_sub); head.addLayout(titlebox); head.addStretch(1)
        self.global_search=QLineEdit(); self.global_search.setPlaceholderText("Search tasks & notes…"); self.global_search.setMaximumWidth(250); self.global_search.returnPressed.connect(self.global_search_run); head.addWidget(self.global_search)
        self.quick=QPushButton("+ New task"); self.quick.clicked.connect(self.add_task); head.addWidget(self.quick); self.content.addLayout(head)
        self.pages=QStackedWidget(); self.content.addWidget(self.pages,1)
        builders=[self.build_dashboard,self.build_tasks,self.build_notes,self.build_calendar,self.build_habits,self.build_documents,self.build_focus,self.build_analytics,self.build_settings]
        for fn in builders: self.pages.addWidget(fn())
        self.navigate(0); self.refresh_all()
        self.apply_theme()
        self.check_reminders()
        file_menu=self.menuBar().addMenu("File")
        for name,fn in [("Refresh",self.refresh_all),("Create backup",self.backup_db),("Exit",self.close)]:
            a=QAction(name,self); a.triggered.connect(fn); file_menu.addAction(a)
        QShortcut(QKeySequence("Ctrl+N"),self).activated.connect(self.quick_new)
        QShortcut(QKeySequence("Ctrl+F"),self).activated.connect(self.global_search.setFocus)
        QShortcut(QKeySequence("Ctrl+Shift+B"),self).activated.connect(self.backup_db)
        self.statusBar().showMessage(f"Ready • Local database: {DB_PATH}")

    def navigate(self,i):
        self.pages.setCurrentIndex(i)
        for j,b in enumerate(self.nav_buttons): b.setChecked(i==j)
        self.page_title.setText(self.TITLES[i][0]); self.page_sub.setText(self.TITLES[i][1])
        self.quick.setVisible(i in (0,1,2))
        self.quick.setText("+ New note" if i==2 else "+ New task")
        try: self.quick.clicked.disconnect()
        except RuntimeError: pass
        self.quick.clicked.connect(self.add_note if i==2 else self.add_task)
        if i==3: self.refresh_calendar()
        if i==4: self.refresh_habits()
        if i==5: self.refresh_documents()
        if i==7: self.refresh_analytics()

    def quick_new(self):
        if self.pages.currentIndex()==2: self.add_note()
        else: self.add_task()

    def make_stat(self,title,desc):
        f=QFrame(); f.setObjectName("StatCard"); l=QVBoxLayout(f); l.setContentsMargins(17,14,17,14)
        l.addWidget(lbl(title,"StatLabel")); n=lbl("0","StatNumber"); l.addWidget(n); l.addWidget(lbl(desc,"Muted")); f.number=n
        return f

    def build_dashboard(self):
        page=QWidget(); l=QVBoxLayout(page); l.setContentsMargins(0,0,0,0); l.setSpacing(14)
        stats=QHBoxLayout()
        self.stat_open=self.make_stat("Open tasks","Ready for action")
        self.stat_today=self.make_stat("Due today","Today's commitments")
        self.stat_notes=self.make_stat("Notes","Ideas saved")
        self.stat_habits=self.make_stat("Habits today","Daily check-ins")
        for x in [self.stat_open,self.stat_today,self.stat_notes,self.stat_habits]: stats.addWidget(x,1)
        l.addLayout(stats)
        row=QHBoxLayout()
        focus=panel(); fl=QVBoxLayout(focus); fl.setContentsMargins(18,16,18,16); fl.addWidget(lbl("Priority focus"))
        fl.addWidget(lbl("Urgent, high-priority, and upcoming tasks.","Muted"))
        self.focus_list=QListWidget(); fl.addWidget(self.focus_list,1)
        btn=QPushButton("Open tasks →"); btn.setObjectName("Secondary"); btn.clicked.connect(lambda:self.navigate(1)); fl.addWidget(btn)
        right=panel(); rl=QVBoxLayout(right); rl.setContentsMargins(18,16,18,16); rl.addWidget(lbl("Quick capture"))
        rl.addWidget(lbl("Keep your mind clear; save it here.","Muted"))
        for text,fn in [("＋  Add a task",self.add_task),("✎  Write a note",self.add_note),("▣  Add document shortcut",self.add_document),("◷  Start focus session",lambda:self.navigate(6))]:
            b=QPushButton(text); b.setObjectName("Secondary" if "task" not in text.lower() else ""); b.clicked.connect(fn); rl.addWidget(b)
        rl.addStretch(1)
        self.daily_quote=lbl("“Great things are done by a series of small things brought together.”","Muted"); self.daily_quote.setWordWrap(True); rl.addWidget(self.daily_quote)
        row.addWidget(focus,3); row.addWidget(right,2); l.addLayout(row,1)
        return page

    def build_tasks(self):
        p=QWidget(); l=QVBoxLayout(p); bar=QHBoxLayout()
        self.task_search=QLineEdit(); self.task_search.setPlaceholderText("Search task title, details, category…"); self.task_search.textChanged.connect(self.refresh_tasks)
        self.task_filter=QComboBox(); self.task_filter.addItems(["All tasks","Open tasks","Completed","Overdue"]); self.task_filter.currentTextChanged.connect(self.refresh_tasks)
        self.category_filter=QComboBox(); self.category_filter.addItems(["All categories","Personal","Work","Family","Finance","Health","Learning","Errands","Other"]); self.category_filter.currentTextChanged.connect(self.refresh_tasks)
        add=QPushButton("+ Add task"); add.clicked.connect(self.add_task)
        for w in [self.task_search,self.task_filter,self.category_filter,add]: bar.addWidget(w)
        l.addLayout(bar)
        self.task_table=QTableWidget(0,7); self.task_table.setHorizontalHeaderLabels(["Task","Category","Priority","Due date","Repeat","Status","Actions"])
        self.task_table.horizontalHeader().setSectionResizeMode(0,QHeaderView.ResizeMode.Stretch)
        for c in range(1,7): self.task_table.horizontalHeader().setSectionResizeMode(c,QHeaderView.ResizeMode.ResizeToContents)
        self.task_table.verticalHeader().setVisible(False); self.task_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows); self.task_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.task_table.cellDoubleClicked.connect(self.edit_task_from_row); l.addWidget(self.task_table,1)
        return p

    def build_notes(self):
        p=QWidget(); l=QVBoxLayout(p); bar=QHBoxLayout()
        self.note_search=QLineEdit(); self.note_search.setPlaceholderText("Search note title or content…"); self.note_search.textChanged.connect(self.refresh_notes)
        add=QPushButton("+ New note"); add.clicked.connect(self.add_note); bar.addWidget(self.note_search,1); bar.addWidget(add); l.addLayout(bar)
        sp=QSplitter(Qt.Orientation.Horizontal); self.note_list=QListWidget(); self.note_list.currentItemChanged.connect(self.show_note)
        sp.addWidget(self.note_list)
        box=panel(); bl=QVBoxLayout(box); bl.setContentsMargins(18,16,18,16)
        self.note_title=lbl("Select a note","PageTitle"); self.note_title.setStyleSheet("font-size:17pt;")
        self.note_body=QTextEdit(); self.note_body.setReadOnly(True)
        row=QHBoxLayout(); edit=QPushButton("Edit"); edit.setObjectName("Secondary"); edit.clicked.connect(self.edit_note)
        pin=QPushButton("Pin / unpin"); pin.setObjectName("Secondary"); pin.clicked.connect(self.toggle_pin)
        delete=QPushButton("Delete"); delete.setObjectName("Danger"); delete.clicked.connect(self.delete_note)
        row.addWidget(edit); row.addWidget(pin); row.addWidget(delete)
        bl.addWidget(self.note_title); bl.addWidget(self.note_body,1); bl.addLayout(row); sp.addWidget(box); sp.setSizes([270,700]); l.addWidget(sp,1)
        return p

    def build_calendar(self):
        p=QWidget(); l=QHBoxLayout(p); l.setContentsMargins(0,0,0,0)
        left=panel(); ll=QVBoxLayout(left); ll.setContentsMargins(12,12,12,12)
        self.calendar=QCalendarWidget(); self.calendar.selectionChanged.connect(self.refresh_calendar); ll.addWidget(self.calendar)
        self.calendar_date_label=lbl("Tasks for selected date","StatLabel"); ll.addWidget(self.calendar_date_label)
        l.addWidget(left,1)
        right=panel(); rl=QVBoxLayout(right); rl.setContentsMargins(16,14,16,14); rl.addWidget(lbl("Scheduled tasks"))
        self.calendar_tasks=QListWidget(); rl.addWidget(self.calendar_tasks,1)
        add=QPushButton("+ Task on this date"); add.clicked.connect(self.add_task_for_calendar_date); rl.addWidget(add)
        l.addWidget(right,1); return p

    def build_habits(self):
        p=QWidget(); l=QVBoxLayout(p); top=QHBoxLayout()
        top.addWidget(lbl("Small actions, repeated daily, become habits.","Muted"),1)
        add=QPushButton("+ Add habit"); add.clicked.connect(self.add_habit); top.addWidget(add); l.addLayout(top)
        self.habit_table=QTableWidget(0,5); self.habit_table.setHorizontalHeaderLabels(["Habit","Why it matters","Today","7-day count","Action"])
        self.habit_table.horizontalHeader().setSectionResizeMode(0,QHeaderView.ResizeMode.ResizeToContents)
        self.habit_table.horizontalHeader().setSectionResizeMode(1,QHeaderView.ResizeMode.Stretch)
        self.habit_table.horizontalHeader().setSectionResizeMode(2,QHeaderView.ResizeMode.ResizeToContents)
        self.habit_table.horizontalHeader().setSectionResizeMode(3,QHeaderView.ResizeMode.ResizeToContents)
        self.habit_table.horizontalHeader().setSectionResizeMode(4,QHeaderView.ResizeMode.ResizeToContents)
        self.habit_table.verticalHeader().setVisible(False); l.addWidget(self.habit_table,1)
        l.addWidget(lbl("* 7-day count shows check-ins over the last seven calendar days.","Muted"))
        return p

    def build_documents(self):
        p=QWidget(); l=QVBoxLayout(p); info=panel(); il=QVBoxLayout(info); il.setContentsMargins(16,12,16,12)
        il.addWidget(lbl("Document shortcuts")); il.addWidget(lbl("LifeOS stores paths only; it never moves or deletes your original files.","Muted")); l.addWidget(info)
        bar=QHBoxLayout(); self.doc_search=QLineEdit(); self.doc_search.setPlaceholderText("Search shortcuts…"); self.doc_search.textChanged.connect(self.refresh_documents)
        add=QPushButton("+ Add file or folder"); add.clicked.connect(self.add_document); bar.addWidget(self.doc_search,1); bar.addWidget(add); l.addLayout(bar)
        self.doc_table=QTableWidget(0,3); self.doc_table.setHorizontalHeaderLabels(["Name","Path","Actions"])
        self.doc_table.horizontalHeader().setSectionResizeMode(0,QHeaderView.ResizeMode.ResizeToContents); self.doc_table.horizontalHeader().setSectionResizeMode(1,QHeaderView.ResizeMode.Stretch); self.doc_table.horizontalHeader().setSectionResizeMode(2,QHeaderView.ResizeMode.ResizeToContents)
        self.doc_table.verticalHeader().setVisible(False); self.doc_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers); l.addWidget(self.doc_table,1); return p

    def build_focus(self):
        p=QWidget(); l=QVBoxLayout(p); l.setAlignment(Qt.AlignmentFlag.AlignTop|Qt.AlignmentFlag.AlignHCenter)
        box=panel(); box.setMaximumWidth(650); bl=QVBoxLayout(box); bl.setContentsMargins(36,30,36,30); bl.setSpacing(16)
        bl.addWidget(lbl("FOCUS SESSION","StatLabel"),0,Qt.AlignmentFlag.AlignHCenter)
        self.timer_label=lbl("25:00","PageTitle"); self.timer_label.setStyleSheet("font-size:48pt;"); bl.addWidget(self.timer_label,0,Qt.AlignmentFlag.AlignHCenter)
        self.timer_progress=QProgressBar(); self.timer_progress.setRange(0,1500); self.timer_progress.setValue(1500); self.timer_progress.setTextVisible(False); bl.addWidget(self.timer_progress)
        mode=QHBoxLayout(); mode.addWidget(lbl("Session length (minutes)"))
        self.focus_length=QSpinBox(); self.focus_length.setRange(1,180); self.focus_length.setValue(25); self.focus_length.valueChanged.connect(self.set_focus_length); mode.addWidget(self.focus_length); bl.addLayout(mode)
        row=QHBoxLayout(); self.timer_start=QPushButton("Start focus"); self.timer_start.clicked.connect(self.start_pause_timer)
        reset=QPushButton("Reset"); reset.setObjectName("Secondary"); reset.clicked.connect(self.reset_timer)
        row.addWidget(self.timer_start); row.addWidget(reset); bl.addLayout(row)
        bl.addWidget(lbl("Try 25 minutes of focused work, then take a short break.","Muted"),0,Qt.AlignmentFlag.AlignHCenter)
        l.addWidget(box); return p

    def build_analytics(self):
        p=QWidget(); l=QVBoxLayout(p); l.setContentsMargins(0,0,0,0); l.setSpacing(14)
        cards=QHBoxLayout()
        self.analytics_completed=self.make_stat("Completed tasks","All-time completed")
        self.analytics_rate=self.make_stat("Completion rate","Completed / all tasks")
        self.analytics_overdue=self.make_stat("Overdue tasks","Open and past due")
        self.analytics_week=self.make_stat("Completed this week","Completion date in last 7 days")
        for card in [self.analytics_completed,self.analytics_rate,self.analytics_overdue,self.analytics_week]: cards.addWidget(card,1)
        l.addLayout(cards)
        box=panel(); bl=QVBoxLayout(box); bl.setContentsMargins(18,16,18,16)
        bl.addWidget(lbl("Productivity breakdown by category"))
        self.analytics_table=QTableWidget(0,3); self.analytics_table.setHorizontalHeaderLabels(["Category","Total tasks","Completed"])
        self.analytics_table.horizontalHeader().setSectionResizeMode(0,QHeaderView.ResizeMode.Stretch)
        self.analytics_table.horizontalHeader().setSectionResizeMode(1,QHeaderView.ResizeMode.ResizeToContents)
        self.analytics_table.horizontalHeader().setSectionResizeMode(2,QHeaderView.ResizeMode.ResizeToContents)
        self.analytics_table.verticalHeader().setVisible(False); self.analytics_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        bl.addWidget(self.analytics_table); l.addWidget(box,1)
        row=QHBoxLayout()
        a=QPushButton("Export tasks to CSV"); a.clicked.connect(self.export_tasks_csv)
        b=QPushButton("Export notes to Markdown"); b.setObjectName("Secondary"); b.clicked.connect(self.export_notes_markdown)
        row.addWidget(a); row.addWidget(b); row.addStretch(1); l.addLayout(row)
        return p

    def build_settings(self):
        p=QWidget(); l=QVBoxLayout(p); l.setAlignment(Qt.AlignmentFlag.AlignTop)
        db=panel(); dl=QVBoxLayout(db); dl.setContentsMargins(20,18,20,18)
        dl.addWidget(lbl("Your data")); dl.addWidget(lbl(f"Database location: {DB_PATH}","Muted"))
        row=QHBoxLayout()
        b=QPushButton("Create backup"); b.clicked.connect(self.backup_db)
        r=QPushButton("Restore from backup"); r.setObjectName("Secondary"); r.clicked.connect(self.restore_db)
        e=QPushButton("Open data folder"); e.setObjectName("Secondary"); e.clicked.connect(self.open_data_folder)
        row.addWidget(b); row.addWidget(r); row.addWidget(e); dl.addLayout(row)
        self.dark_toggle=QCheckBox("Enable dark mode")
        self.dark_toggle.setChecked(self.dark_mode)
        self.dark_toggle.toggled.connect(self.set_dark_mode)
        dl.addWidget(self.dark_toggle)
        self.reminder_toggle=QCheckBox("Show deadline reminders while LifeOS is running")
        self.reminder_toggle.setChecked(self.get_setting("reminders_enabled","1")=="1")
        self.reminder_toggle.toggled.connect(lambda checked:self.set_setting("reminders_enabled","1" if checked else "0"))
        dl.addWidget(self.reminder_toggle)
        l.addWidget(db)
        shortcuts=panel(); sl=QVBoxLayout(shortcuts); sl.setContentsMargins(20,18,20,18); sl.addWidget(lbl("Keyboard shortcuts"))
        for t in ["Ctrl + N   Add a task or note","Ctrl + F   Focus global search","Ctrl + Shift + B   Create database backup","Double-click a task   Edit task"]:
            sl.addWidget(lbl("•  "+t))
        l.addWidget(shortcuts)
        about=panel(); al=QVBoxLayout(about); al.setContentsMargins(20,18,20,18); al.addWidget(lbl("About JASS LifeOS"))
        al.addWidget(lbl("A local-first personal command center by JASS Digital. No account or cloud service is required.","Muted"))
        al.addWidget(lbl("Backups contain your LifeOS database. Store them somewhere safe.","Muted")); l.addWidget(about)
        return p

    def refresh_analytics(self):
        if not hasattr(self,"analytics_table"): return
        today=date.today().isoformat()
        week=(date.today()-timedelta(days=6)).isoformat()
        with connect() as c:
            total=c.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
            done=c.execute("SELECT COUNT(*) FROM tasks WHERE done=1").fetchone()[0]
            overdue=c.execute("SELECT COUNT(*) FROM tasks WHERE done=0 AND due_date<>'' AND due_date<?",(today,)).fetchone()[0]
            week_done=c.execute("SELECT COUNT(*) FROM tasks WHERE done=1 AND completed_at != '' AND date(completed_at)>=?",(week,)).fetchone()[0]
            groups=c.execute("SELECT category,COUNT(*) total,SUM(done) completed FROM tasks GROUP BY category ORDER BY category COLLATE NOCASE").fetchall()
        rate=round((done/total)*100) if total else 0
        self.analytics_completed.number.setText(str(done)); self.analytics_rate.number.setText(f"{rate}%")
        self.analytics_overdue.number.setText(str(overdue)); self.analytics_week.number.setText(str(week_done))
        self.analytics_table.setRowCount(0)
        for g in groups:
            r=self.analytics_table.rowCount(); self.analytics_table.insertRow(r)
            self.analytics_table.setItem(r,0,QTableWidgetItem(g["category"] or "Other"))
            self.analytics_table.setItem(r,1,QTableWidgetItem(str(g["total"])))
            self.analytics_table.setItem(r,2,QTableWidgetItem(str(g["completed"] or 0)))
        if not groups:
            self.analytics_table.insertRow(0); self.analytics_table.setItem(0,0,QTableWidgetItem("No tasks yet"))

    def export_tasks_csv(self):
        path,_=QFileDialog.getSaveFileName(self,"Export tasks to CSV",str(Path.home()/"LifeOS-tasks.csv"),"CSV files (*.csv)")
        if not path:return
        try:
            with connect() as c: rows=c.execute("SELECT title,details,priority,category,due_date,recurrence,done,created_at,completed_at FROM tasks ORDER BY id").fetchall()
            with open(path,"w",newline="",encoding="utf-8-sig") as f:
                writer=csv.writer(f); writer.writerow(["Title","Details","Priority","Category","Due date","Recurrence","Completed","Created at","Completed at"])
                for row in rows: writer.writerow([row[k] for k in row.keys()])
            QMessageBox.information(self,"Export complete",f"Exported {len(rows)} tasks to:\n{path}")
        except Exception as e: QMessageBox.critical(self,"Export failed",str(e))

    def export_notes_markdown(self):
        folder=QFileDialog.getExistingDirectory(self,"Choose folder for Markdown notes",str(Path.home()))
        if not folder:return
        try:
            with connect() as c: rows=c.execute("SELECT title,body,updated_at,pinned FROM notes ORDER BY pinned DESC,title COLLATE NOCASE").fetchall()
            os.makedirs(folder,exist_ok=True)
            for index,row in enumerate(rows,1):
                safe=re.sub(r'[<>:"/\\\\|?*]+',"-",row["title"]).strip(" .-") or f"note-{index}"
                target=Path(folder)/(safe+".md")
                if target.exists(): target=Path(folder)/(safe+f"-{index}.md")
                content=f"# {row['title']}\n\n{row['body']}\n\n---\nUpdated: {row['updated_at']}\nPinned: {'Yes' if row['pinned'] else 'No'}\n"
                target.write_text(content,encoding="utf-8")
            QMessageBox.information(self,"Export complete",f"Exported {len(rows)} notes to:\n{folder}")
        except Exception as e: QMessageBox.critical(self,"Export failed",str(e))

    def get_setting(self,key,default=""):
        with connect() as c:
            row=c.execute("SELECT value FROM app_settings WHERE key=?",(key,)).fetchone()
        return row["value"] if row else default

    def set_setting(self,key,value):
        with connect() as c:
            c.execute("INSERT INTO app_settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(key,str(value)))

    def set_dark_mode(self,enabled):
        self.dark_mode=bool(enabled); self.set_setting("dark_mode","1" if enabled else "0"); self.apply_theme()

    def apply_theme(self):
        app=QApplication.instance()
        if app: app.setStyleSheet(DARK_STYLE if self.dark_mode else STYLE)

    def check_reminders(self):
        if self.get_setting("reminders_enabled","1")!="1": return
        today=date.today().isoformat()
        with connect() as c:
            due=c.execute("SELECT COUNT(*) FROM tasks WHERE done=0 AND due_date=?",(today,)).fetchone()[0]
            overdue=c.execute("SELECT COUNT(*) FROM tasks WHERE done=0 AND due_date<>'' AND due_date<?",(today,)).fetchone()[0]
        signature=f"{today}:{due}:{overdue}"
        if signature != self._reminder_signature and (due or overdue):
            self._reminder_signature=signature
            pieces=[]
            if due: pieces.append(f"{due} task(s) due today")
            if overdue: pieces.append(f"{overdue} overdue")
            if hasattr(self,"statusBar"): self.statusBar().showMessage("Deadline reminder: " + " · ".join(pieces),15000)

    def refresh_all(self):
        self.refresh_dashboard(); self.refresh_tasks(); self.refresh_notes(); self.refresh_calendar(); self.refresh_habits(); self.refresh_documents()
        if hasattr(self,"analytics_table"): self.refresh_analytics()

    def refresh_dashboard(self):
        today=date.today().isoformat()
        with connect() as c:
            opened=c.execute("SELECT COUNT(*) FROM tasks WHERE done=0").fetchone()[0]
            due=c.execute("SELECT COUNT(*) FROM tasks WHERE done=0 AND due_date=?",(today,)).fetchone()[0]
            notes=c.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
            habits=c.execute("SELECT COUNT(*) FROM habits").fetchone()[0]
            checked=c.execute("SELECT COUNT(*) FROM habit_logs WHERE log_date=?",(today,)).fetchone()[0]
            tasks=c.execute("""SELECT * FROM tasks WHERE done=0 ORDER BY CASE priority WHEN 'Urgent' THEN 0 WHEN 'High' THEN 1 WHEN 'Normal' THEN 2 ELSE 3 END, due_date LIMIT 15""").fetchall()
        self.stat_open.number.setText(str(opened)); self.stat_today.number.setText(str(due)); self.stat_notes.number.setText(str(notes)); self.stat_habits.number.setText(f"{checked}/{habits}")
        self.focus_list.clear()
        if not tasks: self.focus_list.addItem("You're all caught up. Add a task whenever something comes up.")
        for t in tasks:
            due_text=f"  ·  {t['due_date']}" if t["due_date"] else ""
            item=QListWidgetItem(f"{'⚑ ' if t['priority'] in ('Urgent','High') else '○ '}{t['title']}  [{t['category']}]{due_text}")
            item.setData(Qt.ItemDataRole.UserRole,t["id"]); self.focus_list.addItem(item)

    def refresh_tasks(self):
        if not hasattr(self,"task_table"): return
        s=self.task_search.text().strip(); filt=self.task_filter.currentText(); cat=self.category_filter.currentText()
        q="SELECT * FROM tasks WHERE (title LIKE ? OR details LIKE ? OR category LIKE ?)"; args=[f"%{s}%",f"%{s}%",f"%{s}%"]
        if filt=="Open tasks": q+=" AND done=0"
        elif filt=="Completed": q+=" AND done=1"
        elif filt=="Overdue": q+=" AND done=0 AND due_date<>'' AND due_date<?"; args.append(date.today().isoformat())
        if cat!="All categories": q+=" AND category=?"; args.append(cat)
        q+=" ORDER BY done, CASE priority WHEN 'Urgent' THEN 0 WHEN 'High' THEN 1 WHEN 'Normal' THEN 2 ELSE 3 END, due_date, id DESC"
        with connect() as c: rows=c.execute(q,args).fetchall()
        self.task_table.setRowCount(0)
        for t in rows:
            r=self.task_table.rowCount(); self.task_table.insertRow(r)
            vals=[t["title"],t["category"],t["priority"],t["due_date"] or "—",t["recurrence"] or "Never"]
            for col,v in enumerate(vals):
                it=QTableWidgetItem(str(v)); self.task_table.setItem(r,col,it)
            self.task_table.item(r,0).setData(Qt.ItemDataRole.UserRole,t["id"])
            if t["done"]: self.task_table.item(r,0).setForeground(Qt.GlobalColor.gray)
            status=QPushButton("✓ Done" if t["done"] else "Mark done"); status.setObjectName("Secondary")
            status.clicked.connect(lambda checked=False,tid=t["id"],done=t["done"]:self.toggle_task(tid,done)); self.task_table.setCellWidget(r,5,status)
            cell=QWidget(); hl=QHBoxLayout(cell); hl.setContentsMargins(2,2,2,2)
            ed=QPushButton("Edit"); ed.setObjectName("Secondary"); ed.clicked.connect(lambda checked=False,tid=t["id"]:self.edit_task(tid))
            de=QPushButton("×"); de.setObjectName("Danger"); de.clicked.connect(lambda checked=False,tid=t["id"]:self.delete_task(tid))
            hl.addWidget(ed); hl.addWidget(de); self.task_table.setCellWidget(r,6,cell)
        self.refresh_dashboard()

    def add_task(self, due_date=None):
        d=TaskDialog(self)
        if due_date:
            qd=QDate.fromString(due_date,"yyyy-MM-dd")
            if qd.isValid(): d.due.setDate(qd); d.no_due.setChecked(False)
        if d.exec()!=QDialog.DialogCode.Accepted: return
        vals=d.values()
        if not vals[0]: QMessageBox.warning(self,"Task required","Please enter a task title."); return
        with connect() as c: c.execute("INSERT INTO tasks(title,details,priority,category,due_date,recurrence) VALUES(?,?,?,?,?,?)",vals)
        self.refresh_all(); self.statusBar().showMessage("Task added.",3000)

    def edit_task(self,tid):
        with connect() as c: row=c.execute("SELECT * FROM tasks WHERE id=?",(tid,)).fetchone()
        if not row:return
        d=TaskDialog(self,row)
        if d.exec()!=QDialog.DialogCode.Accepted:return
        vals=d.values()
        if not vals[0]: QMessageBox.warning(self,"Task required","Please enter a task title."); return
        with connect() as c: c.execute("UPDATE tasks SET title=?,details=?,priority=?,category=?,due_date=?,recurrence=? WHERE id=?",(*vals,tid))
        self.refresh_all()

    def edit_task_from_row(self,row,col):
        it=self.task_table.item(row,0)
        if it:self.edit_task(it.data(Qt.ItemDataRole.UserRole))

    def toggle_task(self,tid,done):
        with connect() as c:
            t=c.execute("SELECT * FROM tasks WHERE id=?",(tid,)).fetchone()
            if not t:return
            if not done and t["recurrence"]!="Never":
                c.execute("UPDATE tasks SET done=1, completed_at=CURRENT_TIMESTAMP WHERE id=?",(tid,))
                if t["recurrence"]=="Daily": nd=date.today()+timedelta(days=1)
                elif t["recurrence"]=="Weekly": nd=date.today()+timedelta(days=7)
                else:
                    d=date.today()
                    nd=(d.replace(day=28)+timedelta(days=4)).replace(day=1)
                c.execute("INSERT INTO tasks(title,details,priority,category,due_date,recurrence) VALUES(?,?,?,?,?,?)",(t["title"],t["details"],t["priority"],t["category"],nd.isoformat(),t["recurrence"]))
            else:
                if done:
                    c.execute("UPDATE tasks SET done=0, completed_at='' WHERE id=?",(tid,))
                else:
                    c.execute("UPDATE tasks SET done=1, completed_at=CURRENT_TIMESTAMP WHERE id=?",(tid,))
        self.refresh_all()

    def delete_task(self,tid):
        if confirm(self,"Delete task","Delete this task permanently?"):
            with connect() as c:c.execute("DELETE FROM tasks WHERE id=?",(tid,))
            self.refresh_all()

    def add_note(self):
        d=NoteDialog(self)
        if d.exec()!=QDialog.DialogCode.Accepted:return
        title,body,pinned=d.values()
        if not title:QMessageBox.warning(self,"Title required","Please enter a note title.");return
        with connect() as c:c.execute("INSERT INTO notes(title,body,pinned) VALUES(?,?,?)",(title,body,pinned))
        self.refresh_notes();self.refresh_dashboard()

    def refresh_notes(self):
        if not hasattr(self,"note_list"):return
        s=self.note_search.text().strip(); old=self.current_note_id
        with connect() as c:rows=c.execute("SELECT * FROM notes WHERE title LIKE ? OR body LIKE ? ORDER BY pinned DESC,updated_at DESC,id DESC",(f"%{s}%",f"%{s}%")).fetchall()
        self.note_list.clear()
        for n in rows:
            it=QListWidgetItem(("📌  " if n["pinned"] else "")+n["title"]);it.setData(Qt.ItemDataRole.UserRole,n["id"]);self.note_list.addItem(it)
            if n["id"]==old:self.note_list.setCurrentItem(it)
        if not rows:self.current_note_id=None;self.note_title.setText("No notes yet");self.note_body.clear()

    def show_note(self,current,previous=None):
        if not current:return
        nid=current.data(Qt.ItemDataRole.UserRole);self.current_note_id=nid
        with connect() as c:n=c.execute("SELECT * FROM notes WHERE id=?",(nid,)).fetchone()
        if n:self.note_title.setText(("📌  " if n["pinned"] else "")+n["title"]);self.note_body.setPlainText(n["body"])

    def selected_note(self):
        if not self.current_note_id:return None
        with connect() as c:return c.execute("SELECT * FROM notes WHERE id=?",(self.current_note_id,)).fetchone()

    def edit_note(self):
        n=self.selected_note()
        if not n:QMessageBox.information(self,"Select a note","Choose a note first.");return
        d=NoteDialog(self,n)
        if d.exec()!=QDialog.DialogCode.Accepted:return
        title,body,pinned=d.values()
        if not title:QMessageBox.warning(self,"Title required","Please enter a note title.");return
        with connect() as c:c.execute("UPDATE notes SET title=?,body=?,pinned=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",(title,body,pinned,n["id"]))
        self.refresh_notes();self.refresh_dashboard()

    def toggle_pin(self):
        n=self.selected_note()
        if not n:QMessageBox.information(self,"Select a note","Choose a note first.");return
        with connect() as c:c.execute("UPDATE notes SET pinned=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",(0 if n["pinned"] else 1,n["id"]))
        self.refresh_notes()

    def delete_note(self):
        n=self.selected_note()
        if not n:QMessageBox.information(self,"Select a note","Choose a note first.");return
        if confirm(self,"Delete note","Delete this note permanently?"):
            with connect() as c:c.execute("DELETE FROM notes WHERE id=?",(n["id"],))
            self.current_note_id=None;self.refresh_notes();self.refresh_dashboard()

    def refresh_calendar(self):
        if not hasattr(self,"calendar_tasks"):return
        qd=self.calendar.selectedDate(); day=qd.toString("yyyy-MM-dd"); self.calendar_date_label.setText("Tasks for "+qd.toString("dddd, d MMMM yyyy"))
        with connect() as c:rows=c.execute("SELECT * FROM tasks WHERE due_date=? ORDER BY done,priority",(day,)).fetchall()
        self.calendar_tasks.clear()
        if not rows:self.calendar_tasks.addItem("No tasks scheduled for this date.")
        for t in rows:
            mark="✓" if t["done"] else "○"
            it=QListWidgetItem(f"{mark} {t['title']}  ·  {t['priority']}");it.setData(Qt.ItemDataRole.UserRole,t["id"]);self.calendar_tasks.addItem(it)

    def add_task_for_calendar_date(self):
        self.add_task(self.calendar.selectedDate().toString("yyyy-MM-dd"))

    def add_habit(self):
        d=HabitDialog(self)
        if d.exec()!=QDialog.DialogCode.Accepted:return
        name=d.name.text().strip();desc=d.description.text().strip()
        if not name:QMessageBox.warning(self,"Habit required","Enter a habit name.");return
        try:
            with connect() as c:c.execute("INSERT INTO habits(name,description) VALUES(?,?)",(name,desc))
        except Exception:QMessageBox.warning(self,"Habit exists","A habit with that name already exists.");return
        self.refresh_habits();self.refresh_dashboard()

    def refresh_habits(self):
        if not hasattr(self,"habit_table"):return
        today=date.today().isoformat(); start=(date.today()-timedelta(days=6)).isoformat()
        with connect() as c:
            rows=c.execute("SELECT * FROM habits ORDER BY name COLLATE NOCASE").fetchall()
            logs=c.execute("SELECT habit_id,log_date FROM habit_logs WHERE log_date>=? AND log_date<=?",(start,today)).fetchall()
        logset={(r["habit_id"],r["log_date"]) for r in logs};self.habit_table.setRowCount(0)
        for h in rows:
            r=self.habit_table.rowCount();self.habit_table.insertRow(r)
            self.habit_table.setItem(r,0,QTableWidgetItem(h["name"]));self.habit_table.setItem(r,1,QTableWidgetItem(h["description"]))
            self.habit_table.item(r,0).setData(Qt.ItemDataRole.UserRole,h["id"])
            cb=QCheckBox("Done today");cb.setChecked((h["id"],today) in logset);cb.stateChanged.connect(lambda state,hid=h["id"]:self.set_habit_log(hid,state))
            self.habit_table.setCellWidget(r,2,cb)
            count=sum(1 for d in range(7) if (h["id"],(date.today()-timedelta(days=d)).isoformat()) in logset)
            self.habit_table.setItem(r,3,QTableWidgetItem(f"{count}/7"))
            rem=QPushButton("Remove"); rem.setObjectName("Danger")
            rem.clicked.connect(lambda checked=False,hid=h["id"]:self.delete_habit(hid))
            self.habit_table.setCellWidget(r,4,rem)
        self.refresh_dashboard()

    def set_habit_log(self,hid,state):
        today=date.today().isoformat()
        with connect() as c:
            if state:
                c.execute("INSERT OR IGNORE INTO habit_logs(habit_id,log_date) VALUES(?,?)",(hid,today))
            else:c.execute("DELETE FROM habit_logs WHERE habit_id=? AND log_date=?",(hid,today))
        self.refresh_dashboard()
        # Refresh the count without recreating the checkbox currently being changed.
        with connect() as c:
            logs=c.execute("SELECT log_date FROM habit_logs WHERE habit_id=? AND log_date>=?",(hid,(date.today()-timedelta(days=6)).isoformat())).fetchall()
        row=next((r for r in range(self.habit_table.rowCount()) if self.habit_table.item(r,0).data(Qt.ItemDataRole.UserRole)==hid),None)
        if row is not None:self.habit_table.setItem(row,3,QTableWidgetItem(f"{len(logs)}/7"))

    def delete_habit(self,hid):
        if confirm(self,"Remove habit","Remove this habit and its check-in history?"):
            with connect() as c:c.execute("DELETE FROM habits WHERE id=?",(hid,))
            self.refresh_habits();self.refresh_dashboard()

    def refresh_documents(self):
        if not hasattr(self,"doc_table"):return
        s=self.doc_search.text().strip()
        with connect() as c:rows=c.execute("SELECT * FROM documents WHERE label LIKE ? OR path LIKE ? ORDER BY label COLLATE NOCASE",(f"%{s}%",f"%{s}%")).fetchall()
        self.doc_table.setRowCount(0)
        for d in rows:
            r=self.doc_table.rowCount();self.doc_table.insertRow(r);self.doc_table.setItem(r,0,QTableWidgetItem(d["label"]));self.doc_table.setItem(r,1,QTableWidgetItem(d["path"]))
            cell=QWidget();hl=QHBoxLayout(cell);hl.setContentsMargins(2,2,2,2)
            op=QPushButton("Open");op.clicked.connect(lambda checked=False,path=d["path"]:self.open_path(path))
            rm=QPushButton("Remove");rm.setObjectName("Secondary");rm.clicked.connect(lambda checked=False,did=d["id"]:self.remove_document(did))
            hl.addWidget(op);hl.addWidget(rm);self.doc_table.setCellWidget(r,2,cell)

    def add_document(self):
        path,_=QFileDialog.getOpenFileName(self,"Choose a file")
        if not path:path=QFileDialog.getExistingDirectory(self,"Or choose a folder")
        if not path:return
        p=Path(path)
        with connect() as c:
            if c.execute("SELECT id FROM documents WHERE path=?",(str(p),)).fetchone():
                QMessageBox.information(self,"Already added","That path is already in the document hub.");return
            c.execute("INSERT INTO documents(label,path) VALUES(?,?)",(p.name or str(p),str(p)))
        self.refresh_documents()

    def open_path(self,path):
        if not Path(path).exists():QMessageBox.warning(self,"Path not found",f"This path no longer exists:\n{path}");return
        try:
            if os.name=="nt":os.startfile(path)
            elif sys.platform=="darwin":subprocess.Popen(["open",path])
            else:subprocess.Popen(["xdg-open",path])
        except Exception as e:QMessageBox.warning(self,"Could not open",str(e))

    def remove_document(self,did):
        if confirm(self,"Remove shortcut","Remove shortcut only? The original file will not be deleted."):
            with connect() as c:c.execute("DELETE FROM documents WHERE id=?",(did,))
            self.refresh_documents()

    def set_focus_length(self,value):
        if self.timer_running:return
        self.focus_seconds=value*60;self.remaining=self.focus_seconds;self.update_timer_display()

    def start_pause_timer(self):
        if self.timer_running:
            self.timer.stop();self.timer_running=False;self.timer_start.setText("Resume focus")
        else:
            self.timer.start();self.timer_running=True;self.timer_start.setText("Pause")
    def tick(self):
        if self.remaining>0:self.remaining-=1;self.update_timer_display()
        if self.remaining<=0:
            self.timer.stop();self.timer_running=False;self.timer_start.setText("Start focus")
            QApplication.beep();QMessageBox.information(self,"Focus session complete","Well done. Your focus session is complete.")
    def reset_timer(self):
        self.timer.stop();self.timer_running=False;self.remaining=self.focus_seconds;self.timer_start.setText("Start focus");self.update_timer_display()
    def update_timer_display(self):
        m,s=divmod(max(0,self.remaining),60);self.timer_label.setText(f"{m:02d}:{s:02d}")
        self.timer_progress.setRange(0,max(1,self.focus_seconds));self.timer_progress.setValue(max(0,self.remaining))

    def backup_db(self):
        if not DB_PATH.exists():QMessageBox.information(self,"No database","The database has not been created yet.");return
        default=str(Path.home()/f"JASS-LifeOS-backup-{datetime.now():%Y%m%d-%H%M%S}.sqlite")
        path,_=QFileDialog.getSaveFileName(self,"Save LifeOS backup",default,"SQLite database (*.sqlite *.db)")
        if not path:return
        try:
            # SQLite backup API produces a consistent snapshot, even if the app is in use.
            with connect() as source, __import__("sqlite3").connect(path) as dest:source.backup(dest)
            QMessageBox.information(self,"Backup complete",f"Backup saved to:\n{path}")
        except Exception as e:QMessageBox.critical(self,"Backup failed",str(e))

    def restore_db(self):
        path,_=QFileDialog.getOpenFileName(self,"Choose LifeOS backup","","SQLite database (*.sqlite *.db)")
        if not path:return
        if not confirm(self,"Restore backup","Restoring replaces your current LifeOS data. A safety backup will be created first. Continue?"):return
        try:
            safety=APP_DIR/f"before-restore-{datetime.now():%Y%m%d-%H%M%S}.sqlite"
            with connect() as source,__import__("sqlite3").connect(str(safety)) as dest:source.backup(dest)
            with __import__("sqlite3").connect(path) as source,connect() as dest:source.backup(dest)
            initialize();self.refresh_all()
            QMessageBox.information(self,"Restore complete",f"Data restored. Safety copy saved at:\n{safety}")
        except Exception as e:QMessageBox.critical(self,"Restore failed",str(e))

    def open_data_folder(self):
        APP_DIR.mkdir(parents=True,exist_ok=True);self.open_path(str(APP_DIR))

    def global_search_run(self):
        s=self.global_search.text().strip()
        if not s:return
        self.task_search.setText(s); self.note_search.setText(s); self.doc_search.setText(s)
        with connect() as c:
            nt=c.execute("SELECT COUNT(*) FROM notes WHERE title LIKE ? OR body LIKE ?",(f"%{s}%",f"%{s}%")).fetchone()[0]
            tt=c.execute("SELECT COUNT(*) FROM tasks WHERE title LIKE ? OR details LIKE ? OR category LIKE ?",(f"%{s}%",f"%{s}%",f"%{s}%")).fetchone()[0]
            nd=c.execute("SELECT COUNT(*) FROM documents WHERE label LIKE ? OR path LIKE ?",(f"%{s}%",f"%{s}%")).fetchone()[0]
        QMessageBox.information(self,"Search results",f"Search: {s}\n\nMatching tasks: {tt}\nMatching notes: {nt}\nMatching document shortcuts: {nd}")
        self.navigate(1 if tt else 2 if nt else 5 if nd else 1)

def main():
    initialize()
    app=QApplication(sys.argv);app.setApplicationName("JASS LifeOS");app.setOrganizationName("JASS Digital")
    app.setStyle("Fusion");app.setStyleSheet(STYLE)
    w=LifeOS();w.show();sys.exit(app.exec())

if __name__=="__main__":main()

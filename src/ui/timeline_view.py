import json
import tkinter as tk
from tkinter import ttk
from datetime import date, datetime, timedelta
from calendar import monthrange

from tkcalendar import Calendar

from src.db.repository import Repository


class TimelineView(ttk.Frame):
    def __init__(self, parent, repository: Repository, on_date_select=None, **kwargs):
        super().__init__(parent, **kwargs)
        self._repo = repository
        self._on_date_select = on_date_select
        self._current_date = date.today()

        self._build_ui()
        self._refresh_preview()

    def _build_ui(self):
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # Left: calendar panel
        cal_frame = ttk.Frame(self)
        cal_frame.grid(row=0, column=0, sticky="ns", padx=(0, 4))

        self._calendar = Calendar(
            cal_frame,
            selectmode="day",
            year=self._current_date.year,
            month=self._current_date.month,
            day=self._current_date.day,
            date_pattern="yyyy-mm-dd",
            font=("Sans", 9),
        )
        self._calendar.pack(fill=tk.X, padx=4, pady=(4, 2))
        self._calendar.bind("<<CalendarSelected>>", self._on_calendar_select)

        nav_frame = ttk.Frame(cal_frame)
        nav_frame.pack(fill=tk.X, padx=4, pady=(0, 4))

        ttk.Button(nav_frame, text="◀", width=3, command=self._prev_day).pack(side=tk.LEFT)
        ttk.Button(nav_frame, text="Today", command=self._goto_today).pack(side=tk.LEFT, padx=4)
        ttk.Button(nav_frame, text="▶", width=3, command=self._next_day).pack(side=tk.LEFT)

        self._cal_date_label = ttk.Label(cal_frame, text="", font=("Sans", 9, "bold"))
        self._cal_date_label.pack(pady=(0, 4))
        self._update_date_label()

        # Right: daily preview tree
        tree_frame = ttk.LabelFrame(self, text="Daily Preview")
        tree_frame.grid(row=0, column=1, sticky="nsew")
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        self._tree = ttk.Treeview(tree_frame, columns=("time", "text"), show="tree", selectmode="browse")
        self._tree.heading("#0", text="Logs")
        self._tree.column("#0", width=300, minwidth=150)

        scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self._tree.yview)
        self._tree.configure(yscrollcommand=scroll.set)

        self._tree.grid(row=0, column=0, sticky="nsew", padx=(4, 0), pady=4)
        scroll.grid(row=0, column=1, sticky="ns", pady=4)

        self._empty_preview = ttk.Label(
            self, text="No entries for this day", foreground="gray"
        )

    def _on_calendar_select(self, event=None):
        selected = self._calendar.get_date()
        try:
            self._current_date = date.fromisoformat(selected)
        except (ValueError, TypeError):
            return
        self._update_date_label()
        self._refresh_preview()
        if self._on_date_select:
            self._on_date_select(self._current_date)

    def _prev_day(self):
        self._current_date -= timedelta(days=1)
        self._calendar.selection_set(self._current_date)
        self._update_date_label()
        self._refresh_preview()
        if self._on_date_select:
            self._on_date_select(self._current_date)

    def _next_day(self):
        self._current_date += timedelta(days=1)
        self._calendar.selection_set(self._current_date)
        self._update_date_label()
        self._refresh_preview()
        if self._on_date_select:
            self._on_date_select(self._current_date)

    def _goto_today(self):
        self._current_date = date.today()
        self._calendar.selection_set(self._current_date)
        self._update_date_label()
        self._refresh_preview()
        if self._on_date_select:
            self._on_date_select(self._current_date)

    def _update_date_label(self):
        self._cal_date_label.config(text=self._current_date.strftime("%A, %B %d, %Y"))

    def _refresh_preview(self):
        for item in self._tree.get_children():
            self._tree.delete(item)

        logs = self._repo.get_logs_for_date(self._current_date)
        if not logs:
            self._empty_preview.grid(row=0, column=1, sticky="", padx=4)
            return

        self._empty_preview.grid_forget()

        for log in logs:
            ts = log["timestamp"]
            try:
                time_str = datetime.fromisoformat(ts).strftime("%H:%M")
            except (ValueError, TypeError):
                time_str = ts[-8:-3] if ts and len(ts) > 8 else ""

            text = log["text"]
            tags = json.loads(log.get("tags", "[]"))
            tag_str = f" [{', '.join(tags)}]" if tags else ""
            display = f"{time_str} — {text}{tag_str}"
            self._tree.insert("", tk.END, text=display)

    def refresh(self, target_date: date | None = None):
        if target_date:
            self._current_date = target_date
            self._calendar.selection_set(target_date)
            self._update_date_label()
        self._refresh_preview()

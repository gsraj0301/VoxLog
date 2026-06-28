import json
import tkinter as tk
from tkinter import ttk
from datetime import date, datetime

from src.db.repository import Repository
from src.ui.tag_dialog import TagDialog


class LogList(ttk.Frame):
    def __init__(self, parent, repository: Repository, **kwargs):
        super().__init__(parent, **kwargs)
        self._repo = repository
        self._current_logs: list[dict] = []
        self._tag_filter: str | None = None

        self._build_ui()

    def _build_ui(self):
        top = ttk.Frame(self)
        top.pack(fill=tk.X, padx=4, pady=(4, 2))

        ttk.Label(top, text="Search:").pack(side=tk.LEFT, padx=(0, 4))
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", self._on_search_change)
        self._search_entry = ttk.Entry(top, textvariable=self._search_var)
        self._search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self._tag_combo = ttk.Combobox(top, state="readonly", width=12)
        self._tag_combo.pack(side=tk.LEFT, padx=(4, 4))
        self._tag_combo.bind("<<ComboboxSelected>>", self._on_tag_filter)
        self._tag_combo.set("All tags")

        ttk.Button(top, text="✕", width=3, command=self._clear_tag_filter).pack(side=tk.LEFT)

        columns = ("time", "text", "tags")
        self._tree = ttk.Treeview(self, columns=columns, show="headings", selectmode="browse")

        self._tree.heading("time", text="Time")
        self._tree.heading("text", text="Log Entry")
        self._tree.heading("tags", text="Tags")

        self._tree.column("time", width=80, minwidth=80)
        self._tree.column("text", width=400, minwidth=150)
        self._tree.column("tags", width=150, minwidth=80)

        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self._tree.yview)
        self._tree.configure(yscrollcommand=scrollbar.set)

        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._tree.bind("<Button-3>", self._show_context_menu)
        self._tree.bind("<Double-1>", self._on_double_click)
        self._tree.bind("<Destroy>", self._cleanup)

        self._context_menu = tk.Menu(self, tearoff=0)
        self._context_menu.add_command(label="Edit Text", command=self._edit_selected_text)
        self._context_menu.add_command(label="Edit Tags", command=self._edit_selected_tags)
        self._context_menu.add_separator()
        self._context_menu.add_command(label="Delete", command=self._delete_selected)
        self._context_menu.add_command(label="Copy Text", command=self._copy_selected_text)

        self._empty_label = ttk.Label(
            self, text="No log entries yet. Press Record to start logging.",
            foreground="gray", font=("Sans", 11),
        )

    def refresh(self, target_date: date | None = None):
        if target_date:
            self._current_logs = self._repo.get_logs_for_date(target_date)
        else:
            self._current_logs = self._repo.get_logs()

        search = self._search_var.get().strip()
        if search:
            self._current_logs = self._repo.get_logs(search=search)

        if self._tag_filter:
            self._current_logs = [
                log for log in self._current_logs
                if self._tag_filter in json.loads(log["tags"])
            ]

        self._refresh_tags()
        self._populate_tree()

    def _refresh_tags(self):
        all_tags = self._repo.get_all_tags()
        values = ["All tags"] + all_tags
        self._tag_combo["values"] = values

    def _populate_tree(self):
        for item in self._tree.get_children():
            self._tree.delete(item)

        if not self._current_logs:
            self._empty_label.pack(expand=True)
            return

        self._empty_label.pack_forget()

        for log in self._current_logs:
            ts = log["timestamp"]
            try:
                time_str = datetime.fromisoformat(ts).strftime("%H:%M")
            except (ValueError, TypeError):
                time_str = ts[-8:-3] if ts and len(ts) > 8 else ts or ""

            text = log["text"]
            tags = ", ".join(json.loads(log.get("tags", "[]"))) if log.get("tags") else ""

            self._tree.insert("", tk.END, iid=str(log["id"]), values=(time_str, text, tags))

    def _on_search_change(self, *_):
        self.refresh()

    def _on_tag_filter(self, event=None):
        selected = self._tag_combo.get()
        if selected and selected != "All tags":
            self._tag_filter = selected
        else:
            self._tag_filter = None
        self.refresh()

    def _clear_tag_filter(self):
        self._tag_combo.set("All tags")
        self._tag_filter = None
        self.refresh()

    def _show_context_menu(self, event):
        row_id = self._tree.identify_row(event.y)
        if row_id:
            self._tree.selection_set(row_id)
            self._context_menu.post(event.x_root, event.y_root)

    def _on_double_click(self, event):
        self._edit_selected_text()

    def _get_selected_log_id(self) -> int | None:
        sel = self._tree.selection()
        if not sel:
            return None
        return int(sel[0])

    def _edit_selected_text(self):
        log_id = self._get_selected_log_id()
        if log_id is None:
            return
        log = self._repo.get_log(log_id)
        if not log:
            return

        dialog = tk.Toplevel(self.winfo_toplevel())
        dialog.title("Edit Log Entry")
        dialog.geometry("500x300")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        ttk.Label(dialog, text="Edit log text:").pack(anchor=tk.W, padx=12, pady=(12, 4))
        text_w = tk.Text(dialog, wrap=tk.WORD, font=("Sans", 11))
        text_w.pack(fill=tk.BOTH, expand=True, padx=12, pady=4)
        text_w.insert("1.0", log["text"])
        text_w.focus_set()

        btn_f = ttk.Frame(dialog)
        btn_f.pack(fill=tk.X, padx=12, pady=(4, 12))

        def save():
            new_text = text_w.get("1.0", tk.END).strip()
            if new_text:
                self._repo.update_log(log_id, text=new_text)
            dialog.destroy()
            self.refresh()

        def cancel():
            dialog.destroy()

        ttk.Button(btn_f, text="Cancel", command=cancel).pack(side=tk.RIGHT, padx=(4, 0))
        ttk.Button(btn_f, text="Save", command=save).pack(side=tk.RIGHT)

    def _edit_selected_tags(self):
        log_id = self._get_selected_log_id()
        if log_id is None:
            return
        log = self._repo.get_log(log_id)
        if not log:
            return

        current_tags = json.loads(log.get("tags", "[]"))
        all_tags = self._repo.get_all_tags()

        def on_tags_submit(tags):
            self._repo.update_log(log_id, tags=tags)
            self.refresh()

        TagDialog(self, all_tags, current_tags, on_submit=on_tags_submit)

    def _delete_selected(self):
        log_id = self._get_selected_log_id()
        if log_id is None:
            return

        result = tk.messagebox.askyesno(
            "Delete Log",
            "Are you sure you want to delete this log entry?",
            icon="warning",
        )
        if result:
            self._repo.delete_log(log_id)
            self.refresh()

    def _copy_selected_text(self):
        log_id = self._get_selected_log_id()
        if log_id is None:
            return
        log = self._repo.get_log(log_id)
        if log:
            self.clipboard_clear()
            self.clipboard_append(log["text"])

    def _cleanup(self, event=None):
        if hasattr(self, "_context_menu"):
            try:
                self._context_menu.unpost()
            except tk.TclError:
                pass

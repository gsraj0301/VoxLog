import tkinter as tk
from tkinter import ttk
from collections.abc import Callable


class TagDialog(tk.Toplevel):
    def __init__(
        self,
        parent: tk.Widget,
        all_tags: list[str],
        current_tags: list[str] | None = None,
        on_submit: Callable[[list[str]], None] | None = None,
    ):
        super().__init__(parent)
        self.title("Edit Tags")
        self.geometry("400x250")
        self.transient(parent.winfo_toplevel())
        self.grab_set()

        self._all_tags = sorted(all_tags)
        self._current_tags = list(current_tags) if current_tags else []
        self._on_submit = on_submit
        self._selected_index = 0

        self._build_ui()
        self._render_tags()

        ttk.Button(self, text="Done", command=self._submit).pack(pady=(0, 8))
        self.protocol("WM_DELETE_WINDOW", self._cancel)

    def _build_ui(self):
        ttk.Label(self, text="Add tags (comma separated, type to autocomplete):").pack(
            anchor=tk.W, padx=12, pady=(12, 2)
        )

        entry_frame = ttk.Frame(self)
        entry_frame.pack(fill=tk.X, padx=12, pady=(0, 2))

        self._entry_var = tk.StringVar()
        self._entry_var.trace_add("write", self._on_entry_change)
        self._entry = ttk.Entry(entry_frame, textvariable=self._entry_var)
        self._entry.pack(fill=tk.X)
        self._entry.bind("<Return>", self._insert_selected)
        self._entry.bind("<Tab>", self._insert_selected)
        self._entry.bind("<Down>", self._move_down)
        self._entry.bind("<Up>", self._move_up)
        self._entry.focus_set()

        self._listbox = tk.Listbox(self, height=4)
        self._listbox.bind("<ButtonRelease-1>", self._on_listbox_click)
        self._listbox.bind("<Return>", self._insert_selected)

        self._tags_frame = ttk.Frame(self)
        self._tags_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(4, 4))

        self._tags_label = ttk.Label(self._tags_frame, text="", wraplength=360)
        self._tags_label.pack(anchor=tk.W)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=12, pady=(4, 8))

        ttk.Button(btn_frame, text="Cancel", command=self._cancel).pack(side=tk.RIGHT, padx=(4, 0))

    def _on_entry_change(self, *_):
        typed = self._entry_var.get().strip().lower()
        if not typed:
            self._listbox.place_forget()
            return

        matches = [t for t in self._all_tags if typed in t.lower() and t not in self._current_tags]
        if not matches:
            self._listbox.place_forget()
            return

        self._listbox.delete(0, tk.END)
        for m in matches:
            self._listbox.insert(tk.END, m)
        self._selected_index = 0
        self._listbox.selection_clear(0, tk.END)
        self._listbox.selection_set(0)
        self._listbox.place(x=self._entry.winfo_x(), y=self._entry.winfo_y() + self._entry.winfo_height() + 2, width=self._entry.winfo_width())

    def _insert_selected(self, event=None):
        if self._listbox.size() == 0:
            return

        sel = self._listbox.curselection()
        if not sel:
            sel = (self._selected_index,)
        tag = self._listbox.get(sel[0])
        if tag not in self._current_tags:
            self._current_tags.append(tag)
            self._render_tags()
        self._entry_var.set("")
        self._listbox.place_forget()
        self._entry.focus_set()

    def _on_listbox_click(self, event):
        self._insert_selected()

    def _move_down(self, event):
        if self._listbox.size() == 0:
            return
        self._selected_index = min(self._selected_index + 1, self._listbox.size() - 1)
        self._listbox.selection_clear(0, tk.END)
        self._listbox.selection_set(self._selected_index)
        self._listbox.see(self._selected_index)

    def _move_up(self, event):
        if self._listbox.size() == 0:
            return
        self._selected_index = max(self._selected_index - 1, 0)
        self._listbox.selection_clear(0, tk.END)
        self._listbox.selection_set(self._selected_index)
        self._listbox.see(self._selected_index)

    def _render_tags(self):
        if self._current_tags:
            self._tags_label.config(text="Tags: " + ", ".join(self._current_tags))
        else:
            self._tags_label.config(text="No tags added yet")

    def _submit(self):
        if self._on_submit:
            self._on_submit(list(dict.fromkeys(self._current_tags)))
        self.destroy()

    def _cancel(self):
        self.destroy()

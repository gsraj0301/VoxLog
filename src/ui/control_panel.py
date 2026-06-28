import tkinter as tk
from tkinter import ttk


class ControlPanel(ttk.Frame):
    def __init__(self, parent, on_record_cb=None, on_stop_cb=None, on_save_cb=None, **kwargs):
        super().__init__(parent, **kwargs)
        self._on_record_cb = on_record_cb
        self._on_stop_cb = on_stop_cb
        self._on_save_cb = on_save_cb

        self._recording = False
        self._build_ui()

    def _build_ui(self):
        # Top row: buttons + status
        top = ttk.Frame(self)
        top.pack(fill=tk.X, padx=8, pady=(8, 2))

        self._record_btn = ttk.Button(
            top, text="● Record", command=self._on_record, width=12
        )
        self._record_btn.pack(side=tk.LEFT, padx=(0, 4))

        self._stop_btn = ttk.Button(
            top, text="■ Stop", command=self._on_stop, state=tk.DISABLED, width=12
        )
        self._stop_btn.pack(side=tk.LEFT, padx=(0, 8))

        self._status_label = ttk.Label(top, text="Idle", foreground="gray")
        self._status_label.pack(side=tk.LEFT)

        # Live transcript area
        self._transcript = tk.Text(self, height=4, wrap=tk.WORD, state=tk.DISABLED)
        self._transcript.pack(fill=tk.X, padx=8, pady=(2, 8))

    def _on_record(self):
        self._recording = True
        self._record_btn.config(state=tk.DISABLED)
        self._stop_btn.config(state=tk.NORMAL)
        self.set_status("Recording...", "red")
        self._clear_transcript()
        if self._on_record_cb:
            self._on_record_cb()

    def _on_stop(self):
        self._recording = False
        self._record_btn.config(state=tk.NORMAL)
        self._stop_btn.config(state=tk.DISABLED)
        self.set_status("Processing...", "orange")
        if self._on_stop_cb:
            self._on_stop_cb()

    def set_status(self, text: str, color: str = "gray"):
        self._status_label.config(text=text, foreground=color)

    def update_live_transcript(self, text: str):
        self._transcript.config(state=tk.NORMAL)
        self._transcript.delete("1.0", tk.END)
        self._transcript.insert("1.0", text)
        self._transcript.config(state=tk.DISABLED)

    def _clear_transcript(self):
        self._transcript.config(state=tk.NORMAL)
        self._transcript.delete("1.0", tk.END)
        self._transcript.config(state=tk.DISABLED)

    def show_review_dialog(self, transcript: str):
        dialog = tk.Toplevel(self.winfo_toplevel())
        dialog.title("Review Log Entry")
        dialog.geometry("600x400")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        ttk.Label(dialog, text="Edit your log entry before saving:").pack(
            anchor=tk.W, padx=12, pady=(12, 4)
        )

        text_widget = tk.Text(dialog, wrap=tk.WORD, font=("Sans", 12))
        text_widget.pack(fill=tk.BOTH, expand=True, padx=12, pady=4)
        text_widget.insert("1.0", transcript)
        text_widget.focus_set()

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill=tk.X, padx=12, pady=(4, 12))

        def on_discard():
            dialog.destroy()
            self.set_status("Idle", "gray")

        def on_save():
            edited = text_widget.get("1.0", tk.END).strip()
            dialog.destroy()
            self.set_status("Idle", "gray")
            if edited and self._on_save_cb:
                self._on_save_cb(edited)

        ttk.Button(btn_frame, text="Discard", command=on_discard).pack(
            side=tk.RIGHT, padx=(4, 0)
        )
        save_btn = ttk.Button(btn_frame, text="✓ Save", command=on_save)
        save_btn.pack(side=tk.RIGHT)

        dialog.protocol("WM_DELETE_WINDOW", on_discard)
        self.wait_window(dialog)

    @property
    def is_recording(self) -> bool:
        return self._recording

import tkinter as tk
from tkinter import ttk
from datetime import date

from src.audio.recorder import AudioRecorder
from src.db.repository import Repository
from src.stt.vosk_engine import VoskEngine
from src.ui.control_panel import ControlPanel
from src.ui.log_list import LogList
from src.ui.timeline_view import TimelineView


class MainWindow(tk.Tk):
    def __init__(self, repository: Repository, vosk_engine: VoskEngine):
        super().__init__()
        self._repo = repository
        self._recorder = AudioRecorder(vosk_engine)
        self._accumulated_text: list[str] = []

        self.title("voxlog — Voice Logger")
        self.geometry("1200x800")
        self._center_window()

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _center_window(self):
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"+{x}+{y}")

    def _build_ui(self):
        # Control panel at top
        self._control_panel = ControlPanel(
            self,
            on_record_cb=self._start_recording,
            on_stop_cb=self._stop_recording,
            on_save_cb=self._on_save,
        )
        self._control_panel.pack(fill=tk.X)

        # Main area: Timeline (left) + LogList (right)
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self._timeline = TimelineView(
            paned,
            self._repo,
            on_date_select=self._on_date_select,
        )
        paned.add(self._timeline, weight=1)

        self._log_list = LogList(paned, self._repo)
        paned.add(self._log_list, weight=2)

        # Initial load
        self._timeline.refresh()
        self._log_list.refresh()

    def _start_recording(self):
        self._accumulated_text = []
        self._recorder.start(
            on_partial=self._on_partial_cb,
            on_final=self._on_final_cb,
        )

    def _on_partial_cb(self, text: str):
        self.after(0, self._control_panel.update_live_transcript, text)

    def _on_final_cb(self, text: str):
        def _update():
            self._accumulated_text.append(text)
            full = " ".join(self._accumulated_text)
            self._control_panel.update_live_transcript(full)

        self.after(0, _update)

    def _stop_recording(self):
        final = self._recorder.stop()
        if final:
            self._accumulated_text.append(final)

        full = " ".join(self._accumulated_text)
        if full:
            self._control_panel.show_review_dialog(full)
        else:
            self._control_panel.set_status("Idle", "gray")

    def _on_save(self, text: str):
        self._repo.insert_log(text)
        self._timeline.refresh()
        self._log_list.refresh()

    def _on_date_select(self, selected_date: date):
        self._log_list.refresh(target_date=selected_date)

    def _on_close(self):
        if self._recorder.is_recording:
            self._recorder.stop()
        self._repo.close()
        self.destroy()

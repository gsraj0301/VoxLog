# voxlog — Implementation Specification

This document tracks all implementation tasks. Each task is implemented one at a time, and we wait for user approval before proceeding to the next.

---

## Task 1 — Project Scaffolding

**Files:** `config.py`, `__init__.py` files, `requirements.txt`, `scripts/download_model.sh`, `.gitignore`

**Description:** Set up the project directory structure, define global configuration paths and constants, list Python dependencies, provide a download script for the Vosk model, and ignore generated files.

**Dependencies:** None

**Acceptance Criteria:**
- All directories exist under `voxlog/`
- `config.py` exports `ROOT`, `DATA_DIR`, `MODEL_DIR`, `DB_PATH`, `SAMPLE_RATE`, `BLOCK_SIZE`, `PARTIAL_INTERVAL`
- `requirements.txt` lists `vosk`, `sounddevice`, `numpy`, `tkcalendar`
- `download_model.sh` downloads and extracts `vosk-model-en-us-0.22` to `data/`
- `.gitignore` ignores `data/`, `*.db`, `__pycache__`, `.venv`

---

## Task 2 — Database Layer

**Files:** `db/schema.sql`, `db/repository.py`

**Description:** Create the SQLite schema for storing logs and tags. Implement a repository class with all CRUD operations: insert, get, update, delete logs, query by date range and tag filter, get logs grouped by date.

**Dependencies:** Task 1 (config.py)

**Acceptance Criteria:**
- `schema.sql` contains DDL for `logs` table with columns: `id`, `timestamp`, `text`, `duration_ms`, `tags`
- `logs.tags` stored as JSON text array `["tag1","tag2"]`
- Indexes on `timestamp` and `text`
- `Repository` class provides: `init_db()`, `insert_log()`, `get_log()`, `get_logs()`, `update_log()`, `delete_log()`, `get_all_tags()`, `get_logs_grouped_by_date()`

---

## Task 3 — STT Engine

**Files:** `stt/vosk_engine.py`

**Description:** Wrap the Vosk offline speech recognition model. Provide methods to load the model, feed audio frames, retrieve partial and final transcriptions, and reset between sessions.

**Dependencies:** Task 1 (config.py for MODEL_PATH, SAMPLE_RATE)

**Acceptance Criteria:**
- `VoskEngine.__init__()` loads model from disk
- `accept_waveform(data: bytes)` feeds audio, returns final text or None
- `partial_result()` returns interim transcription string
- `final_result()` forces final transcription on stop
- `reset()` clears recognizer state for new session
- Thread-safe usage from single worker thread

---

## Task 4 — Audio Recorder

**Files:** `audio/recorder.py`, `audio/device.py`

**Description:** Capture audio from default microphone using sounddevice. Run capture and recognition in background threads, emitting final and partial transcriptions to the main thread via callbacks.

**Dependencies:** Task 1 (config.py), Task 3 (VoskEngine)

**Acceptance Criteria:**
- `AudioDeviceManager` enumerates available input devices
- `AudioRecorder.start(callback_final, callback_partial)` opens stream, starts producer + worker threads
- `AudioRecorder.stop()` gracefully stops stream, flushes final result
- Live partial text delivered to UI via callback_partial at ~200ms intervals
- Final text delivered to UI via callback_final on stop
- Threading uses `queue.Queue` for audio + `root.after()` for UI callbacks

---

## Task 5 — Control Panel UI

**Files:** `ui/control_panel.py`

**Description:** Build the recording control panel with Record/Stop buttons, status indicator, live transcript preview, and the review/edit dialog that appears after recording stops.

**Dependencies:** Task 4 (AudioRecorder interface), Task 2 (Repository for saving reviewed logs)

**Acceptance Criteria:**
- Red Record button starts recording (disabled while recording)
- Stop button stops recording (only enabled during recording)
- Status label shows: "Idle", "Recording...", "Processing..."
- Live transcript text widget updates in real time with partial results
- On stop: review dialog pops up with final transcript in an editable text widget
- Review dialog has [Save] and [Discard] buttons
- Save writes to DB via Repository, Discard discards the transcript

---

## Task 6 — Tag Dialog

**Files:** `ui/tag_dialog.py`

**Description:** A dialog for editing tags on a log entry with autocomplete from existing tags in the database.

**Dependencies:** Task 2 (Repository for get_all_tags())

**Acceptance Criteria:**
- Dialog opened from log list context menu or review dialog
- Comma-separated tag input with autocomplete dropdown
- Suggests existing tags as user types
- Returns list of deduplicated tags on submit
- Cancellable with Esc button

---

## Task 7 — Log List

**Files:** `ui/log_list.py`

**Description:** A searchable, filterable treeview listing all log entries with time, text preview, and tags columns.

**Dependencies:** Task 2 (Repository)

**Acceptance Criteria:**
- `ttk.Treeview` with columns: Time, Text, Tags
- Search bar filters entries in real time as user types
- Right-click context menu: Edit (opens text edit), Edit Tags (opens TagDialog), Delete, Copy Text
- Double-click opens inline text edit
- Refresh method to reload data
- Optional tag filter bar alongside search
- Shows empty state message when no logs exist

---

## Task 8 — Timeline View

**Files:** `ui/timeline_view.py`

**Description:** A split-panel view with a calendar widget on the left and a daily grouped log tree on the right. Selecting a date filters logs to that day. Logs grouped under date headers.

**Dependencies:** Task 2 (Repository for get_logs_grouped_by_date()), Task 7 (LogList)

**Acceptance Criteria:**
- Left panel: `tkcalendar.Calendar` widget showing current month
- Right panel: `ttk.Treeview` with date headers as parent rows, log entries as child rows
- Selecting a date on calendar → updates log tree to show that day's entries
- Expandable/collapsible date groups
- "Today" button to jump to current date
- Previous/Next day navigation buttons

---

## Task 9 — Main Window

**Files:** `ui/main_window.py`

**Description:** The top-level application window that orchestrates all UI components: ControlPanel, TimelineView, LogList, TagDialog. Manages layout, state transitions, and callbacks between components.

**Dependencies:** Tasks 5, 6, 7, 8 (all UI components), Task 2 (Repository), Task 4 (AudioRecorder)

**Acceptance Criteria:**
- Window title: "voxlog — Voice Logger"
- Default geometry: 1200x800, centered on screen
- Top bar: ControlPanel (record/stop, status, live transcript)
- Main area (PanedWindow): TimelineView (calendar + tree) on left, LogList on right
- Tag filter bar at bottom
- Record button → starts AudioRecorder with callbacks wired to UI updates
- Stop button → shows review dialog → on save refreshes timeline + log list
- Window close cleans up audio resources and DB connection
- Settings gear icon (future placeholder)

---

## Task 10 — Entry Point

**Files:** `main.py`

**Description:** Application bootstrap — parse args, ensure model exists, init DB, create MainWindow, start tkinter main loop.

**Dependencies:** Task 9 (MainWindow), Task 2 (Repository init_db)

**Acceptance Criteria:**
- `if __name__ == "__main__": main()`
- Check if Vosk model directory exists; print helpful error if not
- `Repository.init_db()` called on startup
- `MainWindow` instantiated and `mainloop()` started
- Graceful exit on Ctrl+C or window close

---

## Task 11 — README

**Files:** `README.md`

**Description:** User-facing setup, installation, and usage guide.

**Dependencies:** All tasks complete

**Acceptance Criteria:**
- Prerequisites (Python, system packages)
- Installation steps
- Model download instructions
- How to run
- How to use (record, review, tag, timeline)
- Troubleshooting tips

---

## Implementation Log

### ✅ Task 1 — Project Scaffolding (DONE)

**Files created:**
- `src/__init__.py` — package marker
- `src/config.py` — `ROOT`, `DATA_DIR`, `MODEL_DIR`, `DB_PATH`, `SAMPLE_RATE`, `BLOCK_SIZE`, `PARTIAL_INTERVAL_MS`
- `src/db/__init__.py` — package marker
- `src/audio/__init__.py` — package marker
- `src/stt/__init__.py` — package marker
- `src/ui/__init__.py` — package marker
- `requirements.txt` — `vosk==0.3.45`, `sounddevice==0.5.5`, `numpy==1.26.0`, `tkcalendar==1.6.1`
- `scripts/download_model.sh` — downloads & extracts vosk-model-en-us-0.22
- `.gitignore` — ignores `data/`, `*.db`, `__pycache__`, `.venv`, etc.

**Verified:** config imports and resolves paths correctly.

---

### ✅ Task 2 — Database Layer (DONE)

**Files created:**
- `db/schema.sql` — DDL with `logs` table (`id`, `timestamp`, `text`, `duration_ms`, `tags`) + indexes
- `db/repository.py` — `Repository` class with:
  - `init_db()` / `connect()` / `close()`
  - `insert_log(text, duration_ms, tags)` → `int`
  - `get_log(id)` → `dict | None`
  - `get_logs(date_from, date_to, tag_filter, search, limit, offset)` → `list[dict]`
  - `update_log(id, text, tags)` → `bool`
  - `delete_log(id)` → `bool`
  - `get_all_tags()` → `list[str]`
  - `get_logs_grouped_by_date(month, year)` → `dict[str, list[dict]]`
  - `get_logs_for_date(date)` → `list[dict]`

**Verified:** All CRUD operations tested successfully.

---

### ✅ Task 3 — STT Engine (DONE)

**File created:** `stt/vosk_engine.py`

**Class:** `VoskEngine`
- `__init__(model_path, sample_rate)` — loads Vosk `Model`, creates `KaldiRecognizer`
- `accept_waveform(data: bytes) -> str | None` — feeds audio, returns final text when utterance complete
- `partial_result() -> str` — returns interim transcription
- `final_result() -> str` — forces final result on stop
- `reset()` — creates fresh recognizer for new session
- `sample_rate` property — exposes config value for audio stream setup

---

### ✅ Task 4 — Audio Recorder (DONE)

**Files created:**
- `audio/device.py` — `AudioDeviceManager` class with:
  - `list_input_devices()` → `list[AudioDevice]`
  - `default_input_name()` → `str | None`
  - `device_id_by_name(name)` → `int | None`
- `audio/recorder.py` — `AudioRecorder` class with:
  - `start(on_partial, on_final)` — opens `sd.RawInputStream`, spawns worker thread
  - `stop()` — stops stream, joins thread, flushes `final_result()`
  - `is_recording` — property
  - Threading: audio callback pushes to `queue.Queue`, worker pulls and feeds Vosk, partial results emitted every `PARTIAL_INTERVAL_MS`
  - Callbacks called from worker thread (UI wraps with `root.after()`)

---

### ✅ Task 5 — Control Panel UI (DONE)

**File created:** `ui/control_panel.py`

**Class:** `ControlPanel(ttk.Frame)`
- Record button (● Record) — starts recording, disables self, enables Stop
- Stop button (■ Stop) — stops recording, triggers `on_stop_cb`, re-enables Record
- Status label — shows "Idle" (gray), "Recording..." (red), "Processing..." (orange)
- Live transcript — `tk.Text` widget (read-only) showing partial results in real time
- `show_review_dialog(transcript)` — creates a `Toplevel` with:
  - Editable `tk.Text` pre-filled with final transcript
  - Save button → calls `on_save_cb(edited_text)` → refreshes UI
  - Discard button → closes without saving
  - Modal (grab_set), transient on parent

---

### ✅ Task 6 — Tag Dialog (DONE)

**File created:** `ui/tag_dialog.py`

**Class:** `TagDialog(tk.Toplevel)`
- Entry field with autocomplete from existing DB tags
- Listbox dropdown appears below entry, filtered as user types (case-insensitive)
- Arrow keys navigate suggestions, Enter/Tab/click inserts selected tag
- Current tags shown as comma-separated text below entry
- Duplicate prevention (can't add same tag twice)
- Submit returns deduplicated list via `on_submit` callback
- Cancel/Escape closes without changes

---

### ✅ Task 7 — Log List (DONE)

**File created:** `ui/log_list.py`

**Class:** `LogList(ttk.Frame)`
- `ttk.Treeview` with columns: Time, Text, Tags
- Search bar — filters entries in real time as user types (`trace_add` on StringVar)
- Tag filter — `Combobox` dropdown with all unique tags from DB; "✕" clears filter
- Right-click context menu: Edit Text, Edit Tags, Delete, Copy Text
- Double-click opens text edit dialog
- `refresh(target_date)` reloads data from DB, applies search + tag filters
- Empty state label when no logs exist
- Edit Text: `Toplevel` with `tk.Text`, Save/Cancel
- Edit Tags: opens `TagDialog` with autocomplete

---

### ✅ Task 8 — Timeline View (DONE)

**File created:** `ui/timeline_view.py`

**Class:** `TimelineView(ttk.Frame)`
- Left panel: `tkcalendar.Calendar` widget with date selection
- Right panel: `ttk.Treeview` showing that day's logs with time, text, and tags
- Navigation buttons: ◀ (prev day), Today, ▶ (next day)
- Calendar label showing selected date (e.g. "Monday, June 28, 2026")
- `on_date_select(date)` callback fires when date changes (calendar click, nav buttons)
- `refresh(target_date)` updates calendar selection and preview tree
- Empty state: "No entries for this day" when day has no logs

---

### ✅ Task 9 — Main Window (DONE)

**File created:** `ui/main_window.py`

**Class:** `MainWindow(tk.Tk)`
- Title: "voxlog — Voice Logger", geometry 1200x800, centered
- Top: `ControlPanel` (record/stop, status, live transcript, review dialog)
- Main area: `PanedWindow` with `TimelineView` (left, weight 1) and `LogList` (right, weight 2)
- Recording flow:
  - Record → `AudioRecorder.start(on_partial, on_final)`
  - `on_partial` → updates live transcript via `after()`
  - `on_final` → appends completed utterance, updates live transcript
  - Stop → `AudioRecorder.stop()` → appends final result → shows review dialog
  - Save → `Repository.insert_log()` → refreshes TimelineView + LogList
- Date selection → filters LogList to selected day
- Window close → stops recording if active, closes DB connection

---

### ✅ Task 10 — Entry Point (DONE)

**File created:** `main.py`

**Function:** `main()`
- Checks `MODEL_DIR.exists()` → prints download instructions if missing, exits with code 1
- Creates `Repository`, calls `init_db()` (creates tables if not exist)
- Creates `VoskEngine(MODEL_DIR)` — loads the Vosk model
- Creates `MainWindow(repo, engine)` and starts `mainloop()`

---

### ✅ Task 11 — README (DONE)

**File created:** `README.md`

**Structure (per README_MAKER.md template):**
- Hero section (centered): project name, tagline, shields.io badges (Python, tkinter, Vosk, SQLite, Linux)
- 📖 The Story — personal motivation (forgetting daily work, flow interruption)
- ✨ Features — 8 bullet points covering all app capabilities
- 🛠️ Tech Stack — table with layers and technologies
- 📍 The Process — why Python, why Vosk, architecture (3 threads), review flow, DB schema
- 🚀 Running Locally — commands for Pop!_OS/Ubuntu: system deps, venv, pip install, model download, run
- Footer — "Built with care by Raj G."
- No screenshot placeholder (as requested)

# Session Memory — Jarvis V2 / VoxLog

## Project
- **Repo:** `https://github.com/gsraj0301/VoxLog`
- **Path:** `/home/raj/Documents/personal projects/voxlog/`
- **Platform:** Pop!_OS (Linux)
- **Stack:** Python 3.12, tkinter, Vosk, sounddevice, SQLite3, tkcalendar
- **Language:** Python only

## What Was Built
Desktop voice activity logger with:
- Push-to-talk recording (Record/Stop buttons)
- Offline STT via Vosk (vosk-model-en-us-0.22, ~1.8GB)
- Live partial transcription during recording
- Review dialog before saving (edit + save/discard)
- SQLite storage (single `logs` table: id, timestamp, text, duration_ms, tags)
- Tags with autocomplete from existing tags
- Timeline/calendar view (tkcalendar) + searchable log list
- Daily preview tree (time — text [tags])

## Architecture
- **3 threads:** main (tkinter), producer (audio callback → queue), worker (queue → Vosk)
- **UI → worker thread callbacks** go through `root.after()` for thread safety
- **`AudioRecorder`** owns threading, accepts `on_partial`/`on_final` callbacks
- **`MainWindow`** orchestrates everything — ControlPanel, TimelineView, LogList, AudioRecorder, Repository

## Key Decisions
| Decision | Choice |
|----------|--------|
| STT Model | vosk-model-en-us-0.22 (large, more accurate) |
| Review flow | Record → live transcript → Stop → review dialog → Save/Discard |
| Tags storage | JSON text column in SQLite (`["tag1","tag2"]`) |
| No audio files | Transcript only, no WAV saving |
| Push-to-talk | Button-activated (no hotword engine) |

## Files (22 tracked)
```
.gitignore  README.md  SPEC.md  main.py  requirements.txt
scripts/download_model.sh
src/config.py
src/db/schema.sql  src/db/repository.py
src/stt/vosk_engine.py
src/audio/device.py  src/audio/recorder.py
src/ui/control_panel.py  src/ui/tag_dialog.py
src/ui/log_list.py  src/ui/timeline_view.py  src/ui/main_window.py
```

## User Preferences (from README_MAKER.md)
- README style: hero (centered), story, features, tech stack, process, preview, running locally, footer
- Personal & honest tone, emoji headers, shields.io badges
- Screenshots in `screenshots/` directory
- No license section

## Run Commands
```bash
cd /home/raj/Documents/personal\ projects/voxlog
./run.sh
# or manually:
source .venv/bin/activate && python3 main.py
```

## First Run Requirements
1. `./scripts/download_model.sh` (~1.8GB Vosk model)
2. System deps: `python3-tk`, `libportaudio2`, `portaudio19-dev`

<div align="center">

# 🎙️ voxlog

### Your Desktop Voice Activity Logger

**Log what you do. Review when you need to. All offline, all private.**

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![GUI](https://img.shields.io/badge/GUI-tkinter-FF6F00?logo=tkinter&logoColor=white)
![STT](https://img.shields.io/badge/STT-Vosk-00BFFF?logo=vosk&logoColor=white)
![DB](https://img.shields.io/badge/DB-SQLite-003B57?logo=sqlite&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Linux%20(Pop!_OS)-48B9C7?logo=linux&logoColor=white)

</div>

---

## 📖 The Story

I was tired of forgetting what I worked on during the day. Every evening I'd sit down to log my hours and draw a blank — "what did I even do after lunch?" I tried note-taking apps, time trackers, even spreadsheets. Nothing stuck because stopping to type breaks your flow.

So I built voxlog. A simple voice logger that sits on my desktop. I press a button, say what I'm doing, and it transcribes it offline. No internet, no cloud, no subscriptions. At the end of the day I open the calendar view and see everything I logged. It's that straightforward.

---

## ✨ Features

- **Push-to-talk recording** — click Record, speak, click Stop. Review before saving.
- **Offline speech recognition** — runs entirely on your machine via Vosk. Nothing leaves your computer.
- **Live transcription** — see what you're saying in real time as you speak.
- **Review & edit** — review the transcript before saving. Fix any mistakes the STT made.
- **Timeline calendar view** — pick a date on the calendar, see everything you logged that day.
- **Search & filter** — search by text or filter by tags across all your entries.
- **Tagging with autocomplete** — tag your logs and let the app suggest tags you've used before.
- **100% free & open source** — no API keys, no subscriptions, no cloud dependencies.

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **GUI** | tkinter (built-in Python) |
| **Speech Recognition** | Vosk (vosk-model-en-us-0.22, ~1.8GB) |
| **Audio Capture** | sounddevice (PortAudio) |
| **Database** | SQLite3 |
| **Calendar Widget** | tkcalendar |
| **Platform** | Pop!_OS (Linux) |

---

## 📍 The Process

### Why Python?

Python had every library I needed right out of the box. tkinter for the GUI (built-in, zero deps), sqlite3 for the database (built-in), sounddevice for clean audio capture, and Vosk for offline speech recognition with official Python bindings. The GIL isn't an issue — Vosk runs in C++, sounddevice in C, and Python just shuttles bytes between them.

### Why Vosk over cloud APIs?

Privacy. I wanted a logger that works without internet. Vosk's `vosk-model-en-us-0.22` (~1.8GB) gives excellent accuracy for a desktop app. No API keys, no rate limits, no data leaving my machine.

### Architecture

The app uses three threads: the main tkinter thread for the UI, a producer thread feeding audio from the microphone into a queue, and a worker thread pulling audio out and feeding it to Vosk. UI updates from worker threads are scheduled via `root.after()` to keep tkinter happy. The result is a responsive UI that never blocks during recording.

### The Review Flow

I wanted a "human in the loop" — you record, you see live transcription, you stop, you review the text, and *then* you save. This catches STT errors before they hit the database. Every log entry is editable after the fact too — text, tags, or deletion.

### Database Schema

A single `logs` table with an ID, timestamp, text, duration, and a JSON tags column. Simple, flat, no joins. Tags are stored as JSON text arrays which makes querying easy (`WHERE tags LIKE '%"work"%'`).

---

## 🚀 Running Locally

```bash
# 1. Install system dependencies (Pop!_OS / Ubuntu)
sudo apt install python3-tk libportaudio2 portaudio19-dev

# 2. Clone and set up
cd voxlog
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Download the Vosk model (~1.8GB)
./scripts/download_model.sh

# 4. Run
python3 main.py
```

---

<div align="center">

Built with care by Raj G.

</div>

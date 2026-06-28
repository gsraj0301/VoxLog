from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = ROOT / "data"
MODEL_DIR = DATA_DIR / "vosk-model-en-us-0.22"
DB_PATH = ROOT / "logs.db"

SAMPLE_RATE = 16000
BLOCK_SIZE = 8000
PARTIAL_INTERVAL_MS = 200

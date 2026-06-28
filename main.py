import sys

from src.config import MODEL_DIR
from src.db.repository import Repository
from src.stt.vosk_engine import VoskEngine
from src.ui.main_window import MainWindow


def main():
    if not MODEL_DIR.exists():
        print(
            f"Vosk model not found at: {MODEL_DIR}\n\n"
            "Download it first:\n"
            "  ./scripts/download_model.sh\n"
            "or manually from:\n"
            "  https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip"
        )
        sys.exit(1)

    repo = Repository()
    repo.init_db()

    engine = VoskEngine(MODEL_DIR)

    app = MainWindow(repo, engine)
    app.mainloop()


if __name__ == "__main__":
    main()

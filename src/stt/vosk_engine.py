import json
from pathlib import Path

from vosk import KaldiRecognizer, Model


class VoskEngine:
    def __init__(self, model_path: Path, sample_rate: int = 16000):
        self._sample_rate = sample_rate
        self._model = Model(str(model_path))
        self._rec = KaldiRecognizer(self._model, self._sample_rate)
        self._rec.SetWords(False)

    @property
    def sample_rate(self) -> int:
        return self._sample_rate

    def accept_waveform(self, data: bytes) -> str | None:
        if self._rec.AcceptWaveform(data):
            result = json.loads(self._rec.Result())
            text = result.get("text", "").strip()
            return text if text else None
        return None

    def partial_result(self) -> str:
        result = json.loads(self._rec.PartialResult())
        return result.get("partial", "").strip()

    def final_result(self) -> str:
        result = json.loads(self._rec.FinalResult())
        text = result.get("text", "").strip()
        return text

    def reset(self):
        self._rec = KaldiRecognizer(self._model, self._sample_rate)
        self._rec.SetWords(False)

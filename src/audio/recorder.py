import queue
import threading
import time
from collections.abc import Callable

import sounddevice as sd

from src.config import BLOCK_SIZE, PARTIAL_INTERVAL_MS, SAMPLE_RATE
from src.stt.vosk_engine import VoskEngine

PartialCallback = Callable[[str], None]
FinalCallback = Callable[[str], None]


class AudioRecorder:
    def __init__(
        self,
        vosk_engine: VoskEngine,
        sample_rate: int = SAMPLE_RATE,
        blocksize: int = BLOCK_SIZE,
        device_id: int | None = None,
    ):
        self._engine = vosk_engine
        self._sample_rate = sample_rate
        self._blocksize = blocksize
        self._device_id = device_id

        self._audio_queue: queue.Queue[bytes] = queue.Queue()
        self._stop_event = threading.Event()
        self._stream: sd.RawInputStream | None = None
        self._worker: threading.Thread | None = None
        self._recording = False
        self._on_partial: PartialCallback | None = None
        self._on_final: FinalCallback | None = None

    def start(self, on_partial: PartialCallback | None = None, on_final: FinalCallback | None = None):
        if self._recording:
            return

        self._recording = True
        self._stop_event.clear()
        self._engine.reset()

        self._on_partial = on_partial
        self._on_final = on_final

        self._stream = sd.RawInputStream(
            samplerate=self._sample_rate,
            blocksize=self._blocksize,
            dtype="int16",
            channels=1,
            device=self._device_id,
            callback=self._audio_callback,
        )
        self._stream.start()

        self._worker = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker.start()

    def stop(self) -> str:
        if not self._recording:
            return ""

        self._recording = False
        self._stop_event.set()

        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        if self._worker and self._worker.is_alive():
            self._worker.join(timeout=3.0)

        final = self._engine.final_result()
        if final and self._on_final:
            self._on_final(final)
        return final

    @property
    def is_recording(self) -> bool:
        return self._recording

    def _audio_callback(self, indata, frames, time_info, status):
        if status:
            print(f"[audio] {status}")
        self._audio_queue.put(indata.copy())

    def _worker_loop(self):
        next_partial_time = time.monotonic() + (PARTIAL_INTERVAL_MS / 1000)

        while not self._stop_event.is_set() or not self._audio_queue.empty():
            try:
                data = self._audio_queue.get(timeout=0.1)
                audio_bytes = data.tobytes()
                result = self._engine.accept_waveform(audio_bytes)
                if result and self._on_final:
                    self._on_final(result)
                    self._engine.reset()
            except queue.Empty:
                pass

            now = time.monotonic()
            if now >= next_partial_time:
                partial = self._engine.partial_result()
                if partial and self._on_partial:
                    self._on_partial(partial)
                next_partial_time = now + (PARTIAL_INTERVAL_MS / 1000)

"""Microphone capture for the duration the hotkey is held down."""

import queue
import numpy as np
import sounddevice as sd


class Recorder:
    def __init__(self, sample_rate: int = 16000, max_seconds: int = 60):
        self.sample_rate = sample_rate
        self.max_frames = sample_rate * max_seconds
        self._q: "queue.Queue[np.ndarray]" = queue.Queue()
        self._stream = None
        self._recording = False

    def _callback(self, indata, frames, time_info, status):
        if status:
            # Overflow/underflow warnings land here; don't crash on them.
            pass
        self._q.put(indata.copy())

    def start(self):
        if self._recording:
            return
        self._recording = True
        # Drain any stale audio left over from a previous session.
        with self._q.mutex:
            self._q.queue.clear()
        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="float32",
            callback=self._callback,
        )
        self._stream.start()

    def stop(self) -> np.ndarray:
        """Stop recording and return the captured audio as a mono float32 array."""
        if not self._recording:
            return np.zeros((0,), dtype=np.float32)
        self._recording = False
        self._stream.stop()
        self._stream.close()
        self._stream = None

        chunks = []
        total_frames = 0
        while not self._q.empty():
            chunk = self._q.get_nowait()
            chunks.append(chunk)
            total_frames += len(chunk)
            if total_frames >= self.max_frames:
                break

        if not chunks:
            return np.zeros((0,), dtype=np.float32)

        audio = np.concatenate(chunks, axis=0).flatten()
        if len(audio) > self.max_frames:
            audio = audio[: self.max_frames]
        return audio

"""Local, offline speech-to-text using faster-whisper (CTranslate2 Whisper).

No API key, no network calls after the model is downloaded once. The model is
cached under ~/.cache/whisperlinux/models/ for reuse across runs.
"""

import numpy as np
from faster_whisper import WhisperModel

from .config import Config, MODEL_DIR


class Transcriber:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        # faster-whisper downloads the model from Hugging Face on first use and
        # caches it locally under download_root — fully offline afterwards.
        self.model = WhisperModel(
            cfg.model_size,
            device=cfg.device,
            compute_type=cfg.compute_type,
            download_root=str(MODEL_DIR),
        )

    def transcribe(self, audio: np.ndarray) -> str:
        if audio.size == 0:
            return ""

        segments, _info = self.model.transcribe(
            audio,
            language=self.cfg.language or None,
            beam_size=5,
            vad_filter=True,  # trims leading/trailing silence, skips dead air
            vad_parameters=dict(min_silence_duration_ms=300),
        )
        text = "".join(seg.text for seg in segments).strip()
        return text

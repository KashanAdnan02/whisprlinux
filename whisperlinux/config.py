"""Config file handling for WhisperLinux.

Stored at ~/.config/whisperlinux/config.json. Created with defaults on first run.
"""

import json
import os
from dataclasses import dataclass, asdict, field
from pathlib import Path

CONFIG_DIR = Path(os.path.expanduser("~/.config/whisperlinux"))
CONFIG_PATH = CONFIG_DIR / "config.json"
CACHE_DIR = Path(os.path.expanduser("~/.cache/whisperlinux"))
MODEL_DIR = CACHE_DIR / "models"

DEFAULTS = {
    # Single-key push-to-talk hotkey (used when hotkey_modifiers is empty).
    # See evdev.ecodes for names, e.g. KEY_RIGHTCTRL, KEY_PAUSE, KEY_F13.
    "hotkey": "KEY_RIGHTCTRL",
    # Hold all listed modifiers together to record. Left or right side counts for each.
    # Windows/Super key = KEY_LEFTMETA. Set to [] to use hotkey instead.
    "hotkey_modifiers": ["KEY_LEFTALT", "KEY_LEFTMETA", "KEY_LEFTSHIFT"],
    # tiny.en / base.en / small.en / medium.en / large-v3
    "model_size": "base.en",
    # cpu or cuda
    "device": "cpu",
    # int8 is fastest on CPU with a small accuracy tradeoff; float16 for GPU
    "compute_type": "int8",
    # Set to a language code (e.g. "en") to skip auto-detection and go faster.
    # Leave null to auto-detect.
    "language": "en",
    # Sample rate for recording; 16000 is what Whisper expects internally.
    "sample_rate": 16000,
    # Max seconds of audio to buffer for a single recording (safety cap).
    "max_record_seconds": 60,
    # If true, a short beep-like tray icon change signals recording start/stop.
    # (Actual audio beep not implemented by default to avoid extra deps.)
    "visual_feedback": True,
    # Automatically add a trailing space after typed text.
    "trailing_space": True,
}


@dataclass
class Config:
    hotkey: str = DEFAULTS["hotkey"]
    hotkey_modifiers: list[str] = field(default_factory=lambda: list(DEFAULTS["hotkey_modifiers"]))
    model_size: str = DEFAULTS["model_size"]
    device: str = DEFAULTS["device"]
    compute_type: str = DEFAULTS["compute_type"]
    language: str = DEFAULTS["language"]
    sample_rate: int = DEFAULTS["sample_rate"]
    max_record_seconds: int = DEFAULTS["max_record_seconds"]
    visual_feedback: bool = DEFAULTS["visual_feedback"]
    trailing_space: bool = DEFAULTS["trailing_space"]

    def to_dict(self):
        return asdict(self)


def load_config() -> Config:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    if not CONFIG_PATH.exists():
        cfg = Config()
        save_config(cfg)
        return cfg

    try:
        with open(CONFIG_PATH, "r") as f:
            data = json.load(f)
        merged = {**DEFAULTS, **data}
        return Config(**{k: merged[k] for k in DEFAULTS.keys()})
    except (json.JSONDecodeError, TypeError, KeyError):
        # Corrupt config: fall back to defaults but don't overwrite the broken
        # file automatically, so the user can inspect what went wrong.
        return Config()


def save_config(cfg: Config) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg.to_dict(), f, indent=2)

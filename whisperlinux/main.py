"""WhisperLinux entrypoint.

Hold the configured hotkey, speak, release — the transcribed text is typed at
the current cursor focus. Fully offline, no API costs.
"""

import logging
import signal
import sys
import time

from . import __version__
from .config import load_config
from .hotkey import HotkeyListener
from .recorder import Recorder
from .transcriber import Transcriber
from .injector import Injector
from .tray import TrayApp

log = logging.getLogger("whisperlinux")


def _setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="[%(name)s] %(message)s",
    )


def run() -> None:
    _setup_logging()
    cfg = load_config()
    log.info("WhisperLinux %s", __version__)
    log.info("loaded config: %s", cfg)

    log.info("loading whisper model (first run downloads it, then it's cached)...")
    transcriber = Transcriber(cfg)
    log.info("model ready.")

    recorder = Recorder(sample_rate=cfg.sample_rate, max_seconds=cfg.max_record_seconds)
    injector = Injector()
    log.info("detected session type: %s", injector.session)

    tray = TrayApp(on_quit=lambda: sys.exit(0))
    if cfg.visual_feedback:
        tray.start()

    def on_press():
        if cfg.visual_feedback:
            tray.set_state("recording")
        log.info("recording...")
        recorder.start()

    def on_release():
        if cfg.visual_feedback:
            tray.set_state("transcribing")
        audio = recorder.stop()
        log.info("captured %.2fs, transcribing...", len(audio) / cfg.sample_rate)
        text = transcriber.transcribe(audio)
        if cfg.trailing_space and text:
            text += " "
        if text:
            log.info("-> %r", text)
            injector.type_text(text)
        else:
            log.info("(no speech detected)")
        if cfg.visual_feedback:
            tray.set_state("idle")

    if cfg.hotkey_modifiers:
        listener = HotkeyListener(on_press, on_release, modifier_names=cfg.hotkey_modifiers)
    else:
        listener = HotkeyListener(on_press, on_release, key_name=cfg.hotkey)
    listener.start()
    log.info(
        "listening for hotkey: %s. Hold it, speak, release. Ctrl+C to quit.",
        listener.hotkey_label,
    )

    def handle_sigint(sig, frame):
        log.info("shutting down...")
        listener.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_sigint)

    while True:
        time.sleep(1)


def main():
    run()


if __name__ == "__main__":
    main()

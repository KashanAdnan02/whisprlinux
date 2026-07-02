"""Types transcribed text at the current cursor focus.

Uses xdotool under X11 and ydotool under Wayland. Session type is detected via
XDG_SESSION_TYPE, with a fallback probe if that variable isn't set.
"""

import logging
import os
import shutil
import subprocess

log = logging.getLogger("whisperlinux.injector")


def _session_type() -> str:
    session = os.environ.get("XDG_SESSION_TYPE", "").lower()
    if session in ("x11", "wayland"):
        return session
    # Fallback heuristic if the env var is missing.
    if os.environ.get("WAYLAND_DISPLAY"):
        return "wayland"
    if os.environ.get("DISPLAY"):
        return "x11"
    return "unknown"


class Injector:
    def __init__(self):
        self.session = _session_type()
        self._check_tooling()

    def _check_tooling(self):
        if self.session == "x11" and shutil.which("xdotool") is None:
            raise RuntimeError("xdotool not found. Install it: sudo apt install xdotool")
        if self.session == "wayland" and shutil.which("ydotool") is None:
            raise RuntimeError(
                "ydotool not found. Install it and make sure ydotoold is running "
                "(see README.md)."
            )

    def type_text(self, text: str):
        if not text:
            return
        if self.session == "x11":
            result = subprocess.run(
                ["xdotool", "type", "--clearmodifiers", "--", text],
                capture_output=True,
                text=True,
            )
        elif self.session == "wayland":
            result = subprocess.run(
                ["ydotool", "type", "--", text],
                capture_output=True,
                text=True,
            )
        else:
            raise RuntimeError(
                "Could not detect X11 or Wayland session (XDG_SESSION_TYPE unset). "
                "Text injection unavailable."
            )
        if result.returncode != 0:
            log.warning("text injection failed: %s", result.stderr.strip() or result.returncode)

"""Minimal system tray icon reflecting app state (idle / recording / transcribing)."""

import threading
from PIL import Image, ImageDraw
import pystray

_COLORS = {
    "idle": (120, 120, 120),
    "recording": (220, 50, 50),
    "transcribing": (240, 180, 30),
}


def _make_icon(color):
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((8, 8, 56, 56), fill=color)
    return img


class TrayApp:
    def __init__(self, on_quit=None):
        self._on_quit = on_quit
        self._icon = pystray.Icon(
            "whisperlinux",
            _make_icon(_COLORS["idle"]),
            "WhisperLinux - idle",
            menu=pystray.Menu(pystray.MenuItem("Quit", self._quit)),
        )
        self._thread = None

    def start(self):
        self._thread = threading.Thread(target=self._icon.run, daemon=True)
        self._thread.start()

    def set_state(self, state: str):
        color = _COLORS.get(state, _COLORS["idle"])
        self._icon.icon = _make_icon(color)
        self._icon.title = f"WhisperLinux - {state}"

    def _quit(self, icon, item):
        icon.stop()
        if self._on_quit:
            self._on_quit()

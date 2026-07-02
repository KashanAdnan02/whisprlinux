"""Global push-to-talk hotkey listener using raw evdev input devices.

This intentionally bypasses the display server (X11/Wayland) entirely by reading
key events straight from the kernel input devices. That's what makes it work
identically under Wayland compositors that block X11-style global key hooks.

Requires the current user to be in the `input` group (see README.md).
"""

import asyncio
import threading
from typing import Callable

import evdev
from evdev import ecodes, InputDevice, categorize

# Left/right pairs so either side satisfies a modifier in a chord.
_MODIFIER_GROUPS = {
    ecodes.KEY_LEFTALT: (ecodes.KEY_LEFTALT, ecodes.KEY_RIGHTALT),
    ecodes.KEY_RIGHTALT: (ecodes.KEY_LEFTALT, ecodes.KEY_RIGHTALT),
    ecodes.KEY_LEFTMETA: (ecodes.KEY_LEFTMETA, ecodes.KEY_RIGHTMETA),
    ecodes.KEY_RIGHTMETA: (ecodes.KEY_LEFTMETA, ecodes.KEY_RIGHTMETA),
    ecodes.KEY_LEFTSHIFT: (ecodes.KEY_LEFTSHIFT, ecodes.KEY_RIGHTSHIFT),
    ecodes.KEY_RIGHTSHIFT: (ecodes.KEY_LEFTSHIFT, ecodes.KEY_RIGHTSHIFT),
    ecodes.KEY_LEFTCTRL: (ecodes.KEY_LEFTCTRL, ecodes.KEY_RIGHTCTRL),
    ecodes.KEY_RIGHTCTRL: (ecodes.KEY_LEFTCTRL, ecodes.KEY_RIGHTCTRL),
}


def _resolve_modifier_groups(modifier_names: list[str]) -> list[tuple[int, ...]]:
    groups = []
    for name in modifier_names:
        code = getattr(ecodes, name, None)
        if code is None:
            raise ValueError(
                f"Unknown key name '{name}'. Use KEY_* constants from evdev.ecodes, "
                f"e.g. KEY_LEFTALT, KEY_LEFTMETA, KEY_LEFTSHIFT."
            )
        groups.append(_MODIFIER_GROUPS.get(code, (code,)))
    return groups


def _list_keyboard_devices():
    """Return all input devices that look like keyboards (i.e. emit key events)."""
    devices = []
    for path in evdev.list_devices():
        try:
            dev = InputDevice(path)
        except (PermissionError, OSError):
            continue
        caps = dev.capabilities()
        if ecodes.EV_KEY in caps:
            # Cheap heuristic: real keyboards support a wide range of key codes,
            # not just e.g. a couple of buttons on a mouse.
            key_codes = caps[ecodes.EV_KEY]
            if len(key_codes) > 20:
                devices.append(dev)
        else:
            dev.close()
    return devices


class HotkeyListener:
    """Watches all keyboard devices for a key press/release or modifier chord.

    on_press() and on_release() are called from a background thread — callers
    must be thread-safe or hand work off to another thread/queue themselves.
    """

    def __init__(
        self,
        on_press: Callable[[], None],
        on_release: Callable[[], None],
        key_name: str | None = None,
        modifier_names: list[str] | None = None,
    ):
        self.on_press = on_press
        self.on_release = on_release
        self._devices = []
        self._thread = None
        self._loop = None
        self._stop_event = threading.Event()
        self._is_down = False
        self._key_down: dict[int, bool] = {}

        if modifier_names:
            self._chord_mode = True
            self._modifier_groups = _resolve_modifier_groups(modifier_names)
            self.key_code = None
            self.hotkey_label = " + ".join(modifier_names)
        elif key_name:
            self._chord_mode = False
            self._modifier_groups = []
            self.key_code = getattr(ecodes, key_name, None)
            if self.key_code is None:
                raise ValueError(
                    f"Unknown key name '{key_name}'. Use a KEY_* constant from evdev.ecodes, "
                    f"e.g. KEY_RIGHTCTRL, KEY_RIGHTALT, KEY_PAUSE, KEY_F13."
                )
            self.hotkey_label = key_name
        else:
            raise ValueError("Provide either key_name or modifier_names.")

    def start(self):
        self._devices = _list_keyboard_devices()
        if not self._devices:
            raise RuntimeError(
                "No readable keyboard devices found. Check that you're in the "
                "'input' group and have re-logged in (see README.md)."
            )
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._loop is not None:
            self._loop.call_soon_threadsafe(self._loop.stop)
        for dev in self._devices:
            try:
                dev.close()
            except OSError:
                pass

    def _run_loop(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        tasks = [self._loop.create_task(self._watch_device(dev)) for dev in self._devices]
        try:
            self._loop.run_forever()
        finally:
            for t in tasks:
                t.cancel()
            self._loop.close()

    def _chord_held(self) -> bool:
        return all(
            any(self._key_down.get(code, False) for code in group)
            for group in self._modifier_groups
        )

    def _update_chord_state(self):
        held = self._chord_held()
        if held and not self._is_down:
            self._is_down = True
            self.on_press()
        elif not held and self._is_down:
            self._is_down = False
            self.on_release()

    async def _watch_device(self, dev: InputDevice):
        try:
            async for event in dev.async_read_loop():
                if event.type != ecodes.EV_KEY:
                    continue
                key_event = categorize(event)
                # keystate: 0 = up, 1 = down, 2 = hold/repeat
                if key_event.keystate == key_event.key_down:
                    self._key_down[key_event.scancode] = True
                elif key_event.keystate == key_event.key_up:
                    self._key_down[key_event.scancode] = False
                else:
                    continue

                if self._chord_mode:
                    self._update_chord_state()
                elif key_event.scancode == self.key_code:
                    if key_event.keystate == key_event.key_down and not self._is_down:
                        self._is_down = True
                        self.on_press()
                    elif key_event.keystate == key_event.key_up and self._is_down:
                        self._is_down = False
                        self.on_release()
        except (OSError, asyncio.CancelledError):
            return

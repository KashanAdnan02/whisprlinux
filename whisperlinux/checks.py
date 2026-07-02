"""Pre-flight checks for dependencies and permissions."""

import os
import shutil
import sys

import evdev
from evdev import ecodes, InputDevice


def _session_type() -> str:
    session = os.environ.get("XDG_SESSION_TYPE", "").lower()
    if session in ("x11", "wayland"):
        return session
    if os.environ.get("WAYLAND_DISPLAY"):
        return "wayland"
    if os.environ.get("DISPLAY"):
        return "x11"
    return "unknown"


def _in_input_group() -> bool:
    try:
        import grp
        groups = [grp.getgrgid(g).gr_name for g in os.getgroups()]
        return "input" in groups
    except OSError:
        return False


def _readable_keyboards() -> list[str]:
    devices = []
    for path in evdev.list_devices():
        try:
            dev = InputDevice(path)
            caps = dev.capabilities()
            if ecodes.EV_KEY in caps and len(caps[ecodes.EV_KEY]) > 20:
                devices.append(dev.name or path)
            dev.close()
        except (PermissionError, OSError):
            continue
    return devices


def run_checks() -> int:
    ok = True
    print("WhisperLinux system check\n")

    session = _session_type()
    print(f"  Session type: {session or 'unknown'}")

    for tool in ("python3",):
        found = shutil.which(tool)
        print(f"  {tool}: {'OK' if found else 'MISSING'}")
        ok = ok and bool(found)

    if session == "x11":
        found = shutil.which("xdotool")
        print(f"  xdotool: {'OK' if found else 'MISSING (sudo apt install xdotool)'}")
        ok = ok and bool(found)
    elif session == "wayland":
        found = shutil.which("ydotool")
        print(f"  ydotool: {'OK' if found else 'MISSING (sudo apt install ydotool)'}")
        ok = ok and bool(found)

    in_group = _in_input_group()
    print(f"  input group: {'OK' if in_group else 'MISSING (sudo usermod -aG input $USER, then log out/in)'}")
    ok = ok and in_group

    keyboards = _readable_keyboards()
    if keyboards:
        print(f"  keyboard access: OK ({len(keyboards)} device(s))")
    else:
        print("  keyboard access: FAILED (cannot read /dev/input/*)")
        ok = False

    try:
        import sounddevice as sd
        sd.query_devices()
        print("  audio (PortAudio): OK")
    except Exception as exc:
        print(f"  audio (PortAudio): FAILED ({exc})")
        ok = False

    print()
    if ok:
        print("All checks passed. Run: whisperlinux")
        return 0
    print("Some checks failed. See README.md for setup instructions.")
    return 1


if __name__ == "__main__":
    sys.exit(run_checks())

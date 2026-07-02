# WhisperLinux

Free, fully offline push-to-talk dictation for Linux — hold a hotkey, speak, release, and transcribed text is typed at your cursor.

- **100% local** speech-to-text via [faster-whisper](https://github.com/SYSTRAN/faster-whisper) — no API keys, no cloud, no cost after the model downloads once
- **X11 and Wayland** — hotkeys read at the kernel `evdev` level
- **Text injection** via `xdotool` (X11) or `ydotool` (Wayland)
- **System tray** icon showing idle / recording / transcribing state

## Download

Pre-built packages for Linux x86_64 are in [`website/downloads/`](website/downloads/) after running the release build.

| Method | Best for |
|--------|----------|
| `.deb` package | Ubuntu, Debian, Mint, Pop!_OS |
| `.tar.gz` portable | Arch, Fedora, other distros |
| `./install.sh` | Developers / from source |

### One-line install (Ubuntu/Debian)

```bash
curl -fsSL https://whisperlinux.org/install.sh | bash
```

### .deb install

```bash
sudo apt install ./whisperlinux_1.0.0_amd64.deb
whisperlinux --check
```

### Portable tarball

```bash
tar -xzf whisperlinux-1.0.0-linux-amd64.tar.gz
cd whisperlinux-1.0.0-linux-amd64
./install.sh
whisperlinux --check
```

**Important:** log out and back in after install so the `input` group membership takes effect.

## How to use

1. Run `whisperlinux` (or enable autostart — see below)
2. Hold **Alt + Super + Shift** (default hotkey chord)
3. Speak while holding
4. Release — text is typed wherever your cursor is focused

## Autostart on login

```bash
systemctl --user enable --now whisperlinux.service
```

## Configuration

Edit `~/.config/whisperlinux/config.json` (created on first run):

| Option | Default | Description |
|--------|---------|-------------|
| `hotkey_modifiers` | Alt+Super+Shift | Modifier chord to hold |
| `hotkey` | `KEY_RIGHTCTRL` | Single-key fallback (when modifiers list is empty) |
| `model_size` | `base.en` | `tiny.en`, `base.en`, `small.en`, `medium.en`, `large-v3` |
| `device` | `cpu` | `cpu` or `cuda` (NVIDIA GPU) |
| `language` | `en` | Language code; speeds up transcription |

## Build release packages

For maintainers — builds `.deb`, portable tarball, and copies them to `website/downloads/`:

```bash
./packaging/build-release.sh
```

Host the `website/` folder on any static host (GitHub Pages, Netlify, Vercel, nginx).

## Development

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
./run.sh
whisperlinux --check
```

### Permissions

WhisperLinux needs read access to `/dev/input/*` (hotkeys) and optionally `/dev/uinput` (Wayland typing):

```bash
sudo usermod -aG input $USER
# log out and back in
```

### Wayland

Ensure `ydotoold` is running:

```bash
sudo systemctl enable --now ydotool.service   # if packaged
# or: ydotoold &
```

## Project layout

```
whisperlinux/          Application source
packaging/             .deb build, systemd, desktop, icons
website/               Download page (host online)
install.sh             Local / tarball installer
run.sh                 Dev launcher with input-group workaround
```

## License

MIT — see [LICENSE](LICENSE).

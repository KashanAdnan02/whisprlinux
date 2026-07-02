#!/usr/bin/env bash
# WhisperLinux installer — local source tree or extracted tarball.
set -euo pipefail

INSTALL_PREFIX="${INSTALL_PREFIX:-$HOME/.local/share/whisperlinux}"
SYSTEM_INSTALL="${SYSTEM_INSTALL:-0}"
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "== WhisperLinux installer =="

install_system_deps() {
    if command -v apt >/dev/null; then
        sudo apt update
        sudo apt install -y \
            python3 python3-pip python3-venv \
            xdotool ydotool \
            libportaudio2 libasound2 \
            portaudio19-dev
    elif command -v dnf >/dev/null; then
        sudo dnf install -y python3 python3-pip xdotool ydotool portaudio-devel
    elif command -v pacman >/dev/null; then
        sudo pacman -Sy --noconfirm python python-pip xdotool ydotool portaudio
    else
        echo "Install manually: python3, pip, venv, xdotool, ydotool, portaudio"
    fi
}

setup_permissions() {
    echo "Adding $USER to the 'input' group..."
    sudo usermod -aG input "$USER" || true
    echo 'KERNEL=="uinput", GROUP="input", MODE="0660"' | \
        sudo tee /etc/udev/rules.d/99-whisperlinux-uinput.rules >/dev/null
    sudo udevadm control --reload-rules 2>/dev/null || true
    sudo udevadm trigger 2>/dev/null || true
}

install_user_local() {
    mkdir -p "$INSTALL_PREFIX"
    rsync -a --delete \
        --exclude venv --exclude dist --exclude .git \
        "$REPO_DIR/whisperlinux" \
        "$REPO_DIR/requirements.txt" \
        "$REPO_DIR/pyproject.toml" \
        "$REPO_DIR/LICENSE" \
        "$REPO_DIR/README.md" \
        "$INSTALL_PREFIX/"

    if [[ ! -d "$REPO_DIR/venv" ]]; then
        python3 -m venv "$INSTALL_PREFIX/venv"
        "$INSTALL_PREFIX/venv/bin/pip" install --upgrade pip wheel
        "$INSTALL_PREFIX/venv/bin/pip" install -r "$INSTALL_PREFIX/requirements.txt"
    else
        rsync -a "$REPO_DIR/venv/" "$INSTALL_PREFIX/venv/"
    fi

    mkdir -p "$HOME/.local/bin"
    cat > "$HOME/.local/bin/whisperlinux" <<EOF
#!/usr/bin/env bash
set -euo pipefail
INSTALL_DIR="$INSTALL_PREFIX"
PYTHON="\${INSTALL_DIR}/venv/bin/python"
run() { cd "\$INSTALL_DIR" && exec "\$PYTHON" -m whisperlinux.cli "\$@"; }
if id -nG "\${USER}" | grep -qw input; then run "\$@"; else exec sg input -c "cd '\${INSTALL_DIR}' && exec '\${PYTHON}' -m whisperlinux.cli \$*"; fi
EOF
    chmod +x "$HOME/.local/bin/whisperlinux"

    mkdir -p "$HOME/.config/systemd/user"
    cat > "$HOME/.config/systemd/user/whisperlinux.service" <<EOF
[Unit]
Description=WhisperLinux offline push-to-talk dictation
After=graphical-session.target sound.target

[Service]
Type=simple
ExecStart=$HOME/.local/bin/whisperlinux
Restart=on-failure
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=default.target
EOF

    mkdir -p "$HOME/.local/share/applications"
    cat > "$HOME/.local/share/applications/whisperlinux.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=WhisperLinux
Comment=Offline push-to-talk dictation
Exec=$HOME/.local/bin/whisperlinux
Icon=audio-input-microphone
Categories=Utility;Audio;
Terminal=false
EOF

    echo ""
    echo "Installed to: $INSTALL_PREFIX"
    echo "Command: whisperlinux  (ensure ~/.local/bin is in your PATH)"
    echo ""
    echo "Enable autostart: systemctl --user enable --now whisperlinux.service"
}

install_system() {
    sudo mkdir -p /opt/whisperlinux
    sudo rsync -a --delete \
        --exclude venv --exclude dist --exclude .git \
        "$REPO_DIR/whisperlinux" \
        "$REPO_DIR/requirements.txt" \
        "$REPO_DIR/pyproject.toml" \
        "$REPO_DIR/LICENSE" \
        "$REPO_DIR/README.md" \
        /opt/whisperlinux/
    sudo install -m 755 "$REPO_DIR/packaging/setup-venv.sh" /opt/whisperlinux/setup-venv.sh
    sudo /opt/whisperlinux/setup-venv.sh
    sudo install -m 755 "$REPO_DIR/packaging/usr-bin-whisperlinux" /usr/bin/whisperlinux
    sudo install -m 644 "$REPO_DIR/packaging/whisperlinux.desktop" /usr/share/applications/whisperlinux.desktop
    sudo install -m 644 "$REPO_DIR/packaging/whisperlinux.svg" /usr/share/icons/hicolor/scalable/apps/whisperlinux.svg
    sudo install -m 644 "$REPO_DIR/packaging/whisperlinux.service" /usr/lib/systemd/user/whisperlinux.service
    sudo install -m 644 "$REPO_DIR/packaging/99-whisperlinux-uinput.rules" /etc/udev/rules.d/99-whisperlinux-uinput.rules
    sudo update-desktop-database 2>/dev/null || true
    echo "System install complete. Run: whisperlinux --check"
}

install_system_deps
setup_permissions

if [[ "$SYSTEM_INSTALL" == "1" ]]; then
    install_system
else
    install_user_local
fi

echo ""
echo "IMPORTANT: log out and back in for the 'input' group to take effect."
echo "Then run: whisperlinux --check"

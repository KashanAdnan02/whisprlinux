#!/usr/bin/env bash
# Build .deb and portable tarball for WhisperLinux releases.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VERSION="$(python3 -c "import pathlib; exec(pathlib.Path('$ROOT/whisperlinux/__init__.py').read_text()); print(__version__)")"
ARCH="amd64"
PKG="whisperlinux"
DEB_NAME="${PKG}_${VERSION}_${ARCH}.deb"
TARBALL="${PKG}-${VERSION}-linux-${ARCH}.tar.gz"
STAGING="$ROOT/dist/deb-staging"
DIST="$ROOT/dist"
WEBSITE_DL="$ROOT/website/downloads"

echo "== Building WhisperLinux ${VERSION} =="

rm -rf "$STAGING" "$DIST"
mkdir -p "$STAGING/DEBIAN"
mkdir -p "$STAGING/opt/whisperlinux"
mkdir -p "$STAGING/usr/bin"
mkdir -p "$STAGING/usr/share/applications"
mkdir -p "$STAGING/usr/share/icons/hicolor/scalable/apps"
mkdir -p "$STAGING/usr/lib/systemd/user"
mkdir -p "$STAGING/etc/udev/rules.d"

# Application files (no venv — created on first install)
rsync -a \
    --exclude venv \
    --exclude dist \
    --exclude .git \
    --exclude website/downloads \
    --exclude '__pycache__' \
    "$ROOT/whisperlinux" \
    "$ROOT/requirements.txt" \
    "$ROOT/pyproject.toml" \
    "$ROOT/README.md" \
    "$ROOT/LICENSE" \
    "$STAGING/opt/whisperlinux/"

install -m 755 "$ROOT/packaging/setup-venv.sh" "$STAGING/opt/whisperlinux/setup-venv.sh"
install -m 755 "$ROOT/packaging/usr-bin-whisperlinux" "$STAGING/usr/bin/whisperlinux"
install -m 644 "$ROOT/packaging/whisperlinux.desktop" "$STAGING/usr/share/applications/whisperlinux.desktop"
install -m 644 "$ROOT/packaging/whisperlinux.svg" "$STAGING/usr/share/icons/hicolor/scalable/apps/whisperlinux.svg"
install -m 644 "$ROOT/packaging/whisperlinux.service" "$STAGING/usr/lib/systemd/user/whisperlinux.service"
install -m 644 "$ROOT/packaging/99-whisperlinux-uinput.rules" "$STAGING/etc/udev/rules.d/99-whisperlinux-uinput.rules"

cat > "$STAGING/DEBIAN/control" <<EOF
Package: whisperlinux
Version: ${VERSION}
Section: sound
Priority: optional
Architecture: ${ARCH}
Depends: python3 (>= 3.10), python3-venv, python3-pip, xdotool, ydotool, libportaudio2, libasound2
Recommends: pipewire-pulse | pulseaudio
Maintainer: WhisperLinux <support@whisperlinux.org>
Homepage: https://whisperlinux.org
Description: Offline push-to-talk dictation for Linux
 WhisperLinux is a free, fully offline dictation tool. Hold a hotkey,
 speak, release — transcribed text is typed at your cursor. Uses local
 Whisper speech-to-text. Works on X11 and Wayland.
EOF

cat > "$STAGING/DEBIAN/postinst" <<'EOF'
#!/bin/bash
set -e

# Create Python environment on first install / upgrade
if [ -x /opt/whisperlinux/setup-venv.sh ]; then
    /opt/whisperlinux/setup-venv.sh || true
fi

# udev rule for ydotool / uinput
if command -v udevadm >/dev/null; then
    udevadm control --reload-rules 2>/dev/null || true
    udevadm trigger 2>/dev/null || true
fi

# Add installing user to input group when invoked via sudo/dpkg
TARGET_USER="${SUDO_USER:-${LOGNAME:-}}"
if [ -n "$TARGET_USER" ] && [ "$TARGET_USER" != "root" ]; then
    if ! id -nG "$TARGET_USER" | grep -qw input; then
        usermod -aG input "$TARGET_USER" || true
        NEED_RELOGIN=1
    fi
fi

if [ "${NEED_RELOGIN:-0}" = "1" ]; then
    echo ""
    echo "WhisperLinux: added $SUDO_USER to the 'input' group."
    echo "Please log out and back in, then run: whisperlinux --check"
else
    echo ""
    echo "WhisperLinux installed. Run: whisperlinux --check"
fi

exit 0
EOF

cat > "$STAGING/DEBIAN/prerm" <<'EOF'
#!/bin/bash
set -e
exit 0
EOF

chmod 755 "$STAGING/DEBIAN/postinst" "$STAGING/DEBIAN/prerm"

mkdir -p "$DIST" "$WEBSITE_DL"
dpkg-deb --build "$STAGING" "$DIST/$DEB_NAME"

# Portable tarball with pre-built venv for offline-friendly install
TARBALL_DIR="$DIST/${PKG}-${VERSION}-linux-${ARCH}"
rm -rf "$TARBALL_DIR"
mkdir -p "$TARBALL_DIR"

rsync -a \
    --exclude venv \
    --exclude dist \
    --exclude .git \
    --exclude website/downloads \
    --exclude '__pycache__' \
    "$ROOT/" "$TARBALL_DIR/"

python3 -m venv "$TARBALL_DIR/venv"
"$TARBALL_DIR/venv/bin/pip" install --upgrade pip wheel -q
"$TARBALL_DIR/venv/bin/pip" install -r "$TARBALL_DIR/requirements.txt" -q

tar -czf "$DIST/$TARBALL" -C "$DIST" "$(basename "$TARBALL_DIR")"

cp "$DIST/$DEB_NAME" "$DIST/$TARBALL" "$WEBSITE_DL/"

echo ""
echo "Built:"
echo "  $DIST/$DEB_NAME"
echo "  $DIST/$TARBALL"
echo "  (copied to website/downloads/)"

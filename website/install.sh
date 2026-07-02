#!/usr/bin/env bash
# Online installer for Whispr Linux — https://whisprlinux.vercel.app/install.sh
set -euo pipefail

VERSION="1.0.0"
BASE_URL="${WHISPR_LINUX_URL:-https://whisprlinux.vercel.app/downloads}"
ARCH="amd64"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "== Whispr Linux installer v${VERSION} =="

if ! command -v apt >/dev/null; then
    echo "Whispr Linux currently supports Ubuntu and Debian-based distros (.deb)." >&2
    echo "Download the .deb manually from https://whisprlinux.vercel.app" >&2
    exit 1
fi

echo "Detected Debian/Ubuntu — installing .deb package..."
DEB="${BASE_URL}/whisperlinux_${VERSION}_${ARCH}.deb"
curl -fsSL "$DEB" -o "$TMP/whisperlinux.deb"
sudo apt install -y "$TMP/whisperlinux.deb" || {
    sudo apt install -f -y
    sudo dpkg -i "$TMP/whisperlinux.deb"
}

echo ""
echo "Installed. Log out and back in, then run: whisperlinux --check"

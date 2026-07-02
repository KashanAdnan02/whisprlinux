#!/usr/bin/env bash
# Online installer for WhisperLinux — host this at https://your-site.com/install.sh
set -euo pipefail

VERSION="1.0.0"
BASE_URL="${WHISPERLINUX_URL:-https://whisperlinux.org/downloads}"
ARCH="amd64"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "== WhisperLinux online installer v${VERSION} =="

if command -v apt >/dev/null; then
    echo "Detected Debian/Ubuntu — installing .deb package..."
    DEB="${BASE_URL}/whisperlinux_${VERSION}_${ARCH}.deb"
    curl -fsSL "$DEB" -o "$TMP/whisperlinux.deb"
    sudo apt install -y "$TMP/whisperlinux.deb" || {
        sudo apt install -f -y
        sudo dpkg -i "$TMP/whisperlinux.deb"
    }
    echo ""
    echo "Installed. Log out and back in, then run: whisperlinux --check"
    exit 0
fi

echo "Using portable tarball install..."
TARBALL="${BASE_URL}/whisperlinux-${VERSION}-linux-${ARCH}.tar.gz"
curl -fsSL "$TARBALL" | tar -xz -C "$TMP"
EXTRACTED="$(find "$TMP" -maxdepth 1 -type d -name 'whisperlinux-*' | head -1)"
cd "$EXTRACTED"
bash install.sh

#!/usr/bin/env bash
# One-time setup: create Python venv and install dependencies.
set -euo pipefail

INSTALL_DIR="/opt/whisperlinux"
VENV="${INSTALL_DIR}/venv"

echo "== WhisperLinux setup =="

if ! command -v python3 >/dev/null; then
    echo "python3 is required. Install it first." >&2
    exit 1
fi

python3 -m venv "$VENV"
"${VENV}/bin/pip" install --upgrade pip wheel
"${VENV}/bin/pip" install -r "${INSTALL_DIR}/requirements.txt"

echo ""
echo "WhisperLinux Python environment ready at ${VENV}"
echo "Run: whisperlinux --check"

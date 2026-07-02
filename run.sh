#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
source venv/bin/activate

_run() {
    exec python3 -m whisperlinux.cli "$@"
}

if id -nG "${USER}" | grep -qw input; then
    _run "$@"
fi

quoted=""
for arg in "$@"; do
    quoted+=" $(printf '%q' "$arg")"
done
exec sg input -c "cd '$(pwd)' && source venv/bin/activate && exec python3 -m whisperlinux.cli${quoted}"

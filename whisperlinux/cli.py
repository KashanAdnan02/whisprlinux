"""Command-line entry point."""

import argparse
import sys

from . import __version__


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="whisperlinux",
        description="Offline push-to-talk dictation for Linux.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"whisperlinux {__version__}",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify dependencies, permissions, and hardware access.",
    )
    args = parser.parse_args()

    if args.check:
        from .checks import run_checks
        sys.exit(run_checks())

    from .main import run
    run()


if __name__ == "__main__":
    main()

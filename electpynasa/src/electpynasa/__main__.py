"""Package-level entry point: ``python -m electpynasa`` prints the version."""

from electpynasa.__version__ import __version__


def main() -> int:
    print(f"electpynasa {__version__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

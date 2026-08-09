"""Pytest configuration shared across the ElectPyNasa test suite."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure the package under src/ is importable without installation.
ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# Suppress the structured logger during tests by writing to a discard handler
# only when running under pytest. The library writes to sys.stdout by default;
# tests that need to assert on log output can capture stdout explicitly.
os.environ.setdefault("ELECTPYNASA_TEST_MODE", "1")

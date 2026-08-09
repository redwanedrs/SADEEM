"""Unit tests for the structured scientific logger."""

from __future__ import annotations

import json
import sys
from io import StringIO

import pytest

from electpynasa.utils.logging import LOG_PREFIX, SUCCESS_PREFIX, ScientificLogger


@pytest.fixture(autouse=True)
def capture_stdout(monkeypatch):
    """Redirect every logger emission to an in-memory buffer."""
    buf = StringIO()
    # The logger writes via the root Python logger's stream handler.
    # We monkeypatch the underlying stream.
    import logging
    handler = logging.getLogger("electpynasa").handlers[0]
    monkeypatch.setattr(handler, "stream", buf)
    # Also monkeypatch plain print() used by the success token.
    monkeypatch.setattr("builtins.print", lambda *a, **k: buf.write(" ".join(str(x) for x in a) + "\n"))
    return buf


class TestScientificLogger:
    def test_info_emits_structured_log(self, capture_stdout):
        ScientificLogger.info("hello", progress=42.0, extra={"k": "v"})
        line = capture_stdout.getvalue().strip()
        assert line.startswith(LOG_PREFIX)
        payload = json.loads(line[len(LOG_PREFIX):])
        assert payload["level"] == "INFO"
        assert payload["message"] == "hello"
        assert payload["progress"] == 42.0
        assert payload["extra"]["k"] == "v"

    def test_progress_is_clamped(self, capture_stdout):
        ScientificLogger.info("overshoot", progress=200.0)
        line = capture_stdout.getvalue().strip()
        payload = json.loads(line[len(LOG_PREFIX):])
        assert payload["progress"] == 100.0

        capture_stdout.truncate(0)
        capture_stdout.seek(0)
        ScientificLogger.info("undershoot", progress=-10.0)
        line = capture_stdout.getvalue().strip()
        payload = json.loads(line[len(LOG_PREFIX):])
        assert payload["progress"] == 0.0

    def test_success_token_format(self, capture_stdout):
        ScientificLogger.success("/tmp/output.tif")
        line = capture_stdout.getvalue().strip()
        assert line == f"{SUCCESS_PREFIX}/tmp/output.tif"

    def test_warning_and_error_levels(self, capture_stdout):
        ScientificLogger.warning("careful")
        ScientificLogger.error("broken", extra={"why": "test"})
        lines = [l for l in capture_stdout.getvalue().splitlines() if l.startswith(LOG_PREFIX)]
        assert len(lines) == 2
        assert json.loads(lines[0][len(LOG_PREFIX):])["level"] == "WARNING"
        assert json.loads(lines[1][len(LOG_PREFIX):])["level"] == "ERROR"

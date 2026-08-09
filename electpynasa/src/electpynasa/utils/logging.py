"""
Structured scientific logger for ElectPyNasa.

The logger emits two distinct payloads over ``stdout`` so that the Electron
frontend (or any other IPC consumer) can parse them deterministically:

* ``__LOG__:{json}`` — every informational / warning / error event, with
  optional progress percentage and arbitrary metadata.
* ``SUCCESS:{path}`` — terminal success token emitted exactly once per
  pipeline run, carrying the primary output artifact path.

The schema is intentionally minimal and stable; downstream parsers can rely
on the four keys ``timestamp``, ``level``, ``message``, ``progress`` plus the
optional ``extra`` map.
"""

from __future__ import annotations

import json
import logging
import sys
import time
from typing import Any, Optional


# ---------------------------------------------------------------------------
# IPC token prefixes — kept in sync with the Electron renderer parser.
# ---------------------------------------------------------------------------
LOG_PREFIX = "__LOG__:"
SUCCESS_PREFIX = "SUCCESS:"


# ---------------------------------------------------------------------------
# Standard Python logging integration
# ---------------------------------------------------------------------------
class _StreamToStdout(logging.StreamHandler):
    """A handler that always writes to ``sys.stdout`` (flushed immediately)."""

    def __init__(self) -> None:
        super().__init__(stream=sys.stdout)
        self.setFormatter(logging.Formatter("%(message)s"))


def _configure_root_logger() -> logging.Logger:
    """Configure the root ElectPyNasa logger exactly once."""
    logger = logging.getLogger("electpynasa")
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        logger.addHandler(_StreamToStdout())
        logger.propagate = False
    return logger


_ROOT_LOGGER = _configure_root_logger()


# ---------------------------------------------------------------------------
# Public structured logger
# ---------------------------------------------------------------------------
class ScientificLogger:
    """
    Structured scientific logger.

    All methods are class-methods so the logger can be used as a stateless
    façade from anywhere in the codebase without explicit instantiation.
    Every emission is flushed immediately to guarantee real-time UI updates
    when the library runs as a child process of the Electron bridge.
    """

    # ------------------------------------------------------------------
    # Low-level emission
    # ------------------------------------------------------------------
    @staticmethod
    def _emit(level: str, message: str, *,
              progress: Optional[float] = None,
              extra: Optional[dict[str, Any]] = None) -> None:
        payload: dict[str, Any] = {
            "timestamp": time.time(),
            "level": level.upper(),
            "message": message,
        }
        if progress is not None:
            payload["progress"] = max(0.0, min(100.0, float(progress)))
        if extra:
            payload["extra"] = {str(k): _coerce(v) for k, v in extra.items()}

        line = f"{LOG_PREFIX}{json.dumps(payload, ensure_ascii=False)}"
        _ROOT_LOGGER.info(line)

    # ------------------------------------------------------------------
    # Convenience classmethods
    # ------------------------------------------------------------------
    @classmethod
    def debug(cls, message: str, *,
              progress: Optional[float] = None,
              extra: Optional[dict[str, Any]] = None) -> None:
        cls._emit("DEBUG", message, progress=progress, extra=extra)

    @classmethod
    def info(cls, message: str, *,
             progress: Optional[float] = None,
             extra: Optional[dict[str, Any]] = None) -> None:
        cls._emit("INFO", message, progress=progress, extra=extra)

    @classmethod
    def warning(cls, message: str, *,
                extra: Optional[dict[str, Any]] = None) -> None:
        cls._emit("WARNING", message, extra=extra)

    @classmethod
    def error(cls, message: str, *,
              extra: Optional[dict[str, Any]] = None) -> None:
        cls._emit("ERROR", message, extra=extra)

    # ------------------------------------------------------------------
    # Terminal tokens
    # ------------------------------------------------------------------
    @classmethod
    def success(cls, output_path: str) -> None:
        """Emit the terminal success token consumed by the Electron bridge."""
        print(f"{SUCCESS_PREFIX}{output_path}", flush=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _coerce(value: Any) -> Any:
    """Make arbitrary values JSON-serializable for the ``extra`` payload."""
    if isinstance(value, (str, int, float, bool, type(None))):
        return value
    if isinstance(value, (list, tuple)):
        return [_coerce(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _coerce(v) for k, v in value.items()}
    return repr(value)


# ---------------------------------------------------------------------------
# Convenience module-level shortcut functions (mirror of classmethods)
# ---------------------------------------------------------------------------
def info(message: str, **kwargs: Any) -> None:
    ScientificLogger.info(message, **kwargs)


def warning(message: str, **kwargs: Any) -> None:
    ScientificLogger.warning(message, **kwargs)


def error(message: str, **kwargs: Any) -> None:
    ScientificLogger.error(message, **kwargs)


def success(output_path: str) -> None:
    ScientificLogger.success(output_path)

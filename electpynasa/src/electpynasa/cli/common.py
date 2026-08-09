"""
Shared CLI helpers.

Provides:

* :func:`build_arg_parser_factory` — returns a factory that builds a standard
  :class:`argparse.ArgumentParser` pre-configured with common options.
* :func:`safe_main` — wraps a CLI entry-point callable with uniform exception
  handling, structured logging, and a non-zero exit code on failure.
"""

from __future__ import annotations

import argparse
import sys
from typing import Callable, Optional, Sequence

from electpynasa.utils.exceptions import (
    ElectPyNasaError,
    PipelineError,
    PipelineStepError,
)
from electpynasa.utils.logging import ScientificLogger


def add_common_arguments(parser: argparse.ArgumentParser) -> None:
    """Add options shared by every CLI (currently only --verbose)."""
    parser.add_argument(
        "--verbose", action="store_true",
        help="Enable verbose (debug-level) structured logging.",
    )


def safe_main(callable_: Callable[[Sequence[str]], int],
              argv: Optional[Sequence[str]] = None) -> int:
    """
    Run *callable_* under uniform error handling.

    The callable receives the raw argv (defaulting to ``sys.argv[1:]``) and
    must return an int exit code (0 for success). Any
    :class:`ElectPyNasaError` is logged through the structured logger and
    returns a non-zero exit code. Any other unexpected exception is logged
    with full context and returns exit code 2.
    """
    effective_argv = sys.argv[1:] if argv is None else argv
    try:
        return int(callable_(effective_argv) or 0)
    except PipelineStepError as exc:
        ScientificLogger.error(
            f"Pipeline step '{exc.step_name}' failed: {exc.message}",
            extra=exc.context,
        )
        return 1
    except PipelineError as exc:
        ScientificLogger.error(f"Pipeline error: {exc.message}", extra=exc.context)
        return 1
    except ElectPyNasaError as exc:
        ScientificLogger.error(f"{exc.category}: {exc.message}", extra=exc.context)
        return 1
    except KeyboardInterrupt:
        ScientificLogger.warning("Interrupted by user.")
        return 130
    except Exception as exc:  # noqa: BLE001 - last-resort safety net
        ScientificLogger.error(
            f"Unhandled {type(exc).__name__}: {exc}",
            extra={"error_type": type(exc).__name__},
        )
        return 2

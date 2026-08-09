"""
Custom exception hierarchy for ElectPyNasa.

Design principles
-----------------
* Every error in the library inherits from :class:`ElectPyNasaError` so that
  callers can catch the entire family with a single ``except`` clause.
* Errors carry contextual metadata (file paths, parameters, etc.) that the
  structured logger can serialize.
* Each error class is narrow and descriptive — never raise a bare
  ``Exception`` from inside the library.
"""

from __future__ import annotations

from typing import Any, Optional


class ElectPyNasaError(Exception):
    """Base class for every error raised by the ElectPyNasa library."""

    #: Human-readable label used by the structured logger when emitting the
    #: error to the IPC bridge.
    category: str = "ELECTPYNASA_ERROR"

    def __init__(self, message: str, *, context: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.message = message
        self.context: dict[str, Any] = dict(context or {})

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.message


# ---------------------------------------------------------------------------
# Configuration / validation
# ---------------------------------------------------------------------------
class ConfigurationError(ElectPyNasaError):
    """Raised when a configuration object is internally inconsistent."""

    category = "CONFIGURATION_ERROR"


class ValidationError(ElectPyNasaError):
    """Raised when user-supplied input (path, parameter) fails validation."""

    category = "VALIDATION_ERROR"


# ---------------------------------------------------------------------------
# I/O
# ---------------------------------------------------------------------------
class IOError(ElectPyNasaError):  # noqa: A001 - intentional shadow of builtin
    """Raised when a file cannot be opened, decoded, or written."""

    category = "IO_ERROR"


class UnsupportedFormatError(IOError):
    """Raised when an input file format is not supported by any loader."""

    category = "UNSUPPORTED_FORMAT_ERROR"


class CorruptDataError(IOError):
    """Raised when a file is recognized but cannot be decoded."""

    category = "CORRUPT_DATA_ERROR"


# ---------------------------------------------------------------------------
# Processing
# ---------------------------------------------------------------------------
class ProcessingError(ElectPyNasaError):
    """Base class for every error originating from a processing step."""

    category = "PROCESSING_ERROR"


class NormalizationError(ProcessingError):
    """Raised when normalization cannot be performed (e.g. uniform image)."""

    category = "NORMALIZATION_ERROR"


class StretchError(ProcessingError):
    """Raised when a stretch strategy cannot be applied to the input."""

    category = "STRETCH_ERROR"


class RegistrationError(ProcessingError):
    """Raised when no alignment strategy could align the target to the reference."""

    category = "REGISTRATION_ERROR"


class BalancingError(ProcessingError):
    """Raised when color balancing fails (e.g. empty channels)."""

    category = "BALANCING_ERROR"


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------
class PipelineError(ElectPyNasaError):
    """Raised when a pipeline aborts before producing any output."""

    category = "PIPELINE_ERROR"


class PipelineStepError(PipelineError):
    """Raised when an individual pipeline step fails."""

    category = "PIPELINE_STEP_ERROR"

    def __init__(self, step_name: str, message: str, *,
                 context: Optional[dict[str, Any]] = None) -> None:
        full = f"[{step_name}] {message}"
        super().__init__(full, context=context)
        self.step_name = step_name

"""
Common type aliases, enums and dataclasses shared across ElectPyNasa.

Keeping these in a single module makes the public type surface stable and
easy to import from anywhere in the codebase.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Tuple

import numpy as np

# ---------------------------------------------------------------------------
# Numerical aliases
# ---------------------------------------------------------------------------
#: A 2D grayscale image, values typically in ``[0, 1]`` after normalization.
GrayImage = np.ndarray  # shape: (H, W), dtype: float

#: A 2D RGB image, shape ``(H, W, 3)``.
RGBImage = np.ndarray

#: A ``(low, high)`` window returned by normalization strategies.
Window = Tuple[float, float]


class Channel(str, Enum):
    """Named channel for color-composite workflows."""

    RED = "red"
    GREEN = "green"
    BLUE = "blue"

    @classmethod
    def ordered(cls) -> tuple["Channel", "Channel", "Channel"]:
        """Return the canonical RGB ordering used by the composite pipeline."""
        return (cls.RED, cls.GREEN, cls.BLUE)


class LogLevel(str, Enum):
    """Structured log levels (mirrored on the JS side)."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class LoaderResult:
    """Result returned by :class:`~electpynasa.io.loaders.ImageLoader`."""

    data: np.ndarray
    source_path: str
    original_shape: tuple
    sanitized_pixels: int = 0


@dataclass(frozen=True)
class NormalizationResult:
    """Result returned by the percentile normalizer."""

    data: np.ndarray
    window: Window


@dataclass(frozen=True)
class GrayscalePipelineResult:
    """Final artifact container for the grayscale pipeline."""

    grayscale_path: str
    window: Window
    shape: tuple


@dataclass(frozen=True)
class CompositePipelineResult:
    """Final artifact container for the composite pipeline."""

    hdr_path: str
    preview_path: str
    shape: tuple


@dataclass(frozen=True)
class PyramidPipelineResult:
    """Final artifact container for the DZI pyramid pipeline."""

    dzi_path: str
    tiles_directory: str
    base_name: str


# ---------------------------------------------------------------------------
# Internal step outcome
# ---------------------------------------------------------------------------
@dataclass
class StepOutcome:
    """Generic outcome of a single pipeline step."""

    label: str
    payload: dict = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def note(self, message: str) -> None:
        self.notes.append(message)

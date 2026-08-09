"""
Numerical sanity helpers used to guard processing pipelines.

The functions here are intentionally tiny and side-effect free so they can be
re-used both as preconditions (in pipelines) and as assertions in tests.
"""

from __future__ import annotations

from typing import Tuple

import numpy as np

from electpynasa.utils.exceptions import ValidationError


def require_2d(array: np.ndarray, *, label: str = "image") -> None:
    """Raise :class:`ValidationError` unless *array* has exactly 2 dimensions."""
    if not isinstance(array, np.ndarray):
        raise ValidationError(f"{label} must be a numpy.ndarray", context={"type": type(array).__name__})
    if array.ndim != 2:
        raise ValidationError(
            f"{label} must be 2D, got shape {array.shape}",
            context={"shape": list(array.shape)},
        )


def require_same_shape(a: np.ndarray, b: np.ndarray, *,
                       label_a: str = "target",
                       label_b: str = "reference") -> None:
    """Validate that two arrays have identical shapes."""
    if a.shape != b.shape:
        raise ValidationError(
            f"{label_a} and {label_b} must have the same shape, "
            f"got {a.shape} vs {b.shape}",
            context={"shape_a": list(a.shape), "shape_b": list(b.shape)},
        )


def require_range(array: np.ndarray, low: float, high: float, *,
                  label: str = "image") -> None:
    """Validate that *array* values are contained within ``[low, high]``."""
    if array.size == 0:
        raise ValidationError(f"{label} is empty")
    finite = array[np.isfinite(array)]
    if finite.size == 0:
        raise ValidationError(f"{label} contains no finite values")
    vmin, vmax = float(finite.min()), float(finite.max())
    if vmin < low - 1e-9 or vmax > high + 1e-9:
        raise ValidationError(
            f"{label} values out of [{low}, {high}]: "
            f"min={vmin:.6f}, max={vmax:.6f}",
            context={"min": vmin, "max": vmax, "low": low, "high": high},
        )


def finite_or_zero(array: np.ndarray) -> np.ndarray:
    """Replace ``NaN`` / ``Inf`` with ``0`` and return a new array."""
    return np.nan_to_num(array, nan=0.0, posinf=0.0, neginf=0.0)


def safe_percentile(array: np.ndarray, q: float) -> float:
    """Compute a single percentile, ignoring non-finite values."""
    finite = array[np.isfinite(array)]
    if finite.size == 0:
        return 0.0
    return float(np.percentile(finite, q))


def safe_minmax(array: np.ndarray) -> Tuple[float, float]:
    """Return ``(min, max)`` of the finite values of *array* (``0, 0`` if empty)."""
    finite = array[np.isfinite(array)]
    if finite.size == 0:
        return 0.0, 0.0
    return float(finite.min()), float(finite.max())

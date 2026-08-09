"""Unit tests for the GHS, Arcsinh and Logarithmic stretch strategies."""

from __future__ import annotations

import numpy as np
import pytest

from electpynasa.config import GHSConfig, ArcsinhConfig
from electpynasa.processing.stretching import (
    ArcsinhStretch,
    GHSStretch,
    LogarithmicStretch,
)
from electpynasa.utils.exceptions import StretchError


# ---------------------------------------------------------------------------
# GHS
# ---------------------------------------------------------------------------
class TestGHSStretch:
    def test_fixed_point_at_symmetry_point(self) -> None:
        """g(s; k, L, s) must equal s exactly."""
        for s in (0.1, 0.2, 0.25, 0.5, 0.9):
            engine = GHSStretch(GHSConfig(s=s))
            out = engine.stretch(np.array([s], dtype=np.float64))
            assert abs(float(out[0]) - s) < 1e-12

    def test_monotonic_increasing(self) -> None:
        """GHS is monotonically non-decreasing; clipping at 0/1 may produce
        flat regions near the boundaries, which is correct behavior."""
        x = np.linspace(0.0, 1.0, 1001)
        out = GHSStretch().stretch(x)
        assert np.all(np.diff(out) >= -1e-12)

    def test_output_clipped_to_unit_range(self) -> None:
        x = np.linspace(0.0, 1.0, 1001)
        out = GHSStretch(GHSConfig(k=10.0, L=20.0, s=0.05)).stretch(x)
        assert out.min() >= 0.0
        assert out.max() <= 1.0

    def test_extreme_k_does_not_explode(self) -> None:
        x = np.linspace(0.0, 1.0, 101)
        out = GHSStretch(GHSConfig(k=100.0, L=200.0, s=0.5)).stretch(x)
        assert np.all(np.isfinite(out))

    def test_empty_image_raises(self) -> None:
        with pytest.raises(StretchError):
            GHSStretch().stretch(np.array([]))

    def test_invalid_config_rejected(self) -> None:
        with pytest.raises(ValueError):
            GHSConfig(s=1.5)
        with pytest.raises(ValueError):
            GHSConfig(k=-1.0)


# ---------------------------------------------------------------------------
# Arcsinh
# ---------------------------------------------------------------------------
class TestArcsinhStretch:
    def test_zero_input_maps_to_zero(self) -> None:
        out = ArcsinhStretch().stretch(np.array([0.0]))
        assert abs(float(out[0])) < 1e-12

    def test_one_input_maps_to_one(self) -> None:
        """asinh(1/beta) / asinh(1/beta) == 1 by construction."""
        out = ArcsinhStretch(ArcsinhConfig(beta=0.15)).stretch(np.array([1.0]))
        assert abs(float(out[0]) - 1.0) < 1e-9

    def test_monotonic_increasing(self) -> None:
        x = np.linspace(0.0, 1.0, 1001)
        out = ArcsinhStretch().stretch(x)
        assert np.all(np.diff(out) > 0)


# ---------------------------------------------------------------------------
# Logarithmic
# ---------------------------------------------------------------------------
class TestLogarithmicStretch:
    def test_zero_input_maps_to_zero(self) -> None:
        out = LogarithmicStretch(scale=10.0).stretch(np.array([0.0]))
        assert abs(float(out[0])) < 1e-12

    def test_one_input_maps_to_one(self) -> None:
        out = LogarithmicStretch(scale=10.0).stretch(np.array([1.0]))
        assert abs(float(out[0]) - 1.0) < 1e-9

    def test_invalid_scale_rejected(self) -> None:
        with pytest.raises(ValueError):
            LogarithmicStretch(scale=-1.0)

"""Unit tests for percentile normalization and shadow/highlight protection."""

from __future__ import annotations

import numpy as np
import pytest

from electpynasa.config import GHSConfig, NormalizationConfig
from electpynasa.processing.normalization import PercentileNormalizer
from electpynasa.processing.protection import ShadowHighlightProtector
from electpynasa.utils.exceptions import NormalizationError


class TestPercentileNormalizer:
    def test_output_in_unit_range(self) -> None:
        img = np.random.RandomState(0).rand(64, 64) * 1e6
        result = PercentileNormalizer().normalize(img)
        assert result.data.min() >= 0.0
        assert result.data.max() <= 1.0

    def test_window_matches_percentiles(self) -> None:
        img = np.linspace(0, 100, 101)
        result = PercentileNormalizer(NormalizationConfig(lower_pct=10, upper_pct=90)).normalize(img)
        assert result.window[0] == pytest.approx(10.0, abs=1.0)
        assert result.window[1] == pytest.approx(90.0, abs=1.0)

    def test_uniform_image_falls_back_to_min_max(self) -> None:
        img = np.full((10, 10), 5.0)
        result = PercentileNormalizer().normalize(img)
        # Fallback path: high = low + 1.0
        assert np.all(np.isfinite(result.data))

    def test_empty_image_raises(self) -> None:
        with pytest.raises(NormalizationError):
            PercentileNormalizer().normalize(np.array([]))

    def test_all_nan_raises(self) -> None:
        with pytest.raises(NormalizationError):
            PercentileNormalizer().normalize(np.full((5, 5), np.nan))


class TestShadowHighlightProtector:
    def test_identity_when_no_protection(self) -> None:
        """With sp=0 and hp=1.0 the protector must be a no-op."""
        cfg = GHSConfig(shadow_protect=0.0, highlight_protect=1.0)
        x = np.linspace(0, 1, 11)
        y = x ** 2
        out = ShadowHighlightProtector(cfg).apply(x, y)
        assert np.allclose(out, y)

    def test_shadow_protection_pulls_dark_pixels_toward_original(self) -> None:
        cfg = GHSConfig(shadow_protect=0.1, shadow_blend_strength=1.0,
                        highlight_protect=1.0)
        x = np.array([0.0, 0.05, 0.1, 0.5])
        y = np.array([0.5, 0.5, 0.5, 0.5])  # stretched value constant
        out = ShadowHighlightProtector(cfg).apply(x, y)
        # At x=0 the weight is 1, blend strength 1 -> full original (0.0)
        assert abs(out[0] - 0.0) < 1e-9
        # At x=0.05: w = 1 - 0.05/0.1 = 0.5; blend = 0.5 * 1.0 = 0.5
        # out = 0.5*0.05 + (1 - 0.5)*0.5 = 0.025 + 0.25 = 0.275
        assert abs(out[1] - 0.275) < 1e-6
        # At x=sp the weight is 0 -> out = y = 0.5
        assert abs(out[2] - 0.5) < 1e-9

    def test_highlight_protection_compresses_bright_pixels(self) -> None:
        cfg = GHSConfig(shadow_protect=0.0, highlight_protect=0.9,
                        highlight_compress_strength=1.0, s=0.2)
        x = np.array([0.95, 1.0])
        y = np.array([0.9, 1.0])
        out = ShadowHighlightProtector(cfg).apply(x, y)
        # Bright pixels should be compressed toward the symmetry point s.
        assert out[1] < y[1]

    def test_shape_mismatch_raises(self) -> None:
        from electpynasa.utils.exceptions import ProcessingError
        with pytest.raises(ProcessingError):
            ShadowHighlightProtector().apply(np.zeros((5, 5)), np.zeros((6, 6)))

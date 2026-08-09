"""Unit tests for the Lupton smart color balancer."""

from __future__ import annotations

import numpy as np
import pytest

from electpynasa.config import BalancingConfig
from electpynasa.processing.balancing import LuptonBalancer
from electpynasa.utils.exceptions import BalancingError


class TestLuptonBalancer:
    def test_output_shape_and_dtype(self) -> None:
        r = np.random.rand(64, 64)
        g = np.random.rand(64, 64)
        b = np.random.rand(64, 64)
        out = LuptonBalancer().balance(r, g, b)
        assert out.shape == (64, 64, 3)
        assert out.dtype == np.uint8
        assert out.min() >= 0
        assert out.max() <= 255

    def test_shape_mismatch_raises(self) -> None:
        with pytest.raises(BalancingError):
            LuptonBalancer().balance(
                np.zeros((10, 10)),
                np.zeros((20, 20)),
                np.zeros((10, 10)),
            )

    def test_uniform_channels_produce_neutral_gray(self) -> None:
        """If R=G=B, the output pixels should have equal R,G,B values."""
        channel = np.full((32, 32), 0.5)
        out = LuptonBalancer(BalancingConfig(saturation=1.0, non_linear_factor=1.0)).balance(
            channel, channel.copy(), channel.copy(),
        )
        np.testing.assert_allclose(out[..., 0], out[..., 1], atol=2)
        np.testing.assert_allclose(out[..., 1], out[..., 2], atol=2)

    def test_high_saturation_increases_color_spread(self) -> None:
        """Increasing saturation should not decrease the variance between channels."""
        r = np.random.RandomState(0).rand(64, 64) * 0.8 + 0.1
        g = np.random.RandomState(1).rand(64, 64) * 0.8 + 0.1
        b = np.random.RandomState(2).rand(64, 64) * 0.8 + 0.1

        low = LuptonBalancer(BalancingConfig(saturation=0.5)).balance(r, g, b)
        high = LuptonBalancer(BalancingConfig(saturation=2.5)).balance(r, g, b)
        # Saturation boost should not collapse channel means
        assert high.std() >= low.std() * 0.9

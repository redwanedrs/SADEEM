"""Unit tests for the registration chain (astroalign → ECC → ORB)."""

from __future__ import annotations

import numpy as np
import pytest

from electpynasa.config import AstroalignConfig, ECCConfig, ORBConfig
from electpynasa.processing.registration import (
    AstroalignStrategy,
    ECCStrategy,
    ORBStrategy,
    RegistrationChainBuilder,
)
from electpynasa.core.interfaces import RegistrationChain
from electpynasa.utils.exceptions import RegistrationError


def _synthetic_image(shift: tuple[int, int] = (0, 0), shape: tuple[int, int] = (128, 128)) -> np.ndarray:
    """A synthetic grayscale image with well-distributed bright stars."""
    rng = np.random.RandomState(42)
    img = np.zeros(shape, dtype=np.float32) + 1e-3
    y, x = np.mgrid[0:shape[0], 0:shape[1]]
    for cx, cy, amp in [(20, 30, 50), (60, 80, 80), (100, 40, 60),
                        (40, 100, 70), (90, 90, 90)]:
        img += amp * np.exp(-((x - cx - shift[0]) ** 2 + (y - cy - shift[1]) ** 2) / 6.0)
    img += rng.normal(0, 1e-4, shape)
    return img


class TestRegistrationChain:
    def test_chain_builds_with_three_strategies(self) -> None:
        chain = RegistrationChainBuilder.build_default()
        assert isinstance(chain, RegistrationChain)
        assert len(chain.strategies) == 3

    def test_chain_raises_when_every_strategy_fails(self) -> None:
        """If every strategy raises, the chain must raise RegistrationError."""

        class _AlwaysFail(AstroalignStrategy):
            name = "always-fail"

            def align(self, target, reference):
                raise RuntimeError("boom")

        chain = RegistrationChain([_AlwaysFail()])
        with pytest.raises(RegistrationError):
            chain.align(np.zeros((5, 5)), np.zeros((5, 5)))


class TestECCStrategy:
    def test_identity_input_returns_image_unchanged_in_shape(self) -> None:
        ref = _synthetic_image()
        # Target == reference → ECC should converge to identity warp
        out = ECCStrategy(ECCConfig(motion_type="translation", iterations=20)).align(ref, ref)
        assert out.shape == ref.shape

    def test_shape_mismatch_raises(self) -> None:
        with pytest.raises(RegistrationError):
            ECCStrategy().align(np.zeros((10, 10)), np.zeros((20, 20)))


class TestORBStrategy:
    def test_too_few_features_raises(self) -> None:
        # Uniform image has no features
        uniform = np.zeros((64, 64), dtype=np.float32)
        with pytest.raises(RegistrationError):
            ORBStrategy(ORBConfig(min_matches=5)).align(uniform, uniform)

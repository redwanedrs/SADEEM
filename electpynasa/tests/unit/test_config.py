"""Unit tests for the config dataclasses."""

from __future__ import annotations

import pytest

from electpynasa.config import (
    BalancingConfig,
    CompositePipelineConfig,
    ECCConfig,
    GHSConfig,
    GrayscalePipelineConfig,
    NormalizationConfig,
    ORBConfig,
    PyramidConfig,
    PyramidPipelineConfig,
)


class TestGHSConfig:
    def test_defaults(self):
        c = GHSConfig()
        assert c.k == 2.5
        assert c.L == 6.0
        assert c.s == 0.20

    @pytest.mark.parametrize("bad", [0.0, -1.0, 1.5])
    def test_invalid_s_rejected(self, bad):
        with pytest.raises(ValueError):
            GHSConfig(s=bad)

    def test_to_dict_roundtrip(self):
        d = GHSConfig(k=3.0, L=4.0, s=0.5).to_dict()
        assert d["k"] == 3.0
        assert d["L"] == 4.0
        assert d["s"] == 0.5


class TestNormalizationConfig:
    def test_invalid_order_rejected(self):
        with pytest.raises(ValueError):
            NormalizationConfig(lower_pct=99.5, upper_pct=0.5)

    def test_boundary_ok(self):
        NormalizationConfig(lower_pct=0.0, upper_pct=100.0)


class TestPyramidConfig:
    @pytest.mark.parametrize("fmt", ["jpeg", "png", "webp"])
    def test_formats_accepted(self, fmt):
        PyramidConfig(tile_format=fmt)

    def test_invalid_format_rejected(self):
        with pytest.raises(ValueError):
            PyramidConfig(tile_format="avif")

    def test_quality_range(self):
        with pytest.raises(ValueError):
            PyramidConfig(quality=0)
        with pytest.raises(ValueError):
            PyramidConfig(quality=101)


class TestPipelineConfig:
    def test_grayscale_pipeline_composition(self):
        c = GrayscalePipelineConfig()
        assert isinstance(c.normalization, NormalizationConfig)
        assert isinstance(c.ghs, GHSConfig)

    def test_composite_pipeline_composition(self):
        c = CompositePipelineConfig()
        assert isinstance(c.normalization, NormalizationConfig)
        assert isinstance(c.ghs, GHSConfig)
        assert isinstance(c.balancing, BalancingConfig)

    def test_pyramid_pipeline_composition(self):
        c = PyramidPipelineConfig()
        assert isinstance(c.pyramid, PyramidConfig)

"""Integration tests for the end-to-end grayscale pipeline."""

from __future__ import annotations

import numpy as np
import pytest
import tifffile
from astropy.io import fits

from electpynasa.config import GHSConfig, GrayscalePipelineConfig, NormalizationConfig
from electpynasa.pipelines import GrayscalePipeline


def _make_synthetic_fits(path, shape=(128, 128), seed=42):
    rng = np.random.RandomState(seed)
    y, x = np.mgrid[0:shape[0], 0:shape[1]]
    data = 0.001 + 1e-4 * (x + y) / sum(shape)
    for cx, cy, amp in [(30, 40, 60), (90, 80, 90), (60, 100, 30)]:
        data += amp * np.exp(-((x - cx) ** 2 + (y - cy) ** 2) / 8.0)
    data += rng.normal(0, 1e-4, shape)
    fits.writeto(path, data.astype(np.float32), overwrite=True)


class TestGrayscalePipelineIntegration:
    def test_pipeline_produces_tiff(self, tmp_path):
        input_path = tmp_path / "input.fits"
        _make_synthetic_fits(str(input_path))
        output_base = str(tmp_path / "out")

        result = GrayscalePipeline(
            config=GrayscalePipelineConfig(
                normalization=NormalizationConfig(),
                ghs=GHSConfig(),
            ),
            input_path=str(input_path),
            output_base=output_base,
        ).run()

        assert result.grayscale_path.endswith("_grayscale.tif")
        loaded = tifffile.imread(result.grayscale_path)
        assert loaded.shape == (128, 128)
        assert loaded.dtype == np.float32
        assert np.all(np.isfinite(loaded))
        assert loaded.min() >= 0.0
        assert loaded.max() <= 1.0

    def test_pipeline_reports_window_and_shape(self, tmp_path):
        input_path = tmp_path / "input.fits"
        _make_synthetic_fits(str(input_path), shape=(64, 64))
        output_base = str(tmp_path / "out")

        result = GrayscalePipeline(
            input_path=str(input_path),
            output_base=output_base,
        ).run()

        assert len(result.window) == 2
        assert result.window[0] < result.window[1]
        assert result.shape == (64, 64)

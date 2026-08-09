"""Unit tests for the I/O layer (loaders, writers, validators)."""

from __future__ import annotations

import numpy as np
import pytest
import tifffile
from astropy.io import fits

from electpynasa.io.loaders import ImageLoader
from electpynasa.io.validators import (
    validate_image_path,
    validate_output_base,
    validate_three_channels,
)
from electpynasa.io.writers import OpenCVWriter, TIFFWriter
from electpynasa.utils.exceptions import (
    UnsupportedFormatError,
    ValidationError,
)


# ---------------------------------------------------------------------------
# Validators
# ---------------------------------------------------------------------------
class TestValidators:
    def test_validate_image_path_rejects_missing_file(self, tmp_path) -> None:
        with pytest.raises(ValidationError):
            validate_image_path(str(tmp_path / "nope.fits"))

    def test_validate_image_path_rejects_unknown_extension(self, tmp_path) -> None:
        p = tmp_path / "img.xyz"
        p.write_bytes(b"")
        with pytest.raises(UnsupportedFormatError):
            validate_image_path(str(p))

    def test_validate_image_path_scientific_only(self, tmp_path) -> None:
        p = tmp_path / "img.jpg"
        p.write_bytes(b"")
        with pytest.raises(UnsupportedFormatError):
            validate_image_path(str(p), scientific_only=True)

    def test_validate_three_channels(self, tmp_path) -> None:
        paths = []
        for name in ("r.fits", "g.fits", "b.fits"):
            p = tmp_path / name
            fits.writeto(str(p), np.zeros((4, 4), dtype=np.float32))
            paths.append(p)
        r, g, b = validate_three_channels(*(str(p) for p in paths))
        assert all(p.exists() for p in (r, g, b))

    def test_validate_output_base_accepts_string(self) -> None:
        out = validate_output_base("/tmp/some_base")
        assert str(out) == "/tmp/some_base"

    def test_validate_output_base_rejects_empty(self) -> None:
        with pytest.raises(ValidationError):
            validate_output_base("")


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------
class TestImageLoader:
    def test_load_fits_2d(self, tmp_path) -> None:
        p = tmp_path / "img.fits"
        data = np.random.rand(16, 16).astype(np.float32)
        fits.writeto(str(p), data)
        result = ImageLoader.load(str(p))
        assert result.data.shape == (16, 16)
        assert result.data.dtype == np.float64
        assert result.sanitized_pixels == 0

    def test_load_fits_with_nan_sanitizes(self, tmp_path) -> None:
        p = tmp_path / "img.fits"
        data = np.ones((8, 8), dtype=np.float32)
        data[0, 0] = np.nan
        data[1, 1] = np.inf
        fits.writeto(str(p), data)
        result = ImageLoader.load(str(p))
        assert result.sanitized_pixels == 2
        assert np.all(np.isfinite(result.data))

    def test_load_tiff(self, tmp_path) -> None:
        p = tmp_path / "img.tiff"
        data = (np.random.rand(8, 8) * 1000).astype(np.float32)
        tifffile.imwrite(str(p), data)
        result = ImageLoader.load(str(p))
        assert result.data.shape == (8, 8)

    def test_load_unsupported_extension_raises(self, tmp_path) -> None:
        p = tmp_path / "img.png"
        p.write_bytes(b"")
        with pytest.raises(UnsupportedFormatError):
            ImageLoader.load(str(p))

    def test_supports_detection(self) -> None:
        assert ImageLoader.supports("foo.fits") is True
        assert ImageLoader.supports("foo.FIT") is True
        assert ImageLoader.supports("foo.tiff") is True
        assert ImageLoader.supports("foo.png") is False


# ---------------------------------------------------------------------------
# Writers
# ---------------------------------------------------------------------------
class TestTIFFWriter:
    def test_write_grayscale_tiff(self, tmp_path) -> None:
        p = tmp_path / "out.tif"
        data = np.random.rand(8, 8).astype(np.float32)
        TIFFWriter.write(str(p), data, dtype="float32")
        loaded = tifffile.imread(str(p))
        assert loaded.shape == (8, 8)
        np.testing.assert_allclose(loaded, data, atol=1e-6)

    def test_write_rgb_tiff(self, tmp_path) -> None:
        p = tmp_path / "out.tif"
        data = np.random.rand(8, 8, 3).astype(np.float32)
        TIFFWriter.write(str(p), data, dtype="float32")
        loaded = tifffile.imread(str(p))
        assert loaded.shape == (8, 8, 3)


class TestOpenCVWriter:
    def test_write_rgb(self, tmp_path) -> None:
        p = tmp_path / "rgb.png"
        data = (np.random.rand(8, 8, 3) * 255).astype(np.uint8)
        OpenCVWriter.write_rgb(str(p), data)
        import cv2
        loaded = cv2.imread(str(p))
        assert loaded.shape == (8, 8, 3)

    def test_write_rgb_rejects_non_rgb(self, tmp_path) -> None:
        p = tmp_path / "rgb.png"
        data = np.zeros((8, 8), dtype=np.uint8)
        from electpynasa.utils.exceptions import IOError as EPNIOError
        with pytest.raises(EPNIOError):
            OpenCVWriter.write_rgb(str(p), data)

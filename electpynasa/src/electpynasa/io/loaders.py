"""
Image loaders for FITS and TIFF inputs.

The single :class:`ImageLoader` facade auto-detects the file extension and
delegates to a format-specific loader. Multi-dimensional inputs (e.g.
data-cubes) are projected to 2D via maximum-intensity projection. ``NaN`` and
``Inf`` values are replaced with the minimum finite value (or ``0`` if no
finite value exists) so downstream algorithms never have to deal with
non-finite pixels.
"""

from __future__ import annotations

from typing import Optional

import numpy as np

from electpynasa.core.types import LoaderResult
from electpynasa.utils.exceptions import CorruptDataError, UnsupportedFormatError
from electpynasa.utils.filesystem import normalize_extension
from electpynasa.utils.logging import ScientificLogger
from electpynasa.utils.sanity import finite_or_zero


class _FormatLoader:
    """Format-specific loader protocol (duck-typed, no ABC needed)."""

    @staticmethod
    def load(path: str) -> np.ndarray:  # pragma: no cover - interface only
        raise NotImplementedError


class FITSLoader(_FormatLoader):
    """Loader for Flexible Image Transport System (FITS) files."""

    @staticmethod
    def load(path: str) -> np.ndarray:
        from astropy.io import fits  # local import: heavy dependency
        try:
            with fits.open(path, memmap=True) as hdul:
                for idx, hdu in enumerate(hdul):
                    data = getattr(hdu, "data", None)
                    if isinstance(data, np.ndarray) and data.ndim >= 2:
                        ScientificLogger.info(
                            f"FITS HDU[{idx}] selected, shape={data.shape}, "
                            f"dtype={data.dtype}",
                            extra={"hdu_index": idx, "shape": list(data.shape)},
                        )
                        return data.astype(np.float64)
                raise CorruptDataError(
                    f"No 2D image data found in FITS file: {path}",
                    context={"path": path, "hdul_length": len(hdul)},
                )
        except CorruptDataError:
            raise
        except Exception as exc:
            raise CorruptDataError(
                f"Failed to decode FITS file at {path}: {exc}",
                context={"path": path, "error": str(exc)},
            ) from exc


class TIFFLoader(_FormatLoader):
    """Loader for scientific TIFF files (16/32-bit, multi-page)."""

    @staticmethod
    def load(path: str) -> np.ndarray:
        import tifffile  # local import: heavy dependency
        try:
            data = tifffile.imread(path)
        except Exception as exc:
            raise CorruptDataError(
                f"Failed to decode TIFF file at {path}: {exc}",
                context={"path": path, "error": str(exc)},
            ) from exc
        ScientificLogger.info(
            f"TIFF loaded, shape={data.shape}, dtype={data.dtype}",
            extra={"shape": list(data.shape), "dtype": str(data.dtype)},
        )
        return data.astype(np.float64)


class ImageLoader:
    """
    Facade that auto-detects the format and returns a 2D ``float64`` array.

    The facade guarantees the following post-conditions on the returned
    :class:`LoaderResult`:

    * ``data.ndim == 2`` (multi-page / data-cube inputs are projected to 2D
      via maximum-intensity projection);
    * ``data`` contains only finite values (``NaN`` / ``Inf`` are replaced
      with the minimum finite value or ``0``);
    * ``data.dtype == float64``.
    """

    _LOADERS = {
        ".fits": FITSLoader,
        ".fit": FITSLoader,
        ".tif": TIFFLoader,
        ".tiff": TIFFLoader,
    }

    @classmethod
    def supports(cls, path: str) -> bool:
        return normalize_extension(path) in cls._LOADERS

    @classmethod
    def load(cls, path: str) -> LoaderResult:
        """Load *path* and return a :class:`LoaderResult`."""
        ScientificLogger.info(f"Loading image: {path}")

        ext = normalize_extension(path)
        loader = cls._LOADERS.get(ext)
        if loader is None:
            raise UnsupportedFormatError(
                f"Unsupported extension {ext!r} for path {path}",
                context={"path": path, "extension": ext,
                         "supported": sorted(cls._LOADERS.keys())},
            )

        raw = loader.load(path)
        original_shape = tuple(raw.shape)

        projected = cls._project_to_2d(raw)
        sanitized, count = cls._sanitize(projected)

        ScientificLogger.info(
            f"Image ready: shape={sanitized.shape}, dtype={sanitized.dtype}, "
            f"sanitized_pixels={count}",
            extra={"shape": list(sanitized.shape),
                   "sanitized_pixels": count,
                   "original_shape": list(original_shape)},
        )
        return LoaderResult(
            data=sanitized,
            source_path=path,
            original_shape=original_shape,
            sanitized_pixels=count,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _project_to_2d(array: np.ndarray) -> np.ndarray:
        """Reduce N-D arrays to 2D via maximum-intensity projection."""
        if array.ndim == 2:
            return array
        ScientificLogger.warning(
            f"Input has {array.ndim} dimensions; projecting to 2D via "
            f"maximum-intensity projection along axis 0.",
            extra={"original_shape": list(array.shape)},
        )
        return np.max(array, axis=0)

    @staticmethod
    def _sanitize(array: np.ndarray) -> tuple[np.ndarray, int]:
        """Replace non-finite values with the minimum finite value (or 0)."""
        invalid_mask = ~np.isfinite(array)
        count = int(invalid_mask.sum())
        if count == 0:
            return array, 0

        finite_values = array[~invalid_mask]
        fill = float(np.min(finite_values)) if finite_values.size > 0 else 0.0
        out = array.copy()
        out[invalid_mask] = fill
        ScientificLogger.warning(
            f"Replaced {count} non-finite pixel(s) with {fill:.6f}",
            extra={"count": count, "fill_value": fill},
        )
        return out, count

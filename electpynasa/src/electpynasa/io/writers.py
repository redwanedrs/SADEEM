"""
Image writers used by the pipelines.

Two flavours are provided:

* :class:`TIFFWriter` — writes scientific HDR images (32-bit float, single
  page or multi-channel) via ``tifffile``.
* :class:`OpenCVWriter` — writes 8-bit display images (PNG/JPEG/TIFF) via
  OpenCV, with BGR conversion handled internally so callers always pass RGB.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

import numpy as np

from electpynasa.utils.exceptions import IOError as EPNIOError
from electpynasa.utils.filesystem import ensure_parent_dir, to_path
from electpynasa.utils.logging import ScientificLogger

PathLike = Union[str, Path]


class TIFFWriter:
    """Write scientific TIFF files (HDR, 32-bit float)."""

    @staticmethod
    def write(path: PathLike, data: np.ndarray, *,
              dtype: str = "float32") -> str:
        """
        Write *data* to *path* as a TIFF file.

        Parameters
        ----------
        path
            Destination file path.
        data
            ``float32``/``float64`` array, 2D (grayscale) or 3D ``(H, W, C)``.
        dtype
            Output dtype — one of ``float32`` (default), ``float64``, ``uint16``.
        """
        p = to_path(path)
        ensure_parent_dir(p)
        out = _cast(data, dtype)
        try:
            import tifffile
            tifffile.imwrite(str(p), out)
        except Exception as exc:
            raise EPNIOError(
                f"Failed to write TIFF file at {p}: {exc}",
                context={"path": str(p), "error": str(exc)},
            ) from exc
        ScientificLogger.info(
            f"TIFF written: {p} (shape={out.shape}, dtype={out.dtype})",
            extra={"path": str(p), "shape": list(out.shape), "dtype": str(out.dtype)},
        )
        return str(p)


class OpenCVWriter:
    """Write 8-bit display images (RGB → BGR handled internally)."""

    @staticmethod
    def write_rgb(path: PathLike, rgb: np.ndarray, *,
                  dtype: str = "uint8") -> str:
        """
        Write an RGB ``uint8`` image to *path*.

        OpenCV expects BGR ordering; the writer handles the conversion
        transparently so callers always pass RGB.
        """
        p = to_path(path)
        ensure_parent_dir(p)
        out = _cast(rgb, dtype)
        if out.ndim != 3 or out.shape[2] != 3:
            raise EPNIOError(
                f"OpenCV writer expects an RGB image (H, W, 3); got shape {out.shape}",
                context={"path": str(p), "shape": list(out.shape)},
            )

        try:
            import cv2
            bgr = cv2.cvtColor(out, cv2.COLOR_RGB2BGR)
            ok = cv2.imwrite(str(p), bgr)
            if not ok:
                raise RuntimeError("cv2.imwrite returned False")
        except Exception as exc:
            raise EPNIOError(
                f"Failed to write image at {p}: {exc}",
                context={"path": str(p), "error": str(exc)},
            ) from exc

        ScientificLogger.info(
            f"RGB image written: {p} (shape={out.shape}, dtype={out.dtype})",
            extra={"path": str(p), "shape": list(out.shape)},
        )
        return str(p)

    @staticmethod
    def write_gray(path: PathLike, gray: np.ndarray, *,
                   dtype: str = "uint8") -> str:
        """Write a single-channel image to *path*."""
        p = to_path(path)
        ensure_parent_dir(p)
        out = _cast(gray, dtype)
        try:
            import cv2
            ok = cv2.imwrite(str(p), out)
            if not ok:
                raise RuntimeError("cv2.imwrite returned False")
        except Exception as exc:
            raise EPNIOError(
                f"Failed to write grayscale image at {p}: {exc}",
                context={"path": str(p), "error": str(exc)},
            ) from exc
        ScientificLogger.info(
            f"Grayscale image written: {p} (shape={out.shape}, dtype={out.dtype})",
            extra={"path": str(p), "shape": list(out.shape)},
        )
        return str(p)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _cast(array: np.ndarray, dtype: str) -> np.ndarray:
    """Cast *array* to *dtype* (string alias → numpy dtype)."""
    mapping = {
        "float32": np.float32,
        "float64": np.float64,
        "uint8": np.uint8,
        "uint16": np.uint16,
    }
    if dtype not in mapping:
        raise ValueError(f"Unsupported dtype alias: {dtype!r}")
    return array.astype(mapping[dtype])

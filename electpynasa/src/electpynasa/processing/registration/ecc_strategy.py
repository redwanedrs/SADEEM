"""
OpenCV ECC (Enhanced Correlation Coefficient) registration.

ECC maximizes the correlation coefficient between the warped target and the
reference. It is robust to small shifts / rotations / affine distortions and
works well even when the number of point sources is too low for astroalign.
"""

from __future__ import annotations

import numpy as np

from electpynasa.config import ECCConfig
from electpynasa.core.interfaces import RegistrationStrategy
from electpynasa.core.types import GrayImage
from electpynasa.utils.exceptions import RegistrationError
from electpynasa.utils.logging import ScientificLogger

# Map config string → OpenCV motion type constant.
_MOTION_TYPES = {
    "translation": "MOTION_TRANSLATION",
    "euclidean": "MOTION_EUCLIDEAN",
    "affine": "MOTION_AFFINE",
    "homography": "MOTION_HOMOGRAPHY",
}


class ECCStrategy(RegistrationStrategy):
    """Register images using OpenCV's :func:`cv2.findTransformECC`."""

    name = "opencv-ecc"

    def __init__(self, config: ECCConfig | None = None) -> None:
        self._config = config or ECCConfig()

    @property
    def config(self) -> ECCConfig:
        return self._config

    def align(self, target: GrayImage, reference: GrayImage) -> GrayImage:
        try:
            import cv2
        except ImportError as exc:  # pragma: no cover - environment-dependent
            raise RegistrationError(
                "opencv-python is not installed",
                context={"error": str(exc)},
            ) from exc

        if reference.shape != target.shape:
            raise RegistrationError(
                "ECC strategy requires both images to share the same shape",
                context={"reference_shape": list(reference.shape),
                         "target_shape": list(target.shape)},
            )

        motion_attr = _MOTION_TYPES.get(self._config.motion_type.lower())
        if motion_attr is None:
            raise RegistrationError(
                f"Unknown motion type: {self._config.motion_type!r}",
                context={"motion_type": self._config.motion_type,
                         "valid": sorted(_MOTION_TYPES.keys())},
            )
        motion = getattr(cv2, motion_attr)

        ref_f = _to_float32(reference)
        tgt_f = _to_float32(target)

        warp_matrix = np.eye(2, 3, dtype=np.float32) if motion != cv2.MOTION_HOMOGRAPHY \
            else np.eye(3, 3, dtype=np.float32)

        criteria = (
            cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT,
            self._config.iterations,
            self._config.termination_eps,
        )

        try:
            # Pass positionally for maximum portability across OpenCV versions
            # (parameter names have changed across 4.x releases).
            _, warp_matrix = cv2.findTransformECC(
                ref_f, tgt_f, warp_matrix, motion, criteria,
            )
        except Exception as exc:
            raise RegistrationError(
                f"ECC alignment failed: {exc}",
                context={"error": str(exc)},
            ) from exc

        h, w = reference.shape[:2]
        if motion == cv2.MOTION_HOMOGRAPHY:
            aligned = cv2.warpPerspective(
                tgt_f, warp_matrix, (w, h),
                flags=cv2.INTER_CUBIC + cv2.WARP_INVERSE_MAP,
                borderMode=cv2.BORDER_REPLICATE,
            )
        else:
            aligned = cv2.warpAffine(
                tgt_f, warp_matrix, (w, h),
                flags=cv2.INTER_CUBIC + cv2.WARP_INVERSE_MAP,
                borderMode=cv2.BORDER_REPLICATE,
            )

        ScientificLogger.info(
            f"ECC alignment succeeded with motion_type={self._config.motion_type}",
            extra=self._config.to_dict(),
        )
        return aligned.astype(np.float64)


def _to_float32(image: GrayImage) -> np.ndarray:
    """Normalize to ``[0, 1]`` float32 (ECC requires a positive float image)."""
    arr = image.astype(np.float32)
    finite = arr[np.isfinite(arr)]
    if finite.size == 0:
        return arr
    vmin, vmax = float(finite.min()), float(finite.max())
    if vmax <= vmin:
        return np.zeros_like(arr)
    return (arr - vmin) / (vmax - vmin)

"""
OpenCV ORB feature-based registration.

ORB is the most generic strategy in the chain. It detects Oriented FAST
keypoints, computes BRIEF descriptors, matches them with a brute-force
Hamming matcher, and recovers a homography via RANSAC. It is useful when
both images lack well-distributed stellar point sources (e.g. dense nebular
fields) but still contain distinctive structural features.
"""

from __future__ import annotations

import numpy as np

from electpynasa.config import ORBConfig
from electpynasa.core.interfaces import RegistrationStrategy
from electpynasa.core.types import GrayImage
from electpynasa.utils.exceptions import RegistrationError
from electpynasa.utils.logging import ScientificLogger


class ORBStrategy(RegistrationStrategy):
    """Register images using ORB features + RANSAC homography."""

    name = "opencv-orb"

    def __init__(self, config: ORBConfig | None = None) -> None:
        self._config = config or ORBConfig()

    @property
    def config(self) -> ORBConfig:
        return self._config

    def align(self, target: GrayImage, reference: GrayImage) -> GrayImage:
        try:
            import cv2
        except ImportError as exc:  # pragma: no cover - environment-dependent
            raise RegistrationError(
                "opencv-python is not installed",
                context={"error": str(exc)},
            ) from exc

        ref_8 = _to_uint8(reference)
        tgt_8 = _to_uint8(target)

        orb = cv2.ORB_create(nfeatures=self._config.nfeatures)
        kp_ref, desc_ref = orb.detectAndCompute(ref_8, None)
        kp_tgt, desc_tgt = orb.detectAndCompute(tgt_8, None)

        if desc_ref is None or desc_tgt is None \
                or len(kp_ref) < self._config.min_matches \
                or len(kp_tgt) < self._config.min_matches:
            raise RegistrationError(
                "ORB could not find enough features",
                context={
                    "ref_keypoints": len(kp_ref) if kp_ref else 0,
                    "tgt_keypoints": len(kp_tgt) if kp_tgt else 0,
                    "required": self._config.min_matches,
                },
            )

        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        matches = sorted(bf.match(desc_ref, desc_tgt), key=lambda m: m.distance)
        if len(matches) < self._config.min_matches:
            raise RegistrationError(
                "ORB could not find enough matches after brute-force matching",
                context={"matches": len(matches),
                         "required": self._config.min_matches},
            )

        # Build correspondence arrays. Note the queryIdx/trainIdx split:
        # we matched ref → tgt, so src = ref keypoint, dst = tgt keypoint.
        src_pts = np.float32(
            [kp_ref[m.queryIdx].pt for m in matches]
        ).reshape(-1, 1, 2)
        dst_pts = np.float32(
            [kp_tgt[m.trainIdx].pt for m in matches]
        ).reshape(-1, 1, 2)

        H, status = cv2.findHomography(
            dst_pts, src_pts, cv2.RANSAC, self._config.ransac_threshold,
        )
        if H is None:
            raise RegistrationError(
                "RANSAC could not recover a valid homography",
                context={"matches": len(matches)},
            )

        inliers = int(np.sum(status)) if status is not None else 0
        h, w = reference.shape[:2]
        aligned = cv2.warpPerspective(
            target.astype(np.float32), H, (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE,
        )

        ScientificLogger.info(
            f"ORB alignment succeeded: matches={len(matches)}, inliers={inliers}",
            extra={"matches": len(matches), "inliers": inliers},
        )
        return aligned.astype(np.float64)


def _to_uint8(image: GrayImage) -> np.ndarray:
    """Normalize a float image to ``uint8`` for OpenCV feature detection."""
    arr = image.astype(np.float32)
    finite = arr[np.isfinite(arr)]
    if finite.size == 0:
        return np.zeros(arr.shape, dtype=np.uint8)
    vmin, vmax = float(finite.min()), float(finite.max())
    if vmax <= vmin:
        return np.zeros(arr.shape, dtype=np.uint8)
    norm = (arr - vmin) / (vmax - vmin)
    return np.clip(norm * 255.0, 0, 255).astype(np.uint8)

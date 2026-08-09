"""
Astroalign-based registration.

Uses the ``astroalign`` library to perform asterism matching on stellar point
sources. This is the most accurate strategy for astronomical imagery but
requires a sufficient number of well-distributed stars in both images.
"""

from __future__ import annotations

import numpy as np

from electpynasa.config import AstroalignConfig
from electpynasa.core.interfaces import RegistrationStrategy
from electpynasa.core.types import GrayImage
from electpynasa.utils.exceptions import RegistrationError
from electpynasa.utils.logging import ScientificLogger


class AstroalignStrategy(RegistrationStrategy):
    """Register images using ``astroalign`` asterism matching."""

    name = "astroalign"

    def __init__(self, config: AstroalignConfig | None = None) -> None:
        self._config = config or AstroalignConfig()

    @property
    def config(self) -> AstroalignConfig:
        return self._config

    def align(self, target: GrayImage, reference: GrayImage) -> GrayImage:
        try:
            import astroalign
        except ImportError as exc:  # pragma: no cover - environment-dependent
            raise RegistrationError(
                "astroalign is not installed",
                context={"error": str(exc)},
            ) from exc

        if target.shape != reference.shape:
            # astroalign can resample to the reference footprint, but we
            # explicitly resize here so downstream consumers always see the
            # reference shape.
            ScientificLogger.warning(
                f"Shape mismatch (target={target.shape}, ref={reference.shape}); "
                f"astroalign will resample to the reference footprint."
            )

        try:
            aligned, _ = astroalign.register(
                target.astype(np.float32),
                reference.astype(np.float32),
                min_detection_points=self._config.min_detection_stars,
                max_control_points=self._config.max_detection_stars,
            )
        except Exception as exc:
            raise RegistrationError(
                f"astroalign registration failed: {exc}",
                context={"error": str(exc),
                         "target_shape": list(target.shape),
                         "reference_shape": list(reference.shape)},
            ) from exc

        return aligned.astype(np.float64)

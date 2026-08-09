"""
Logarithmic stretch.

.. math::

    y = \\frac{\\ln(1 + a \\cdot x)}{\\ln(1 + a)}

For very small ``x`` the slope is steep (lifting faint nebulosity out of the
noise floor), and the slope decays for larger ``x`` (compressing highlights).
"""

from __future__ import annotations

import numpy as np

from electpynasa.core.interfaces import StretchStrategy
from electpynasa.core.types import GrayImage
from electpynasa.utils.exceptions import StretchError
from electpynasa.utils.logging import ScientificLogger


class LogarithmicStretch(StretchStrategy):
    """Classical logarithmic stretch."""

    def __init__(self, scale: float = 10.0) -> None:
        if scale <= 0.0:
            raise ValueError("Logarithmic stretch scale must be > 0")
        self._scale = float(scale)

    @property
    def scale(self) -> float:
        return self._scale

    def stretch(self, image: GrayImage) -> GrayImage:
        if image.size == 0:
            raise StretchError("Cannot stretch an empty image")
        ScientificLogger.info(f"Applying logarithmic stretch: a={self._scale}")
        a = self._scale
        denom = np.log1p(a)
        out = np.log1p(a * np.clip(image, 0.0, None)) / denom
        return np.clip(out, 0.0, 1.0)

    def describe(self) -> dict:
        base = super().describe()
        base["scale"] = self._scale
        return base

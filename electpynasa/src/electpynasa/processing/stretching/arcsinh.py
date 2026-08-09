"""
Lupton Arcsinh stretch.

Used both as a standalone stretch strategy and as the luminance engine inside
the :class:`~electpynasa.processing.balancing.lupton.LuptonBalancer`.

The mapping is:

.. math::

    y = \\frac{\\mathrm{asinh}(x / \\beta)}{\\mathrm{asinh}(1 / \\beta)}

* For ``x ≪ β`` the response is linear (preserving faint-star photometry).
* For ``x ≫ β`` the response is logarithmic (compressing bright regions).
"""

from __future__ import annotations

import numpy as np

from electpynasa.config import ArcsinhConfig
from electpynasa.core.interfaces import StretchStrategy
from electpynasa.core.types import GrayImage
from electpynasa.utils.exceptions import StretchError
from electpynasa.utils.logging import ScientificLogger


class ArcsinhStretch(StretchStrategy):
    """Arcsinh (Lupton) stretch."""

    def __init__(self, config: ArcsinhConfig | None = None) -> None:
        self._config = config or ArcsinhConfig()

    @property
    def config(self) -> ArcsinhConfig:
        return self._config

    def stretch(self, image: GrayImage) -> GrayImage:
        if image.size == 0:
            raise StretchError("Cannot stretch an empty image")
        beta = max(self._config.beta, 1e-6)
        ScientificLogger.info(
            f"Applying Arcsinh stretch: beta={beta}",
            extra=self._config.to_dict(),
        )
        denom = np.arcsinh(1.0 / beta)
        out = np.arcsinh(np.clip(image, 0.0, None) / beta) / denom
        return np.clip(out, 0.0, 1.0)

    def describe(self) -> dict:
        base = super().describe()
        base.update(self._config.to_dict())
        return base

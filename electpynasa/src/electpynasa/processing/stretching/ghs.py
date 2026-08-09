"""
Generalized Hyperbolic Stretch (GHS).

The GHS transformation maps a normalized intensity ``x ∈ [0, 1]`` to an
output intensity ``y ∈ [0, 1]`` using:

.. math::

    y = s + \\frac{k \\cdot (x - s)}{1 + L \\cdot |x - s|}

where:

* ``s`` is the symmetry point (input intensity that receives maximum stretch);
* ``k`` is the stretch factor (linear amplification at ``x = s``);
* ``L`` is the local stretch decay rate.

The derivative of the curve is:

.. math::

    \\frac{dy}{dx} = \\frac{k}{(1 + L \\cdot |x - s|)^2}

This shows that contrast peaks at ``x = s`` (slope = ``k``) and decays
quadratically as the input moves away from the symmetry point. The decay
naturally protects highlights and shadows from over-stretching, while the
symmetry point lets us target specific intensity ranges (e.g. faint
nebulosity just above the background sky level).
"""

from __future__ import annotations

import numpy as np

from electpynasa.config import GHSConfig
from electpynasa.core.interfaces import StretchStrategy
from electpynasa.core.types import GrayImage
from electpynasa.utils.exceptions import StretchError
from electpynasa.utils.logging import ScientificLogger


class GHSStretch(StretchStrategy):
    """Generalized Hyperbolic Stretch."""

    def __init__(self, config: GHSConfig | None = None) -> None:
        self._config = config or GHSConfig()

    @property
    def config(self) -> GHSConfig:
        return self._config

    def stretch(self, image: GrayImage) -> GrayImage:
        if image.size == 0:
            raise StretchError("Cannot stretch an empty image")
        cfg = self._config
        ScientificLogger.info(
            f"Applying GHS: k={cfg.k}, L={cfg.L}, s={cfg.s}",
            extra=cfg.to_dict(),
        )
        d = image - cfg.s
        denom = 1.0 + cfg.L * np.abs(d)
        y = cfg.s + cfg.k * d / denom
        # Numerical safety: GHS may overshoot [0, 1] slightly for extreme k/L
        return np.clip(y, 0.0, 1.0)

    def describe(self) -> dict:
        base = super().describe()
        base.update(self._config.to_dict())
        return base

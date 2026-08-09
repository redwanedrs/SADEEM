"""
Shadow / highlight protection.

Even with GHS, aggressively stretching low-intensity details can amplify
background noise and bloat bright stars. This module implements the two
protection mechanisms described in the reference guide:

**Shadow protection** (for ``x ≤ sp``):

.. math::

    w(x) = 1 - \\frac{x}{sp + \\epsilon}

    y_{prot} = w \\cdot \\gamma_{shadow} \\cdot x
               + (1 - w \\cdot \\gamma_{shadow}) \\cdot y

At ``x = 0`` the weight is ``1`` and the output collapses to a blend toward
the unstretched dark level, suppressing noise. As ``x`` approaches ``sp`` the
weight drops to ``0``, smoothly handing off to the full GHS stretch.

**Highlight compression** (for ``x ≥ hp``):

.. math::

    x_{rel} = \\frac{x - hp}{1 - hp + \\epsilon}

    \\text{attenuation}(x) = 1 - \\gamma_{high} \\cdot x_{rel}^{0.8}

    y_{prot} = s + (y - s) \\cdot \\text{attenuation}(x)

This is a soft knee that preserves gradient detail in bright star cores.
"""

from __future__ import annotations

import numpy as np

from electpynasa.config import GHSConfig
from electpynasa.core.interfaces import ProtectionStrategy
from electpynasa.core.types import GrayImage
from electpynasa.utils.exceptions import ProcessingError
from electpynasa.utils.logging import ScientificLogger


class ShadowHighlightProtector(ProtectionStrategy):
    """Protect shadows and highlights from over-stretching."""

    def __init__(self, config: GHSConfig | None = None) -> None:
        self._config = config or GHSConfig()

    @property
    def config(self) -> GHSConfig:
        return self._config

    def apply(self, original: GrayImage, stretched: GrayImage) -> GrayImage:
        if original.shape != stretched.shape:
            raise ProcessingError(
                "Protection requires original and stretched images to share shape",
                context={"original_shape": list(original.shape),
                         "stretched_shape": list(stretched.shape)},
            )

        cfg = self._config
        ScientificLogger.info(
            f"Applying protection: sp={cfg.shadow_protect}, hp={cfg.highlight_protect}, "
            f"shadow_blend={cfg.shadow_blend_strength}, "
            f"highlight_compress={cfg.highlight_compress_strength}",
            extra=cfg.to_dict(),
        )

        out = stretched.copy().astype(np.float64, copy=False)
        original = original.astype(np.float64, copy=False)

        # ----- Shadow protection zone -----
        if cfg.shadow_protect > 0.0:
            shadow_mask = original <= cfg.shadow_protect
            if np.any(shadow_mask):
                w = 1.0 - (original[shadow_mask] / (cfg.shadow_protect + 1e-12))
                blend = w * cfg.shadow_blend_strength
                out[shadow_mask] = (
                    blend * original[shadow_mask]
                    + (1.0 - blend) * stretched[shadow_mask]
                )

        # ----- Highlight compression zone -----
        if cfg.highlight_protect < 1.0:
            highlight_mask = original >= cfg.highlight_protect
            if np.any(highlight_mask):
                rel = (original[highlight_mask] - cfg.highlight_protect) / (
                    1.0 - cfg.highlight_protect + 1e-12
                )
                attenuation = 1.0 - cfg.highlight_compress_strength * (rel ** 0.8)
                s_pivot = cfg.s
                out[highlight_mask] = s_pivot + (out[highlight_mask] - s_pivot) * attenuation

        return np.clip(out, 0.0, 1.0)

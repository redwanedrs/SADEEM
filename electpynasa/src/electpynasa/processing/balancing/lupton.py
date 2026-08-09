"""
Lupton smart color balance.

Implements the three-step balancing pipeline described in the reference guide:

1. **Background neutralization** — for each channel, compute the median of
   pixels below the ``background_percentile`` and subtract it. This forces
   the empty-sky background of all three channels to a neutral black point.

2. **White-point calibration** — divide each channel by its
   ``white_point_percentile`` so that bright, non-saturated stellar sources
   integrate to neutral white.

3. **Luminance-preserving saturation (Lupton)** — compute the mean luminance
   ``V``, stretch it via ``arcsinh(Q · V) / Q``, then rescale every channel
   by ``V_stretched / V``. This preserves the original channel ratios
   (hence hue) while compressing the dynamic range and applying the
   saturation multiplier.
"""

from __future__ import annotations

import numpy as np

from electpynasa.config import BalancingConfig
from electpynasa.core.interfaces import BalancingStrategy
from electpynasa.core.types import GrayImage, RGBImage
from electpynasa.utils.exceptions import BalancingError
from electpynasa.utils.logging import ScientificLogger


class LuptonBalancer(BalancingStrategy):
    """Scientific-grade smart color balancer."""

    def __init__(self, config: BalancingConfig | None = None) -> None:
        self._config = config or BalancingConfig()

    @property
    def config(self) -> BalancingConfig:
        return self._config

    def balance(self, r: GrayImage, g: GrayImage, b: GrayImage) -> RGBImage:
        if not (r.shape == g.shape == b.shape):
            raise BalancingError(
                "All channels must share the same shape",
                context={"r": list(r.shape), "g": list(g.shape), "b": list(b.shape)},
            )
        ScientificLogger.info(
            "Starting smart color balance pipeline",
            extra=self._config.to_dict(),
        )

        channels = {
            "R": r.astype(np.float64, copy=False),
            "G": g.astype(np.float64, copy=False),
            "B": b.astype(np.float64, copy=False),
        }

        # ----- Step 1: Background neutralization -----
        neutralized = {}
        for name, ch in channels.items():
            cutoff = np.percentile(ch, self._config.background_percentile)
            low_pixels = ch[ch <= cutoff]
            offset = float(np.median(low_pixels)) if low_pixels.size > 0 else float(np.min(ch))
            neutralized[name] = np.maximum(ch - offset, 0.0)
            ScientificLogger.info(
                f"Background neutralization [{name}]: offset={offset:.6f}",
                extra={"channel": name, "offset": offset},
            )

        # ----- Step 2: White-point calibration -----
        scaled = {}
        for name, ch in neutralized.items():
            white = float(np.percentile(ch, self._config.white_point_percentile))
            if white <= 0.0:
                fallback = float(np.max(ch))
                white = fallback if fallback > 0.0 else 1.0
                ScientificLogger.warning(
                    f"White-point fallback for channel {name}: using max={white:.6f}",
                    extra={"channel": name, "white_point": white},
                )
            scaled[name] = ch / white
            ScientificLogger.info(
                f"White-point calibration [{name}]: white={white:.6f}",
                extra={"channel": name, "white_point": white},
            )

        rc, gc, bc = scaled["R"], scaled["G"], scaled["B"]

        # ----- Step 3: Lupton luminance-preserving saturation -----
        luminance = (rc + gc + bc) / 3.0
        epsilon = 1e-12

        q = self._config.non_linear_factor
        if q > 0.0:
            lum_stretched = np.arcsinh(q * np.maximum(luminance, 0.0)) / q
        else:
            lum_stretched = luminance

        ratio = lum_stretched / (luminance + epsilon)
        saturation = self._config.saturation

        r_bal = rc * ratio * saturation
        g_bal = gc * ratio * saturation
        b_bal = bc * ratio * saturation

        rgb = np.stack([r_bal, g_bal, b_bal], axis=-1)

        # ----- Global clip protection -----
        clip = float(np.percentile(rgb, self._config.global_clip_percentile))
        if clip > 0.0:
            rgb = rgb / clip
        rgb = np.clip(rgb, 0.0, 1.0)

        ScientificLogger.info(
            f"Smart color balance complete (saturation={saturation}, Q={q})",
            extra={"saturation": saturation, "Q": q, "clip": clip},
        )
        return (rgb * 255.0).astype(np.uint8)

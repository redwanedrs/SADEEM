"""
Percentile-based normalization.

The percentile normalizer projects an arbitrary-range image into ``[0, 1]``
using the *lower*-th and *upper*-th percentile as black/white points. This is
robust to hot pixels and cosmic ray hits, which would otherwise dominate a
plain ``min/max`` normalization.
"""

from __future__ import annotations

import numpy as np

from electpynasa.config import NormalizationConfig
from electpynasa.core.interfaces import NormalizationStrategy
from electpynasa.core.types import NormalizationResult, Window
from electpynasa.utils.exceptions import NormalizationError
from electpynasa.utils.logging import ScientificLogger
from electpynasa.utils.sanity import safe_percentile


class PercentileNormalizer(NormalizationStrategy):
    """Normalize an image to ``[0, 1]`` using percentile clipping."""

    def __init__(self, config: NormalizationConfig | None = None) -> None:
        self._config = config or NormalizationConfig()

    @property
    def config(self) -> NormalizationConfig:
        return self._config

    def normalize(self, image: np.ndarray) -> NormalizationResult:
        cfg = self._config
        ScientificLogger.info(
            f"Normalizing with percentiles [{cfg.lower_pct}, {cfg.upper_pct}]",
            extra=cfg.to_dict(),
        )

        if image.size == 0:
            raise NormalizationError("Cannot normalize an empty image")

        low = safe_percentile(image, cfg.lower_pct)
        high = safe_percentile(image, cfg.upper_pct)

        if high <= low:
            # Degenerate case: fall back to min/max of finite values
            finite = image[np.isfinite(image)]
            if finite.size == 0:
                raise NormalizationError("Image has no finite values")
            low = float(finite.min())
            high = float(finite.max())
            if high <= low:
                high = low + 1.0
            ScientificLogger.warning(
                f"Percentile window collapsed; falling back to min/max "
                f"[{low:.6f}, {high:.6f}]",
                extra={"low": low, "high": high},
            )

        window: Window = (low, high)
        ScientificLogger.info(
            f"Normalization window: low={low:.6f}, high={high:.6f}",
            extra={"low": low, "high": high},
        )

        norm = (image - low) / (high - low)
        norm = np.clip(norm, 0.0, 1.0)
        return NormalizationResult(data=norm, window=window)

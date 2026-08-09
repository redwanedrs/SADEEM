"""
Abstract base classes defining the strategy contracts used by ElectPyNasa.

Every concrete algorithm (GHS, arcsinh, percentile normalization,
shadow/highlight protection, astroalign, ECC, ORB, Lupton balance, …)
implements one of the interfaces declared here. This makes any algorithm
swappable at runtime without touching the pipelines that consume them.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

import numpy as np

from electpynasa.core.types import GrayImage, NormalizationResult, RGBImage, Window


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------
class NormalizationStrategy(ABC):
    """Project a high-dynamic-range image into a normalized ``[0, 1]`` range."""

    @abstractmethod
    def normalize(self, image: np.ndarray) -> NormalizationResult:
        """Return the normalized image and the ``(low, high)`` window used."""
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Stretching
# ---------------------------------------------------------------------------
class StretchStrategy(ABC):
    """Apply a non-linear stretch to a normalized ``[0, 1]`` image."""

    @abstractmethod
    def stretch(self, image: GrayImage) -> GrayImage:
        """Return the stretched image (same shape as input)."""
        raise NotImplementedError

    def describe(self) -> dict[str, Any]:
        """Return a serializable description of the strategy parameters."""
        return {"strategy": self.__class__.__name__}


# ---------------------------------------------------------------------------
# Protection
# ---------------------------------------------------------------------------
class ProtectionStrategy(ABC):
    """Modify a stretched image to protect shadows / highlights."""

    @abstractmethod
    def apply(self, original: GrayImage, stretched: GrayImage) -> GrayImage:
        """Return the protected image (same shape as input)."""
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------
class RegistrationStrategy(ABC):
    """Spatially align a *target* image to a *reference* image."""

    name: str = "abstract"

    @abstractmethod
    def align(self, target: GrayImage, reference: GrayImage) -> GrayImage:
        """Return the registered target image (same shape as reference)."""
        raise NotImplementedError

    def describe(self) -> dict[str, Any]:
        return {"strategy": self.__class__.__name__, "name": self.name}


class RegistrationChain:
    """
    Try a sequence of :class:`RegistrationStrategy` instances in order.

    The first strategy that succeeds wins. If every strategy fails the chain
    raises :class:`~electpynasa.utils.exceptions.RegistrationError` so the
    caller can decide whether to fall back to an unaligned channel.
    """

    def __init__(self, strategies: list[RegistrationStrategy]) -> None:
        if not strategies:
            raise ValueError("RegistrationChain requires at least one strategy")
        self._strategies = list(strategies)

    @property
    def strategies(self) -> list[RegistrationStrategy]:
        return list(self._strategies)

    def align(self, target: GrayImage, reference: GrayImage) -> GrayImage:
        from electpynasa.utils.exceptions import RegistrationError
        from electpynasa.utils.logging import ScientificLogger

        last_error: Optional[Exception] = None
        for strategy in self._strategies:
            try:
                ScientificLogger.info(
                    f"Attempting alignment via {strategy.name}...",
                    extra={"strategy": strategy.__class__.__name__},
                )
                aligned = strategy.align(target, reference)
                ScientificLogger.info(f"{strategy.name} alignment succeeded.")
                return aligned
            except Exception as exc:  # noqa: BLE001 - we want full chain info
                last_error = exc
                ScientificLogger.warning(
                    f"{strategy.name} alignment failed: {exc}",
                    extra={"strategy": strategy.__class__.__name__,
                           "error": str(exc)},
                )
        raise RegistrationError(
            "Every registration strategy failed",
            context={"last_error": str(last_error) if last_error else None},
        )


# ---------------------------------------------------------------------------
# Balancing
# ---------------------------------------------------------------------------
class BalancingStrategy(ABC):
    """Transform three aligned channels into a balanced 8-bit RGB image."""

    @abstractmethod
    def balance(self, r: GrayImage, g: GrayImage, b: GrayImage) -> RGBImage:
        """Return an 8-bit RGB image (shape ``(H, W, 3)``, dtype ``uint8``)."""
        raise NotImplementedError

"""Stretch strategies: GHS, Arcsinh (Lupton), Logarithmic."""

from electpynasa.processing.stretching.arcsinh import ArcsinhStretch
from electpynasa.processing.stretching.ghs import GHSStretch
from electpynasa.processing.stretching.logarithmic import LogarithmicStretch

__all__ = ["GHSStretch", "ArcsinhStretch", "LogarithmicStretch"]

"""
Configuration objects for every algorithm and pipeline in ElectPyNasa.

All configs are immutable dataclasses with built-in validation, sensible
defaults, and a ``to_dict()`` helper for serialization to the structured
logger.
"""

from electpynasa.config.settings import (
    ArcsinhConfig,
    AstroalignConfig,
    BalancingConfig,
    CompositePipelineConfig,
    ECCConfig,
    GHSConfig,
    GrayscalePipelineConfig,
    NormalizationConfig,
    ORBConfig,
    PyramidConfig,
    PyramidPipelineConfig,
)

__all__ = [
    "GHSConfig",
    "ArcsinhConfig",
    "NormalizationConfig",
    "AstroalignConfig",
    "ECCConfig",
    "ORBConfig",
    "BalancingConfig",
    "PyramidConfig",
    "GrayscalePipelineConfig",
    "CompositePipelineConfig",
    "PyramidPipelineConfig",
]

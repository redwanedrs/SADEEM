"""
Core abstractions: types, interfaces, and the pipeline orchestrator.

This sub-package is dependency-light (only numpy + the utils sub-package) so
that it can be imported without pulling in scientific I/O libraries.
"""

from electpynasa.core.interfaces import (
    BalancingStrategy,
    NormalizationStrategy,
    ProtectionStrategy,
    RegistrationChain,
    RegistrationStrategy,
    StretchStrategy,
)
from electpynasa.core.pipeline import Pipeline
from electpynasa.core.types import (
    Channel,
    CompositePipelineResult,
    GrayscalePipelineResult,
    GrayImage,
    LoaderResult,
    LogLevel,
    NormalizationResult,
    PyramidPipelineResult,
    RGBImage,
    StepOutcome,
    Window,
)

__all__ = [
    # Types
    "GrayImage",
    "RGBImage",
    "Window",
    "Channel",
    "LogLevel",
    "LoaderResult",
    "NormalizationResult",
    "GrayscalePipelineResult",
    "CompositePipelineResult",
    "PyramidPipelineResult",
    "StepOutcome",
    # Interfaces
    "NormalizationStrategy",
    "StretchStrategy",
    "ProtectionStrategy",
    "RegistrationStrategy",
    "RegistrationChain",
    "BalancingStrategy",
    # Orchestrator
    "Pipeline",
]

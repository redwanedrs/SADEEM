"""
High-level ElectPyNasa pipelines.

Each pipeline is a concrete :class:`~electpynasa.core.pipeline.Pipeline`
subclass that composes the lower-level strategies into a deterministic,
observable workflow.
"""

from electpynasa.pipelines.composite_pipeline import CompositePipeline
from electpynasa.pipelines.grayscale_pipeline import GrayscalePipeline
from electpynasa.pipelines.pyramid_pipeline import PyramidPipeline

__all__ = ["GrayscalePipeline", "CompositePipeline", "PyramidPipeline"]

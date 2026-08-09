"""
Grayscale GHS pipeline.

Loads a single FITS/TIFF image, applies percentile normalization, GHS
stretch, and shadow/highlight protection, and writes the result as a 32-bit
float TIFF.

Pipeline steps
--------------
1. **load**      — :class:`~electpynasa.io.loaders.ImageLoader`
2. **normalize** — :class:`~electpynasa.processing.normalization.PercentileNormalizer`
3. **stretch**   — :class:`~electpynasa.processing.stretching.GHSStretch`
4. **protect**   — :class:`~electpynasa.processing.protection.ShadowHighlightProtector`
5. **write**     — :class:`~electpynasa.io.writers.TIFFWriter`
"""

from __future__ import annotations

from typing import Optional

from electpynasa.config import GrayscalePipelineConfig
from electpynasa.core.pipeline import Pipeline
from electpynasa.core.types import GrayscalePipelineResult, StepOutcome
from electpynasa.io.loaders import ImageLoader
from electpynasa.io.validators import validate_image_path, validate_output_base
from electpynasa.io.writers import TIFFWriter
from electpynasa.processing.normalization import PercentileNormalizer
from electpynasa.processing.protection import ShadowHighlightProtector
from electpynasa.processing.stretching import GHSStretch
from electpynasa.utils.exceptions import ValidationError
from electpynasa.utils.logging import ScientificLogger


class GrayscalePipeline(Pipeline):
    """End-to-end grayscale GHS pipeline."""

    name = "grayscale-ghs"

    def __init__(self,
                 *,
                 config: Optional[GrayscalePipelineConfig] = None,
                 input_path: Optional[str] = None,
                 output_base: Optional[str] = None) -> None:
        super().__init__()
        self._config = config or GrayscalePipelineConfig()
        self._input_path = input_path
        self._output_base = output_base
        self.build()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run(self, context=None) -> GrayscalePipelineResult:
        ctx = dict(context or {})
        ctx["input_path"] = self._input_path
        ctx["output_base"] = self._output_base
        ctx["config"] = self._config.to_dict()
        result = super().run(ctx)
        return result["result"]

    # ------------------------------------------------------------------
    # Step registration
    # ------------------------------------------------------------------
    def build(self) -> None:
        self.add_step("validate", self._step_validate)
        self.add_step("load", self._step_load)
        self.add_step("normalize", self._step_normalize)
        self.add_step("stretch", self._step_stretch)
        self.add_step("protect", self._step_protect)
        self.add_step("write", self._step_write)

    # ------------------------------------------------------------------
    # Steps
    # ------------------------------------------------------------------
    def _step_validate(self, ctx: dict) -> StepOutcome:
        if not self._input_path:
            raise ValidationError("input_path is required")
        if not self._output_base:
            raise ValidationError("output_base is required")
        validate_image_path(self._input_path, scientific_only=True)
        validate_output_base(self._output_base)
        return StepOutcome(label="validate",
                           payload={"input_path": self._input_path,
                                    "output_base": self._output_base})

    def _step_load(self, ctx: dict) -> StepOutcome:
        loader_result = ImageLoader.load(self._input_path)
        ctx["raw"] = loader_result.data
        return StepOutcome(
            label="load",
            payload={"shape": list(loader_result.data.shape),
                     "sanitized_pixels": loader_result.sanitized_pixels},
        )

    def _step_normalize(self, ctx: dict) -> StepOutcome:
        result = PercentileNormalizer(self._config.normalization).normalize(ctx["raw"])
        ctx["normalized"] = result.data
        ctx["window"] = result.window
        return StepOutcome(
            label="normalize",
            payload={"window": list(result.window)},
        )

    def _step_stretch(self, ctx: dict) -> StepOutcome:
        stretched = GHSStretch(self._config.ghs).stretch(ctx["normalized"])
        ctx["stretched"] = stretched
        return StepOutcome(
            label="stretch",
            payload=self._config.ghs.to_dict(),
        )

    def _step_protect(self, ctx: dict) -> StepOutcome:
        protected = ShadowHighlightProtector(self._config.ghs).apply(
            ctx["normalized"], ctx["stretched"],
        )
        ctx["protected"] = protected
        return StepOutcome(label="protect")

    def _step_write(self, ctx: dict) -> StepOutcome:
        out_path = f"{self._output_base}_grayscale.tif"
        ScientificLogger.info(f"Writing grayscale output to {out_path}")
        TIFFWriter.write(out_path, ctx["protected"], dtype=self._config.output_dtype)
        result = GrayscalePipelineResult(
            grayscale_path=out_path,
            window=ctx["window"],
            shape=tuple(ctx["protected"].shape),
        )
        ctx["result"] = result
        ScientificLogger.success(out_path)
        return StepOutcome(label="write",
                           payload={"output_path": out_path})

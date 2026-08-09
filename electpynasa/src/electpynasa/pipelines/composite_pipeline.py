"""
Color composite pipeline.

Loads three FITS/TIFF channels (red / green / blue), applies percentile
normalization + GHS stretch + shadow/highlight protection to each, registers
the red and blue channels to the green reference, stacks them into a 32-bit
HDR TIFF, and finally balances the result into an 8-bit display preview.

Pipeline steps
--------------
1. **validate**   — input paths + extension check
2. **load**       — load R / G / B channels via :class:`ImageLoader`
3. **stretch**    — per-channel normalize → GHS → protect
4. **register**   — cascade astroalign → ECC → ORB for R and B (G is reference)
5. **write_hdr**  — write the 32-bit HDR master TIFF
6. **balance**    — :class:`LuptonBalancer` → 8-bit preview TIFF
"""

from __future__ import annotations

from typing import Optional

import numpy as np

from electpynasa.config import CompositePipelineConfig
from electpynasa.core.pipeline import Pipeline
from electpynasa.core.types import CompositePipelineResult, StepOutcome
from electpynasa.io.loaders import ImageLoader
from electpynasa.io.validators import validate_output_base, validate_three_channels
from electpynasa.io.writers import OpenCVWriter, TIFFWriter
from electpynasa.processing.balancing import LuptonBalancer
from electpynasa.processing.normalization import PercentileNormalizer
from electpynasa.processing.protection import ShadowHighlightProtector
from electpynasa.processing.registration import RegistrationChainBuilder
from electpynasa.processing.stretching import GHSStretch
from electpynasa.utils.exceptions import ValidationError
from electpynasa.utils.logging import ScientificLogger


class CompositePipeline(Pipeline):
    """End-to-end color composite pipeline."""

    name = "color-composite"

    def __init__(self,
                 *,
                 config: Optional[CompositePipelineConfig] = None,
                 red_path: Optional[str] = None,
                 green_path: Optional[str] = None,
                 blue_path: Optional[str] = None,
                 output_base: Optional[str] = None) -> None:
        super().__init__()
        self._config = config or CompositePipelineConfig()
        self._red_path = red_path
        self._green_path = green_path
        self._blue_path = blue_path
        self._output_base = output_base
        self.build()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run(self, context=None) -> CompositePipelineResult:
        ctx = dict(context or {})
        ctx["red_path"] = self._red_path
        ctx["green_path"] = self._green_path
        ctx["blue_path"] = self._blue_path
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
        self.add_step("stretch", self._step_stretch)
        self.add_step("register", self._step_register)
        self.add_step("write_hdr", self._step_write_hdr)
        self.add_step("balance", self._step_balance)

    # ------------------------------------------------------------------
    # Steps
    # ------------------------------------------------------------------
    def _step_validate(self, ctx: dict) -> StepOutcome:
        if not all([self._red_path, self._green_path, self._blue_path,
                    self._output_base]):
            raise ValidationError(
                "red_path, green_path, blue_path and output_base are all required",
            )
        validate_three_channels(self._red_path, self._green_path, self._blue_path)
        validate_output_base(self._output_base)
        return StepOutcome(label="validate")

    def _step_load(self, ctx: dict) -> StepOutcome:
        ctx["raw_red"] = ImageLoader.load(self._red_path).data
        ctx["raw_green"] = ImageLoader.load(self._green_path).data
        ctx["raw_blue"] = ImageLoader.load(self._blue_path).data
        ScientificLogger.info(
            "All three channels loaded.",
            extra={
                "red_shape": list(ctx["raw_red"].shape),
                "green_shape": list(ctx["raw_green"].shape),
                "blue_shape": list(ctx["raw_blue"].shape),
            },
        )
        return StepOutcome(label="load")

    def _step_stretch(self, ctx: dict) -> StepOutcome:
        normalizer = PercentileNormalizer(self._config.normalization)
        protector = ShadowHighlightProtector(self._config.ghs)
        ghs = GHSStretch(self._config.ghs)

        out = {}
        for name in ("red", "green", "blue"):
            raw = ctx[f"raw_{name}"]
            norm = normalizer.normalize(raw).data
            stretched = ghs.stretch(norm)
            protected = protector.apply(norm, stretched)
            out[name] = protected
            ScientificLogger.info(
                f"Channel {name} stretched and protected.",
                extra={"channel": name, "shape": list(protected.shape)},
            )

        ctx["stretched"] = out
        return StepOutcome(label="stretch")

    def _step_register(self, ctx: dict) -> StepOutcome:
        stretched = ctx["stretched"]
        reference = stretched["green"]

        chain = RegistrationChainBuilder.build_default()

        # Green is the reference. Red and Blue are aligned to it.
        aligned_red = self._align_or_fallback(chain, stretched["red"], reference, "red")
        aligned_blue = self._align_or_fallback(chain, stretched["blue"], reference, "blue")

        ctx["aligned"] = {
            "red": aligned_red,
            "green": reference,
            "blue": aligned_blue,
        }
        return StepOutcome(label="register")

    def _step_write_hdr(self, ctx: dict) -> StepOutcome:
        aligned = ctx["aligned"]
        rgb_hdr = _stack_rgb(aligned["red"], aligned["green"], aligned["blue"]).astype("float32")
        hdr_path = f"{self._output_base}_color_32bit.tiff"
        ScientificLogger.info(f"Writing 32-bit HDR master TIFF: {hdr_path}")
        TIFFWriter.write(hdr_path, rgb_hdr, dtype="float32")
        ctx["hdr_path"] = hdr_path
        ctx["shape"] = tuple(rgb_hdr.shape)
        return StepOutcome(label="write_hdr", payload={"hdr_path": hdr_path})

    def _step_balance(self, ctx: dict) -> StepOutcome:
        aligned = ctx["aligned"]
        preview_rgb = LuptonBalancer(self._config.balancing).balance(
            aligned["red"], aligned["green"], aligned["blue"],
        )
        preview_path = f"{self._output_base}_color_8bit_preview.tiff"
        ScientificLogger.info(f"Writing 8-bit display preview: {preview_path}")
        OpenCVWriter.write_rgb(preview_path, preview_rgb, dtype="uint8")

        result = CompositePipelineResult(
            hdr_path=ctx["hdr_path"],
            preview_path=preview_path,
            shape=ctx["shape"],
        )
        ctx["result"] = result
        ScientificLogger.success(preview_path)
        return StepOutcome(label="balance", payload={"preview_path": preview_path})

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _align_or_fallback(chain, target, reference, name: str):
        """Try to align *target*; if every strategy fails, fall back to *target*."""
        from electpynasa.utils.exceptions import RegistrationError
        from electpynasa.utils.logging import ScientificLogger

        try:
            return chain.align(target, reference)
        except RegistrationError as exc:
            ScientificLogger.warning(
                f"Every registration strategy failed for {name} channel. "
                f"Falling back to the unaligned channel. Reason: {exc}",
                extra={"channel": name, "error": str(exc)},
            )
            return target


def _stack_rgb(r, g, b):
    """Stack three single-channel arrays into an ``(H, W, 3)`` RGB array."""
    if not (r.shape == g.shape == b.shape):
        raise ValueError(
            f"Cannot stack channels with mismatched shapes: "
            f"r={r.shape}, g={g.shape}, b={b.shape}"
        )
    return np.stack([r, g, b], axis=-1)

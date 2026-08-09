"""
DZI pyramid pipeline.

Wraps the ``vips dzsave`` CLI to produce a multi-resolution Deep Zoom Image
(DZI) pyramid from a large input image (TIFF/JPEG/PNG/WebP). The pyramid is
emitted into a structured output directory and a ``.dzi`` manifest is
generated so that any OpenSeadragon / Leaflet-style viewer can consume it.
"""

from __future__ import annotations

import os
import subprocess
from typing import Optional

from electpynasa.config import PyramidPipelineConfig
from electpynasa.core.pipeline import Pipeline
from electpynasa.core.types import PyramidPipelineResult, StepOutcome
from electpynasa.io.validators import validate_image_path
from electpynasa.utils.exceptions import (
    PipelineStepError,
    ValidationError,
)
from electpynasa.utils.filesystem import ensure_directory_exists, to_path, which
from electpynasa.utils.logging import ScientificLogger


class PyramidPipeline(Pipeline):
    """End-to-end DZI pyramid pipeline (libvips)."""

    name = "dzi-pyramid"

    def __init__(self,
                 *,
                 config: Optional[PyramidPipelineConfig] = None,
                 input_path: Optional[str] = None,
                 output_dir: Optional[str] = None) -> None:
        super().__init__()
        self._config = config or PyramidPipelineConfig()
        self._input_path = input_path
        self._output_dir = output_dir
        self.build()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run(self, context=None) -> PyramidPipelineResult:
        ctx = dict(context or {})
        ctx["input_path"] = self._input_path
        ctx["output_dir"] = self._output_dir
        ctx["config"] = self._config.to_dict()
        result = super().run(ctx)
        return result["result"]

    # ------------------------------------------------------------------
    # Step registration
    # ------------------------------------------------------------------
    def build(self) -> None:
        self.add_step("validate", self._step_validate)
        self.add_step("check_vips", self._step_check_vips)
        self.add_step("prepare_output", self._step_prepare_output)
        self.add_step("run_dzsave", self._step_run_dzsave)
        self.add_step("finalize", self._step_finalize)

    # ------------------------------------------------------------------
    # Steps
    # ------------------------------------------------------------------
    def _step_validate(self, ctx: dict) -> StepOutcome:
        if not self._input_path:
            raise ValidationError("input_path is required")
        if not self._output_dir:
            raise ValidationError("output_dir is required")
        validate_image_path(self._input_path, scientific_only=False)
        return StepOutcome(label="validate")

    def _step_check_vips(self, ctx: dict) -> StepOutcome:
        if which("vips") is None:
            raise PipelineStepError(
                "check_vips",
                "The libvips CLI ('vips') was not found on PATH. "
                "Install libvips to enable pyramid generation.",
            )
        try:
            subprocess.run(
                ["vips", "--version"], check=True, capture_output=True, text=True,
            )
        except (subprocess.CalledProcessError, OSError) as exc:
            raise PipelineStepError(
                "check_vips",
                f"Failed to invoke 'vips --version': {exc}",
            ) from exc
        ScientificLogger.info("libvips CLI verified.")
        return StepOutcome(label="check_vips")

    def _step_prepare_output(self, ctx: dict) -> StepOutcome:
        base_name = to_path(self._input_path).stem
        image_output_dir = to_path(self._output_dir) / base_name
        image_output_dir.mkdir(parents=True, exist_ok=True)

        vips_output_path = image_output_dir / base_name
        cfg = self._config.pyramid
        if cfg.tile_format in ("jpeg", "webp"):
            vips_target = f"{vips_output_path}[Q={cfg.quality}]"
        else:
            vips_target = str(vips_output_path)

        ctx["base_name"] = base_name
        ctx["image_output_dir"] = str(image_output_dir)
        ctx["vips_target"] = vips_target
        ctx["dzi_path"] = f"{vips_output_path}.dzi"
        return StepOutcome(
            label="prepare_output",
            payload={"base_name": base_name,
                     "image_output_dir": str(image_output_dir)},
        )

    def _step_run_dzsave(self, ctx: dict) -> StepOutcome:
        cfg = self._config.pyramid
        command = [
            "vips", "dzsave",
            self._input_path,
            ctx["vips_target"],
            "--tile-size", str(cfg.tile_size),
            "--overlap", str(cfg.overlap),
            "--suffix", f".{cfg.tile_format}",
        ]
        ScientificLogger.info(f"Executing: {' '.join(command)}", extra=cfg.to_dict())

        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        # Stream stdout lines as informational logs
        for line in iter(process.stdout.readline, ""):
            stripped = line.strip()
            if stripped:
                ScientificLogger.info(f"[vips] {stripped}")
        process.stdout.close()

        stderr_output = process.stderr.read()
        process.stderr.close()
        return_code = process.wait()

        if return_code != 0:
            raise PipelineStepError(
                "run_dzsave",
                f"vips dzsave exited with code {return_code}. stderr: {stderr_output}",
                context={"return_code": return_code, "stderr": stderr_output},
            )
        return StepOutcome(label="run_dzsave")

    def _step_finalize(self, ctx: dict) -> StepOutcome:
        dzi_path = ctx["dzi_path"]
        if not os.path.exists(dzi_path):
            raise PipelineStepError(
                "finalize",
                f"DZI manifest was not created at expected path: {dzi_path}",
            )
        result = PyramidPipelineResult(
            dzi_path=dzi_path,
            tiles_directory=ctx["image_output_dir"],
            base_name=ctx["base_name"],
        )
        ctx["result"] = result
        ScientificLogger.success(dzi_path)
        return StepOutcome(label="finalize",
                           payload={"dzi_path": dzi_path})

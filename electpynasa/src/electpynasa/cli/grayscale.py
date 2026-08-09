"""
CLI entry point for the grayscale GHS pipeline.

Usage::

    python -m electpynasa.cli.grayscale \\
        --input path/to/image.fits \\
        --output path/to/output_base \\
        [--k 2.5] [--L 6.0] [--s 0.20] [--sp 0.01] [--hp 0.98]
"""

from __future__ import annotations

import argparse
import sys
from typing import Optional, Sequence

from electpynasa.cli.common import add_common_arguments, safe_main
from electpynasa.config import GHSConfig, GrayscalePipelineConfig, NormalizationConfig
from electpynasa.pipelines import GrayscalePipeline
from electpynasa.utils.logging import ScientificLogger


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="electpynasa-grayscale",
        description="Apply GHS stretch + shadow/highlight protection to a single FITS/TIFF image.",
    )
    parser.add_argument("--input", required=True, help="Path to the input FITS or TIFF image.")
    parser.add_argument("--output", required=True, help="Output base path (suffixes are appended automatically).")
    parser.add_argument("--k", type=float, default=GHSConfig().k, help="GHS stretch factor.")
    parser.add_argument("--L", type=float, default=GHSConfig().L, help="GHS local stretch decay rate.")
    parser.add_argument("--s", type=float, default=GHSConfig().s, help="GHS symmetry point.")
    parser.add_argument("--sp", type=float, default=GHSConfig().shadow_protect, help="Shadow protection threshold.")
    parser.add_argument("--hp", type=float, default=GHSConfig().highlight_protect, help="Highlight protection threshold.")
    parser.add_argument("--lower-pct", type=float, default=NormalizationConfig().lower_pct, help="Normalization lower percentile.")
    parser.add_argument("--upper-pct", type=float, default=NormalizationConfig().upper_pct, help="Normalization upper percentile.")
    add_common_arguments(parser)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    config = GrayscalePipelineConfig(
        normalization=NormalizationConfig(
            lower_pct=args.lower_pct, upper_pct=args.upper_pct,
        ),
        ghs=GHSConfig(
            k=args.k, L=args.L, s=args.s,
            shadow_protect=args.sp, highlight_protect=args.hp,
        ),
    )

    pipeline = GrayscalePipeline(
        config=config,
        input_path=args.input,
        output_base=args.output,
    )
    pipeline.run()
    ScientificLogger.info("CLI finished successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(safe_main(main))

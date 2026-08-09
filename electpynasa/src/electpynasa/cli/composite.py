"""
CLI entry point for the color composite pipeline.

Usage::

    python -m electpynasa.cli.composite \\
        --r red.fits --g green.fits --b blue.fits \\
        --output path/to/output_base
"""

from __future__ import annotations

import argparse
import sys
from typing import Optional, Sequence

from electpynasa.cli.common import add_common_arguments, safe_main
from electpynasa.config import (
    BalancingConfig,
    CompositePipelineConfig,
    GHSConfig,
    NormalizationConfig,
)
from electpynasa.pipelines import CompositePipeline
from electpynasa.utils.logging import ScientificLogger


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="electpynasa-composite",
        description="Build an aligned, color-balanced RGB composite from three FITS/TIFF channels.",
    )
    parser.add_argument("--r", required=True, dest="red", help="Path to the RED channel image.")
    parser.add_argument("--g", required=True, dest="green", help="Path to the GREEN channel image.")
    parser.add_argument("--b", required=True, dest="blue", help="Path to the BLUE channel image.")
    parser.add_argument("--output", required=True, help="Output base path (suffixes are appended automatically).")
    parser.add_argument("--k", type=float, default=GHSConfig().k, help="GHS stretch factor.")
    parser.add_argument("--L", type=float, default=GHSConfig().L, help="GHS local stretch decay rate.")
    parser.add_argument("--s", type=float, default=GHSConfig().s, help="GHS symmetry point.")
    parser.add_argument("--saturation", type=float, default=BalancingConfig().saturation, help="Color saturation multiplier.")
    parser.add_argument("--q", type=float, default=BalancingConfig().non_linear_factor, help="Lupton Q factor.")
    add_common_arguments(parser)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    config = CompositePipelineConfig(
        normalization=NormalizationConfig(),
        ghs=GHSConfig(k=args.k, L=args.L, s=args.s),
        balancing=BalancingConfig(saturation=args.saturation, non_linear_factor=args.q),
    )

    pipeline = CompositePipeline(
        config=config,
        red_path=args.red,
        green_path=args.green,
        blue_path=args.blue,
        output_base=args.output,
    )
    pipeline.run()
    ScientificLogger.info("CLI finished successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(safe_main(main))

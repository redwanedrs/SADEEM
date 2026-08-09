"""
CLI entry point for the DZI pyramid pipeline.

Usage::

    python -m electpynasa.cli.pyramid \\
        --input path/to/image.tif \\
        --output path/to/output_dir \\
        [--tileSize 256] [--overlap 1] [--format jpeg] [--quality 90]
"""

from __future__ import annotations

import argparse
import sys
from typing import Optional, Sequence

from electpynasa.cli.common import add_common_arguments, safe_main
from electpynasa.config import PyramidConfig, PyramidPipelineConfig
from electpynasa.pipelines import PyramidPipeline
from electpynasa.utils.logging import ScientificLogger


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="electpynasa-pyramid",
        description="Build a Deep Zoom Image (DZI) pyramid from a large TIFF/JPEG/PNG/WebP image.",
    )
    parser.add_argument("--input", required=True, help="Path to the input image.")
    parser.add_argument("--output", required=True, help="Output directory (an image-named subdirectory is created inside).")
    parser.add_argument("--tileSize", type=int, default=PyramidConfig().tile_size, help="Tile size in pixels.")
    parser.add_argument("--overlap", type=int, default=PyramidConfig().overlap, help="Tile overlap in pixels.")
    parser.add_argument("--format", default=PyramidConfig().tile_format,
                        choices=["jpeg", "png", "webp"], help="Tile format.")
    parser.add_argument("--quality", type=int, default=PyramidConfig().quality, help="JPEG/WebP quality (1-100).")
    add_common_arguments(parser)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    config = PyramidPipelineConfig(
        pyramid=PyramidConfig(
            tile_size=args.tileSize,
            overlap=args.overlap,
            tile_format=args.format,
            quality=args.quality,
        ),
    )

    pipeline = PyramidPipeline(
        config=config,
        input_path=args.input,
        output_dir=args.output,
    )
    pipeline.run()
    ScientificLogger.info("CLI finished successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(safe_main(main))

"""
Configuration dataclasses for every algorithm in ElectPyNasa.

Each config is a frozen dataclass so configurations are hashable, immutable
and trivially serializable. Defaults follow the values recommended in the
*Transforming Raw Deep-Space Telescopic Data* reference guide.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


# ---------------------------------------------------------------------------
# GHS / stretch configs
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class GHSConfig:
    """Configuration for the Generalized Hyperbolic Stretch."""

    #: Stretch factor — linear amplification at the symmetry point.
    k: float = 2.5
    #: Local stretch decay rate — controls how fast contrast decays away
    #: from the symmetry point.
    L: float = 6.0
    #: Symmetry point — the input intensity that receives maximum stretch.
    s: float = 0.20
    #: Shadow protection threshold (input intensities below ``sp`` are blended
    #: back toward their linear value to suppress noise amplification).
    shadow_protect: float = 0.01
    #: Highlight compression threshold (input intensities above ``hp`` are
    #: softly compressed to prevent star bloat).
    highlight_protect: float = 0.98
    #: Strength of the shadow blend (``0`` = no protection, ``1`` = full).
    shadow_blend_strength: float = 0.90
    #: Strength of the highlight compression (``0`` = no compression,
    #: ``1`` = full).
    highlight_compress_strength: float = 0.92

    def __post_init__(self) -> None:
        if not 0.0 < self.s <= 1.0:
            raise ValueError("GHSConfig.s must be in (0, 1]")
        if self.k <= 0.0:
            raise ValueError("GHSConfig.k must be > 0")
        if self.L < 0.0:
            raise ValueError("GHSConfig.L must be >= 0")
        if not 0.0 <= self.shadow_protect <= 0.5:
            raise ValueError("GHSConfig.shadow_protect must be in [0, 0.5]")
        if not 0.5 <= self.highlight_protect <= 1.0:
            raise ValueError("GHSConfig.highlight_protect must be in [0.5, 1.0]")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ArcsinhConfig:
    """Configuration for the Lupton arcsinh stretch."""

    #: Softening parameter — controls the linear-to-log transition.
    beta: float = 0.15
    #: Saturation multiplier.
    saturation: float = 1.25

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class NormalizationConfig:
    """Configuration for percentile-based normalization."""

    lower_pct: float = 0.5
    upper_pct: float = 99.5

    def __post_init__(self) -> None:
        if not 0.0 <= self.lower_pct < self.upper_pct <= 100.0:
            raise ValueError(
                "NormalizationConfig requires 0 <= lower_pct < upper_pct <= 100"
            )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class AstroalignConfig:
    """Configuration for the astroalign registration strategy."""

    min_detection_stars: int = 50
    max_detection_stars: int = 200

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ECCConfig:
    """Configuration for the OpenCV ECC registration strategy."""

    motion_type: str = "affine"  # one of: translation, euclidean, affine, homography
    iterations: int = 60
    termination_eps: float = 1e-7

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ORBConfig:
    """Configuration for the OpenCV ORB registration strategy."""

    nfeatures: int = 3000
    ransac_threshold: float = 5.0
    min_matches: int = 8

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Color balancing
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class BalancingConfig:
    """Configuration for the Lupton smart color balance."""

    saturation: float = 1.35
    non_linear_factor: float = 7.5
    background_percentile: float = 10.0
    white_point_percentile: float = 99.9
    global_clip_percentile: float = 99.95

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Pyramid (DZI)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class PyramidConfig:
    """Configuration for DZI pyramid generation via libvips."""

    tile_size: int = 256
    overlap: int = 1
    tile_format: str = "jpeg"
    quality: int = 90

    def __post_init__(self) -> None:
        if self.tile_size <= 0:
            raise ValueError("PyramidConfig.tile_size must be > 0")
        if self.overlap < 0:
            raise ValueError("PyramidConfig.overlap must be >= 0")
        if self.tile_format not in ("jpeg", "png", "webp"):
            raise ValueError(
                f"PyramidConfig.tile_format must be one of jpeg/png/webp, "
                f"got {self.tile_format!r}"
            )
        if not 1 <= self.quality <= 100:
            raise ValueError("PyramidConfig.quality must be in [1, 100]")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Pipeline-level config
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class GrayscalePipelineConfig:
    """Top-level config for the grayscale GHS pipeline."""

    normalization: NormalizationConfig = field(default_factory=NormalizationConfig)
    ghs: GHSConfig = field(default_factory=GHSConfig)
    output_dtype: str = "float32"  # float32 | float64 | uint16

    def to_dict(self) -> dict[str, Any]:
        return {
            "normalization": self.normalization.to_dict(),
            "ghs": self.ghs.to_dict(),
            "output_dtype": self.output_dtype,
        }


@dataclass(frozen=True)
class CompositePipelineConfig:
    """Top-level config for the color composite pipeline."""

    normalization: NormalizationConfig = field(default_factory=NormalizationConfig)
    ghs: GHSConfig = field(default_factory=GHSConfig)
    balancing: BalancingConfig = field(default_factory=BalancingConfig)

    def to_dict(self) -> dict[str, Any]:
        return {
            "normalization": self.normalization.to_dict(),
            "ghs": self.ghs.to_dict(),
            "balancing": self.balancing.to_dict(),
        }


@dataclass(frozen=True)
class PyramidPipelineConfig:
    """Top-level config for the DZI pyramid pipeline."""

    pyramid: PyramidConfig = field(default_factory=PyramidConfig)

    def to_dict(self) -> dict[str, Any]:
        return {"pyramid": self.pyramid.to_dict()}

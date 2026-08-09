"""
Format validators for incoming image files.

Validators run *before* any heavy I/O — they reject obviously invalid inputs
fast and with precise error categories so the UI can show actionable
messages.
"""

from __future__ import annotations

from pathlib import Path

from electpynasa.utils.exceptions import UnsupportedFormatError, ValidationError
from electpynasa.utils.filesystem import (
    SCIENTIFIC_IMAGE_EXTENSIONS,
    SUPPORTED_IMAGE_EXTENSIONS,
    ensure_file_exists,
    normalize_extension,
    to_path,
)


def validate_image_path(path: str, *, scientific_only: bool = False) -> Path:
    """
    Validate that *path* exists and has a supported image extension.

    Parameters
    ----------
    path
        Filesystem path to inspect.
    scientific_only
        If ``True`` only FITS/TIFF extensions are accepted (used by the
        grayscale / composite pipelines). If ``False`` (default) any image
        extension is accepted (used by the pyramid tiler).
    """
    if not path or not isinstance(path, str):
        raise ValidationError("Image path must be a non-empty string",
                              context={"path": path})

    p = ensure_file_exists(path, label="input image")
    ext = normalize_extension(p)

    allowed = SCIENTIFIC_IMAGE_EXTENSIONS if scientific_only else SUPPORTED_IMAGE_EXTENSIONS
    if ext not in allowed:
        raise UnsupportedFormatError(
            f"Unsupported extension {ext!r} for path {p}. "
            f"Allowed: {sorted(allowed)}",
            context={"path": str(p), "extension": ext,
                     "allowed": sorted(allowed)},
        )
    return p


def validate_three_channels(red: str, green: str, blue: str) -> tuple[Path, Path, Path]:
    """Validate three channel paths for the composite pipeline (scientific)."""
    r = validate_image_path(red, scientific_only=True)
    g = validate_image_path(green, scientific_only=True)
    b = validate_image_path(blue, scientific_only=True)
    return r, g, b


def validate_output_base(output_base: str) -> Path:
    """Validate an output base path (must be writable, parent must be creatable)."""
    if not output_base or not isinstance(output_base, str):
        raise ValidationError("Output base must be a non-empty string",
                              context={"output_base": output_base})
    return to_path(output_base)

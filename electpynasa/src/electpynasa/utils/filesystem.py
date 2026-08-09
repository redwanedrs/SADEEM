"""
Filesystem helpers used across ElectPyNasa.

The helpers centralise all path manipulation so that the rest of the codebase
can stay purely declarative. Every helper is side-effect free except the ones
whose name starts with ``ensure_`` / ``write_``.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Iterable, Optional, Union

from electpynasa.utils.exceptions import ValidationError

PathLike = Union[str, os.PathLike, Path]

#: All file extensions ElectPyNasa knows how to ingest.
SUPPORTED_IMAGE_EXTENSIONS: frozenset[str] = frozenset({
    ".fits", ".fit", ".tif", ".tiff", ".jpg", ".jpeg", ".png", ".webp",
})

#: Scientific formats (16/32-bit) that the loader can ingest.
SCIENTIFIC_IMAGE_EXTENSIONS: frozenset[str] = frozenset({
    ".fits", ".fit", ".tif", ".tiff",
})

#: Output formats supported by the DZI pyramid generator.
PYRAMID_FORMATS: tuple[str, ...] = ("jpeg", "png", "webp")


# ---------------------------------------------------------------------------
# Path normalization
# ---------------------------------------------------------------------------
def to_path(value: PathLike) -> Path:
    """Convert any path-like object into a normalized :class:`Path`."""
    if isinstance(value, Path):
        return value
    return Path(value).expanduser()


def normalize_extension(path: PathLike) -> str:
    """Return the lower-cased extension (including the leading dot)."""
    return to_path(path).suffix.lower()


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def ensure_file_exists(path: PathLike, *, label: str = "file") -> Path:
    """Validate that *path* exists and is a regular file."""
    p = to_path(path)
    if not p.exists():
        raise ValidationError(
            f"The {label} does not exist: {p}",
            context={"path": str(p), "label": label},
        )
    if not p.is_file():
        raise ValidationError(
            f"The {label} is not a regular file: {p}",
            context={"path": str(p), "label": label},
        )
    return p


def ensure_directory_exists(path: PathLike, *, label: str = "directory") -> Path:
    """Validate that *path* exists and is a directory."""
    p = to_path(path)
    if not p.exists():
        raise ValidationError(
            f"The {label} does not exist: {p}",
            context={"path": str(p), "label": label},
        )
    if not p.is_dir():
        raise ValidationError(
            f"The {label} is not a directory: {p}",
            context={"path": str(p), "label": label},
        )
    return p


def ensure_parent_dir(path: PathLike) -> Path:
    """Create the parent directory of *path* if needed and return it."""
    p = to_path(path)
    parent = p.parent
    parent.mkdir(parents=True, exist_ok=True)
    return parent


# ---------------------------------------------------------------------------
# Discovery helpers
# ---------------------------------------------------------------------------
def which(executable: str) -> Optional[str]:
    """Return the absolute path to *executable* if present on ``$PATH``."""
    return shutil.which(executable)


def iter_files(directory: PathLike, *, extensions: Iterable[str]) -> list[Path]:
    """Return a sorted list of files in *directory* matching *extensions*."""
    ext_set = {e.lower() for e in extensions}
    root = ensure_directory_exists(directory)
    return sorted(
        p for p in root.iterdir()
        if p.is_file() and p.suffix.lower() in ext_set
    )


# ---------------------------------------------------------------------------
# Output base builders
# ---------------------------------------------------------------------------
def build_output_base(input_path: PathLike, suffix: str,
                      output_dir: Optional[PathLike] = None) -> Path:
    """
    Build an *output base* path for a given input image.

    The output base is the stem onto which pipelines append suffixes such as
    ``_grayscale.tif`` or ``_color_8bit_preview.tiff``. If *output_dir* is
    ``None`` the base is emitted next to the input file, otherwise inside the
    given directory (which is created if necessary).
    """
    src = to_path(input_path)
    stem = src.stem
    target_dir = to_path(output_dir) if output_dir else src.parent
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir / f"{stem}{suffix}"

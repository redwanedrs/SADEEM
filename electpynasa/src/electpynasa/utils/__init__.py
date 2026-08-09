"""Utility sub-package: logging, exceptions, filesystem, numerical sanity."""

from electpynasa.utils.exceptions import (
    BalancingError,
    ConfigurationError,
    CorruptDataError,
    ElectPyNasaError,
    IOError as EPNIOError,
    NormalizationError,
    PipelineError,
    PipelineStepError,
    ProcessingError,
    RegistrationError,
    StretchError,
    UnsupportedFormatError,
    ValidationError,
)
from electpynasa.utils.filesystem import (
    PYRAMID_FORMATS,
    SCIENTIFIC_IMAGE_EXTENSIONS,
    SUPPORTED_IMAGE_EXTENSIONS,
    build_output_base,
    ensure_directory_exists,
    ensure_file_exists,
    ensure_parent_dir,
    iter_files,
    normalize_extension,
    to_path,
    which,
)
from electpynasa.utils.logging import ScientificLogger
from electpynasa.utils.sanity import (
    finite_or_zero,
    require_2d,
    require_range,
    require_same_shape,
    safe_minmax,
    safe_percentile,
)

__all__ = [
    # Exceptions
    "ElectPyNasaError",
    "EPNIOError",
    "UnsupportedFormatError",
    "CorruptDataError",
    "ConfigurationError",
    "ValidationError",
    "ProcessingError",
    "NormalizationError",
    "StretchError",
    "RegistrationError",
    "BalancingError",
    "PipelineError",
    "PipelineStepError",
    # Logger
    "ScientificLogger",
    # Filesystem
    "to_path",
    "normalize_extension",
    "ensure_file_exists",
    "ensure_directory_exists",
    "ensure_parent_dir",
    "which",
    "iter_files",
    "build_output_base",
    "SUPPORTED_IMAGE_EXTENSIONS",
    "SCIENTIFIC_IMAGE_EXTENSIONS",
    "PYRAMID_FORMATS",
    # Sanity
    "require_2d",
    "require_same_shape",
    "require_range",
    "finite_or_zero",
    "safe_percentile",
    "safe_minmax",
]

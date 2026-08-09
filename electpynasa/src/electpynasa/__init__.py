"""
ElectPyNasa
===========

A professional, modular astronomical image processing library for transforming
raw deep-space telescopic data (FITS / TIFF) into scientifically accurate,
display-ready visualizations.

The package is organized around four core principles:

1. **Separation of concerns** — I/O, algorithms, pipelines, and presentation
   are strictly isolated in dedicated sub-packages.
2. **Strategy pattern** — every processing step (stretching, registration,
   balancing) is a swappable strategy behind a stable interface.
3. **Pipeline orchestration** — high-level pipelines compose low-level
   strategies into reproducible workflows.
4. **Observability first** — structured JSON logging flows through every
   layer, enabling both human-friendly consoles and machine-parsable IPC.

Public API
----------
Modules:
    electpynasa.core         — interfaces, types, exceptions, pipeline base
    electpynasa.io           — loaders, writers, validators
    electpynasa.processing   — stretching, normalization, protection,
                               registration, balancing strategies
    electpynasa.pipelines    — high-level grayscale, composite, pyramid
                               pipelines
    electpynasa.utils        — logging, filesystem, sanity helpers

Example
-------
>>> from electpynasa.pipelines import GrayscalePipeline
>>> from electpynasa.config import GHSConfig
>>> result = GrayscalePipeline(config=GHSConfig()).run("input.fits", "out_base")
"""

from electpynasa.__version__ import __version__
from electpynasa.utils.exceptions import (
    ElectPyNasaError,
    IOError as EPNIOError,
    ProcessingError,
    ConfigurationError,
    RegistrationError,
    ValidationError,
)

__all__ = [
    "__version__",
    "ElectPyNasaError",
    "EPNIOError",
    "ProcessingError",
    "ConfigurationError",
    "RegistrationError",
    "ValidationError",
]

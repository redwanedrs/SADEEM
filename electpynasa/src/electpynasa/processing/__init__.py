"""
Processing sub-package.

Aggregates every concrete algorithm:

* :mod:`electpynasa.processing.normalization`  — percentile normalization
* :mod:`electpynasa.processing.stretching`     — GHS, arcsinh, log stretches
* :mod:`electpynasa.processing.protection`     — shadow/highlight protection
* :mod:`electpynasa.processing.registration`   — astroalign / ECC / ORB chain
* :mod:`electpynasa.processing.balancing`      — Lupton smart color balance
"""

from electpynasa.processing.balancing import LuptonBalancer
from electpynasa.processing.normalization import PercentileNormalizer
from electpynasa.processing.protection import ShadowHighlightProtector
from electpynasa.processing.registration import (
    AstroalignStrategy,
    ECCStrategy,
    ORBStrategy,
    RegistrationChainBuilder,
)
from electpynasa.processing.stretching import (
    ArcsinhStretch,
    GHSStretch,
    LogarithmicStretch,
)

__all__ = [
    # Normalization
    "PercentileNormalizer",
    # Stretching
    "GHSStretch",
    "ArcsinhStretch",
    "LogarithmicStretch",
    # Protection
    "ShadowHighlightProtector",
    # Registration
    "AstroalignStrategy",
    "ECCStrategy",
    "ORBStrategy",
    "RegistrationChainBuilder",
    # Balancing
    "LuptonBalancer",
]

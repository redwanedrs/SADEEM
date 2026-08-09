"""Registration strategies: Astroalign → ECC → ORB (cascading fallback)."""

from electpynasa.processing.registration.astroalign_strategy import AstroalignStrategy
from electpynasa.processing.registration.base import RegistrationChainBuilder
from electpynasa.processing.registration.ecc_strategy import ECCStrategy
from electpynasa.processing.registration.orb_strategy import ORBStrategy

__all__ = [
    "AstroalignStrategy",
    "ECCStrategy",
    "ORBStrategy",
    "RegistrationChainBuilder",
]

"""
Helpers to build a sensible default registration chain.

The default chain tries the most accurate strategy first (astroalign —
asterism matching on stellar point sources) and falls back to increasingly
generic strategies (OpenCV ECC → OpenCV ORB) if the previous one fails.
"""

from __future__ import annotations

from typing import Optional

from electpynasa.config import AstroalignConfig, ECCConfig, ORBConfig
from electpynasa.core.interfaces import RegistrationChain
from electpynasa.processing.registration.astroalign_strategy import AstroalignStrategy
from electpynasa.processing.registration.ecc_strategy import ECCStrategy
from electpynasa.processing.registration.orb_strategy import ORBStrategy


class RegistrationChainBuilder:
    """Build a default registration chain (astroalign → ECC → ORB)."""

    @staticmethod
    def build_default(
        astroalign_cfg: Optional[AstroalignConfig] = None,
        ecc_cfg: Optional[ECCConfig] = None,
        orb_cfg: Optional[ORBConfig] = None,
    ) -> RegistrationChain:
        """Return a :class:`RegistrationChain` with the three default strategies."""
        return RegistrationChain([
            AstroalignStrategy(astroalign_cfg or AstroalignConfig()),
            ECCStrategy(ecc_cfg or ECCConfig()),
            ORBStrategy(orb_cfg or ORBConfig()),
        ])

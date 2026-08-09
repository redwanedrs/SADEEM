"""
Backward-compatible shim for ``ghs_stretch_grayscale.py``.

Delegates to :mod:`electpynasa.cli.grayscale` so the Electron frontend can
keep invoking ``ghs_stretch_grayscale.py`` without any change.
"""

#!/usr/bin/env python3
from electpynasa.cli.common import safe_main
from electpynasa.cli.grayscale import main

if __name__ == "__main__":
    import sys
    sys.exit(safe_main(main))

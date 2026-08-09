"""
Backward-compatible shim for ``create_pyramid.py``.

Delegates to :mod:`electpynasa.cli.pyramid`.
"""

#!/usr/bin/env python3
from electpynasa.cli.common import safe_main
from electpynasa.cli.pyramid import main

if __name__ == "__main__":
    import sys
    sys.exit(safe_main(main))

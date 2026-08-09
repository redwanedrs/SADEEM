"""
Backward-compatible shim for ``align/ghs_auto_color.py``.

Delegates to :mod:`electpynasa.cli.composite`.
"""

#!/usr/bin/env python3
from electpynasa.cli.common import safe_main
from electpynasa.cli.composite import main

if __name__ == "__main__":
    import sys
    sys.exit(safe_main(main))

"""
CLI entry points for ElectPyNasa.

Three CLIs are exposed:

* :mod:`electpynasa.cli.grayscale`  — single-channel GHS stretch
* :mod:`electpynasa.cli.composite`  — three-channel color composite
* :mod:`electpynasa.cli.pyramid`    — DZI pyramid generation

Each module is invocable via ``python -m electpynasa.cli.<name>`` and emits
the structured ``__LOG__:{json}`` protocol on stdout, terminating with a
``SUCCESS:{path}`` token on success.
"""

from electpynasa.cli.common import add_common_arguments, safe_main

__all__ = ["add_common_arguments", "safe_main"]

"""Single source of truth for the package version.

The version itself is declared in ``pyproject.toml``; this module reads it
back at runtime via :func:`importlib.metadata.version` so that
:data:`__version__` and the HTTP ``User-Agent`` header stay in sync with the
installed distribution automatically. No other file should hardcode the
version string.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

try:
    __version__: str = version("lettr")
except PackageNotFoundError:  # pragma: no cover — running from an uninstalled checkout
    __version__ = "0.0.0+unknown"

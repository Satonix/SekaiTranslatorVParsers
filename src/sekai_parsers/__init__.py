from __future__ import annotations

from .registry import get_engine, list_engines, register_engine

def _autoload_engines() -> None:
    import pkgutil
    import importlib
    from . import engines as _engines_pkg

    for m in pkgutil.iter_modules(_engines_pkg.__path__, _engines_pkg.__name__ + "."):
        importlib.import_module(m.name)

_autoload_engines()

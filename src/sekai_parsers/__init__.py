from __future__ import annotations

from .engine_registry import get_engine, list_engines, register_engine

def discover_engines() -> None:
    import importlib
    import pkgutil
    from . import engines as engines_pkg

    # importa todo submódulo dentro de sekai_parsers.engines
    for m in pkgutil.iter_modules(engines_pkg.__path__, engines_pkg.__name__ + "."):
        importlib.import_module(m.name)

# descobre ao importar o pacote
discover_engines()

__all__ = ["get_engine", "list_engines", "register_engine", "discover_engines"]

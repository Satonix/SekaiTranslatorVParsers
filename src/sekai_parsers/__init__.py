from __future__ import annotations

from .engine_registry import get_engine, list_engines, register_engine

def discover_engines() -> None:
    """
    Importa automaticamente todos os módulos em sekai_parsers.engines
    para executar os register_engine() no import.
    """
    import importlib
    import pkgutil

    pkg_name = __name__ + ".engines"
    pkg = importlib.import_module(pkg_name)

    for m in pkgutil.iter_modules(pkg.__path__, pkg_name + "."):
        importlib.import_module(m.name)

# Descobre no import do pacote
discover_engines()

__all__ = ["get_engine", "list_engines", "register_engine", "discover_engines"]

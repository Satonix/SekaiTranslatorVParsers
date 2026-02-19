from __future__ import annotations

"""
sekai_parsers package

Auto-loads all engine modules inside sekai_parsers.engines
so they can register themselves via register_engine().
"""

from .registry import register_engine, get_engine, list_engines


def _autoload_engines() -> None:
    import pkgutil
    import importlib
    from . import engines as _engines_pkg

    # percorre todos os módulos dentro de sekai_parsers.engines
    for module_info in pkgutil.iter_modules(
        _engines_pkg.__path__,
        _engines_pkg.__name__ + ".",
    ):
        importlib.import_module(module_info.name)


# executa auto-registro ao importar o pacote
_autoload_engines()


__all__ = [
    "register_engine",
    "get_engine",
    "list_engines",
]

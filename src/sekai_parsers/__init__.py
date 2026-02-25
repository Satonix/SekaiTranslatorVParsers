<<<<<<< HEAD
from __future__ import annotations

from .engine_registry import get_engine, list_engines, register_engine

_DISCOVERY_ERRORS: list[tuple[str, str]] = []  # (module_name, error_str)


def discover_engines() -> None:
    """
    Importa todo submódulo dentro de sekai_parsers.engines para que cada engine
    registre seu parser via register_engine(...).

    Importante: não deixa 1 engine quebrada impedir o pacote inteiro de carregar.
    """
    import importlib
    import pkgutil

    try:
        from . import engines as engines_pkg
    except Exception as e:
        _DISCOVERY_ERRORS.append(("sekai_parsers.engines", repr(e)))
        return

    for m in pkgutil.iter_modules(engines_pkg.__path__, engines_pkg.__name__ + "."):
        try:
            importlib.import_module(m.name)
        except Exception as e:
            _DISCOVERY_ERRORS.append((m.name, repr(e)))
            # continua importando as outras engines


def discovery_errors() -> list[tuple[str, str]]:
    """Retorna erros de discovery (se houver)."""
    return list(_DISCOVERY_ERRORS)


# descobre ao importar o pacote (sem quebrar o import)
try:
    discover_engines()
except Exception as _e:
    _DISCOVERY_ERRORS.append(("discover_engines()", repr(_e)))


__all__ = [
    "get_engine",
    "list_engines",
    "register_engine",
    "discover_engines",
    "discovery_errors",
]
=======
from __future__ import annotations

from .engine_registry import get_engine, list_engines, register_engine

_DISCOVERY_ERRORS: list[tuple[str, str]] = []  # (module_name, error_str)


def discover_engines() -> None:
    """
    Importa todo submódulo dentro de sekai_parsers.engines para que cada engine
    registre seu parser via register_engine(...).

    Importante: não deixa 1 engine quebrada impedir o pacote inteiro de carregar.
    """
    import importlib
    import pkgutil

    try:
        from . import engines as engines_pkg
    except Exception as e:
        _DISCOVERY_ERRORS.append(("sekai_parsers.engines", repr(e)))
        return

    for m in pkgutil.iter_modules(engines_pkg.__path__, engines_pkg.__name__ + "."):
        try:
            importlib.import_module(m.name)
        except Exception as e:
            _DISCOVERY_ERRORS.append((m.name, repr(e)))
            # continua importando as outras engines


def discovery_errors() -> list[tuple[str, str]]:
    """Retorna erros de discovery (se houver)."""
    return list(_DISCOVERY_ERRORS)


# descobre ao importar o pacote (sem quebrar o import)
try:
    discover_engines()
except Exception as _e:
    _DISCOVERY_ERRORS.append(("discover_engines()", repr(_e)))


__all__ = [
    "get_engine",
    "list_engines",
    "register_engine",
    "discover_engines",
    "discovery_errors",
]
>>>>>>> 824d17b2d4c0216bd447d690127f0ff6d4259d4a

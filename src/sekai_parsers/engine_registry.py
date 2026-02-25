<<<<<<< HEAD
from __future__ import annotations

from collections.abc import Callable
from typing import Dict, Protocol


class Parser(Protocol):
    """
    Interface mínima esperada pelos engines.
    Ajuste/expanda depois se você tiver uma classe base real.
    """
    def detect(self, file_path: str, data: bytes | None = None) -> bool: ...
    def extract(self, file_path: str) -> list[dict]: ...
    def inject(self, file_path: str, entries: list[dict]) -> None: ...


_ENGINE_FACTORIES: Dict[str, Callable[[], Parser]] = {}


def register_engine(engine_id: str, factory: Callable[[], Parser]) -> None:
    """Register an engine parser.

    `engine_id` must be stable, e.g. `kirikiri.ks`.
    """
    _ENGINE_FACTORIES[engine_id] = factory


def get_engine(engine_id: str) -> Parser:
    if engine_id not in _ENGINE_FACTORIES:
        raise KeyError(f"Unknown engine_id: {engine_id}")
    return _ENGINE_FACTORIES[engine_id]()


def list_engines() -> list[str]:
    return sorted(_ENGINE_FACTORIES.keys())
=======
from __future__ import annotations

from collections.abc import Callable
from typing import Dict, Protocol


class Parser(Protocol):
    """
    Interface mínima esperada pelos engines.
    Ajuste/expanda depois se você tiver uma classe base real.
    """
    def detect(self, file_path: str, data: bytes | None = None) -> bool: ...
    def extract(self, file_path: str) -> list[dict]: ...
    def inject(self, file_path: str, entries: list[dict]) -> None: ...


_ENGINE_FACTORIES: Dict[str, Callable[[], Parser]] = {}


def register_engine(engine_id: str, factory: Callable[[], Parser]) -> None:
    """Register an engine parser.

    `engine_id` must be stable, e.g. `kirikiri.ks`.
    """
    _ENGINE_FACTORIES[engine_id] = factory


def get_engine(engine_id: str) -> Parser:
    if engine_id not in _ENGINE_FACTORIES:
        raise KeyError(f"Unknown engine_id: {engine_id}")
    return _ENGINE_FACTORIES[engine_id]()


def list_engines() -> list[str]:
    return sorted(_ENGINE_FACTORIES.keys())
>>>>>>> 824d17b2d4c0216bd447d690127f0ff6d4259d4a

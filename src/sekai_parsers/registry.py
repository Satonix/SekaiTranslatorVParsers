from __future__ import annotations

from collections.abc import Callable
from typing import Dict

from .api import Parser

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

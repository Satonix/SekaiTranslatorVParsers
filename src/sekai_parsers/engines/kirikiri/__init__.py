from __future__ import annotations

from ...engine_registry import register_engine
from .ks_parser import KiriKiriKsParser


def _factory():
    return KiriKiriKsParser()


register_engine("kirikiri.ks", _factory)

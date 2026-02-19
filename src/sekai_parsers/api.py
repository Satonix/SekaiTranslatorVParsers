from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True)
class Entry:
    """A translatable unit.

    - `key` is stable within a file and used to map translations.
    - `speaker` is optional and may be derived from script tags.
    - `text` is the original text as shown to the player (raw, not localized).
    - `meta` stores engine-specific info needed for lossless export.
    """
    key: str
    text: str
    speaker: str | None = None
    meta: dict | None = None


@dataclass(slots=True)
class ParseResult:
    engine_id: str
    entries: list[Entry]


class Parser(Protocol):
    engine_id: str
    extensions: tuple[str, ...]

    def parse(self, data: bytes, *, file_path: str | None = None) -> ParseResult: ...
    def export(
        self,
        data: bytes,
        entries: list[Entry],
        *,
        file_path: str | None = None,
    ) -> bytes: ...

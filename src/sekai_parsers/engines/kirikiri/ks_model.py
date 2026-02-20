from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class TextSpan:
    """A span of text inside the original script that is replaceable."""
    key: str
    start: int
    end: int
    speaker: str | None

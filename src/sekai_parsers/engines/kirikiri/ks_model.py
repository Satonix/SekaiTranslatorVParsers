<<<<<<< HEAD
from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class TextSpan:
    """A span of text inside the original script that is replaceable."""
    key: str
    start: int
    end: int
    speaker: str | None
=======
from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class TextSpan:
    """A span of text inside the original script that is replaceable."""
    key: str
    start: int
    end: int
    speaker: str | None
>>>>>>> 824d17b2d4c0216bd447d690127f0ff6d4259d4a

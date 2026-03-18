from __future__ import annotations

import re
from dataclasses import dataclass

from ...api import Entry, ParseResult


def _decode(data: bytes) -> tuple[str, str]:
    for enc in ("utf-8-sig", "utf-8", "cp932"):
        try:
            return data.decode(enc), enc
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace"), "utf-8"


def _find_en_ranges(text: str, en_finder: re.Pattern) -> list[tuple[int, int]]:
    """
    Encontra todos os blocos  en = { ... }  no texto,
    rastreando depth de chaves — idêntico ao while do JS.
    """
    ranges: list[tuple[int, int]] = []

    for m in en_finder.finditer(text):
        pos = m.end()
        depth = 1
        while pos < len(text) and depth > 0:
            if text[pos] == "{":
                depth += 1
            elif text[pos] == "}":
                depth -= 1
            pos += 1
        ranges.append((m.start(), pos))

    return ranges


def _is_inside_en(start: int, end: int, en_ranges: list[tuple[int, int]]) -> bool:
    for r_start, r_end in en_ranges:
        if start > r_start and end < r_end:
            return True
    return False


_LEFT_DQUOTE  = "\u201c"
_RIGHT_DQUOTE = "\u201d"


@dataclass(frozen=True, slots=True)
class ArtemisProfile:
    id: str
    rx_en_block: re.Pattern
    rx_text: re.Pattern


DEFAULT_PROFILE = ArtemisProfile(
    id="default",
    rx_en_block=re.compile(r"\ben\s*=\s*\{"),
    rx_text=re.compile(
        r'"((?:[^"\\]|\\[\s\S])*)"'
        r'\s*,\s*\r?\n\s*'
        r'\{"rt2"\}',
    ),
)


class ArtemisAstParser:
    """Parser para a Artemis Engine (.ast)."""

    extensions = (".ast",)

    def __init__(self, profile: ArtemisProfile = DEFAULT_PROFILE):
        self.profile   = profile
        self.engine_id = f"artemis.ast.{profile.id}"

    def parse(self, data: bytes, *, file_path: str | None = None) -> ParseResult:
        text, _enc = _decode(data)
        en_ranges  = _find_en_ranges(text, self.profile.rx_en_block)

        entries: list[Entry] = []
        key_idx = 0

        for tm in self.profile.rx_text.finditer(text):
            s = tm.start(1)
            e = tm.end(1)

            if text[s] == _LEFT_DQUOTE:
                s += 1
            if e > s and text[e - 1] == _RIGHT_DQUOTE:
                e -= 1

            if not _is_inside_en(s, e, en_ranges):
                continue

            key = f"{file_path or 'file'}:{key_idx}"
            key_idx += 1

            entries.append(
                Entry(
                    key=key,
                    text=text[s:e],
                    meta={"char_start": s, "char_end": e},
                )
            )

        return ParseResult(engine_id=self.engine_id, entries=entries)

    def export(
        self,
        data: bytes,
        entries: list[Entry],
        *,
        file_path: str | None = None,
    ) -> bytes:
        text, enc = _decode(data)

        by_key: dict[str, Entry] = {
            e.key: e for e in entries if getattr(e, "key", None)
        }

        sorted_entries = sorted(
            [e for e in entries if e.meta and "char_start" in e.meta],
            key=lambda e: e.meta["char_start"],  # type: ignore[index]
            reverse=True,
        )

        chars = list(text)

        for entry in sorted_entries:
            ent = by_key.get(entry.key)
            if ent is None:
                continue

            s: int = entry.meta["char_start"]   # type: ignore[index]
            e: int = entry.meta["char_end"]      # type: ignore[index]
            chars[s:e] = list(ent.text)

        return "".join(chars).encode(enc, errors="replace")

    def can_parse(self, *, file_path: str | None = None, data: bytes | None = None) -> bool:
        return (file_path or "").lower().endswith(".ast")

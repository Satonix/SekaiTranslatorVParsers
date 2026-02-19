from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from ...api import Entry, ParseResult
from ...utils.text import normalize_newlines
from .ks_model import TextSpan


_CN_TAG_RE = re.compile(r'^\[cn\s+name="([^"]+)"(?:[^\]]*)\]\s*$', re.IGNORECASE)
# We treat any bracketed command/tag line as non-text control.
_TAG_LINE_RE = re.compile(r'^\s*(\[[^\]]*\]|\*[^\s].*)\s*$')


@dataclass(slots=True)
class _ParseState:
    speaker: str | None = None


class KiriKiriKsParser:
    """KiriKiri `.ks` parser focused on stable round-trip.

    Supported pattern (as seen in *Forbidden Love Wife Sister*):
    - Speaker tag: [cn name="..."] (may contain other attributes)
    - The following one or more *non-tag* lines are treated as text until the next tag line.
    - Lines starting with ';' (comments) are ignored.
    """

    engine_id = "kirikiri.ks"
    extensions = (".ks",)

    def parse(self, data: bytes, *, file_path: str | None = None) -> ParseResult:
        text = data.decode("utf-8", errors="replace")
        text_nl = normalize_newlines(text)

        spans: list[TextSpan] = []
        entries: list[Entry] = []

        state = _ParseState()
        i = 0
        key_idx = 0

        lines = text_nl.splitlines(keepends=True)
        offset = 0

        def is_comment(line: str) -> bool:
            stripped = line.lstrip()
            return stripped.startswith(";")

        while i < len(lines):
            line = lines[i]
            line_start = offset
            offset += len(line)

            if is_comment(line) or not line.strip():
                i += 1
                continue

            m_cn = _CN_TAG_RE.match(line.strip())
            if m_cn:
                state.speaker = m_cn.group(1)
                i += 1
                continue

            if _TAG_LINE_RE.match(line.strip()):
                i += 1
                continue

            # Text block: consume consecutive non-tag/non-comment lines
            block_start_off = line_start
            block_lines = [line]
            i += 1

            while i < len(lines):
                nxt = lines[i]
                if is_comment(nxt) or not nxt.strip():
                    break
                if _CN_TAG_RE.match(nxt.strip()):
                    break
                if _TAG_LINE_RE.match(nxt.strip()):
                    break
                block_lines.append(nxt)
                i += 1

            block_text = "".join(block_lines)

            start = block_start_off
            end = block_start_off + len(block_text)

            key = f"{file_path or 'file'}:{key_idx}"
            key_idx += 1

            entries.append(
                Entry(
                    key=key,
                    original=block_text,
                    translation="",
                    speaker=state.speaker,
                    meta={},
                )
            )
            spans.append(TextSpan(start=start, end=end, key=key))

        return ParseResult(
            engine_id=self.engine_id,
            original_text=text_nl,
            entries=entries,
            spans=spans,
        )

    def export(self, result: ParseResult, entries: Iterable[Entry]) -> bytes:
        # Map key -> replacement text (translation if present, else original)
        by_key: dict[str, str] = {}
        for e in entries:
            repl = e.translation if (e.translation is not None and e.translation != "") else e.original
            by_key[e.key] = repl

        out = result.original_text
        # Apply replacements from back to front to keep offsets stable
        for sp in sorted(result.spans, key=lambda s: s.start, reverse=True):
            repl = by_key.get(sp.key)
            if repl is None:
                continue
            out = out[:sp.start] + repl + out[sp.end:]

        return out.encode(

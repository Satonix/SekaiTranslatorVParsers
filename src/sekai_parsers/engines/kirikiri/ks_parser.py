from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from ...api import Entry, ParseResult
from ...registry import register_engine
from ...utils.text import normalize_newlines
from .ks_model import TextSpan


_CN_TAG_RE = re.compile(r'^\[cn\s+name="([^"]+)"(?:[^\]]*)\]\s*$', re.IGNORECASE)
# We treat any bracketed command/tag line as non-text control.
_TAG_LINE_RE = re.compile(r'^\s*(\[[^\]]*\]|\*[^\s].*)\s*$')


@dataclass(slots=True)
class _ParseState:
    speaker: str | None = None


class KirikiriKsParser:
    """KiriKiri `.ks` parser focused on stable round-trip.


    Supported pattern (as seen in *Forbidden Love Wife Sister*):
    - Speaker tag: [cn name="..."] (may contain other attributes)
    - The following one or more *non-tag* lines are treated as text until the next tag line.
    - Lines starting with ';' (comments) are ignored.
    """

    engine_id = "kirikiri.ks"
    extensions = (".ks",)

    def parse(self, data: bytes, *, file_path: str | None = None) -> ParseResult:
        # Most KiriKiri projects are Shift-JIS, but this game sample already contains ASCII/UTF-8.
        # We decode as UTF-8 with replacement; consumers can keep original bytes if needed.
        text = data.decode("utf-8", errors="replace")
        text_nl = normalize_newlines(text)

        spans: list[TextSpan] = []
        entries: list[Entry] = []

        state = _ParseState()
        i = 0
        key_idx = 0

        # We'll scan line-by-line while also tracking absolute offsets for replacement.
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

            # Tag/control line -> reset speaker? keep speaker for subsequent text; game uses cn before each line anyway.
            if _TAG_LINE_RE.match(line.strip()):
                i += 1
                continue

            # Otherwise it's text. It may span multiple consecutive non-tag, non-comment lines.
            block_start_i = i
            block_start_off = line_start
            block_lines = [line]
            i += 1
            while i < len(lines):
                peek = lines[i]
                if is_comment(peek) or not peek.strip():
                    # include blank lines? keep them out of translatable text
                    break
                if _CN_TAG_RE.match(peek.strip()) or _TAG_LINE_RE.match(peek.strip()):
                    break
                block_lines.append(peek)
                i += 1

            block_text = "".join(block_lines)
            # Preserve indentation exactly; translation replaces whole block.
            key = f"t{key_idx:06d}"
            key_idx += 1
            spans.append(TextSpan(key=key, start=block_start_off, end=block_start_off + len(block_text), speaker=state.speaker))
            entries.append(Entry(key=key, text=block_text.rstrip("\n"), speaker=state.speaker, meta={"eol": "\n" if block_text.endswith("\n") else ""}))

        return ParseResult(engine_id=self.engine_id, entries=entries)

    def export(
        self,
        data: bytes,
        entries: list[Entry],
        *,
        file_path: str | None = None,
    ) -> bytes:
        text = data.decode("utf-8", errors="replace")
        text_nl = normalize_newlines(text)

        # Re-parse to get current spans (so export can work even if called with original file).
        parsed = self.parse(data, file_path=file_path)
        spans_by_key = {e.key: s for e, s in zip(parsed.entries, self._spans_from_parse(data))}

        # Map new texts
        entry_by_key = {e.key: e for e in entries}

        out = text_nl
        # Apply replacements from back to front to keep offsets valid
        spans_sorted = sorted(spans_by_key.values(), key=lambda s: s.start, reverse=True)
        for span in spans_sorted:
            e = entry_by_key.get(span.key)
            if e is None:
                continue
            meta = e.meta or {}
            eol = meta.get("eol", "\n")
            replacement = (e.text or "")
            # Keep original trailing newline if it existed
            if eol and not replacement.endswith("\n"):
                replacement = replacement + eol
            out = out[: span.start] + replacement + out[span.end :]

        return out.encode("utf-8")

    # Internal: compute spans using same logic as parse, but retaining offsets.
    def _spans_from_parse(self, data: bytes) -> list[TextSpan]:
        text = data.decode("utf-8", errors="replace")
        text_nl = normalize_newlines(text)
        lines = text_nl.splitlines(keepends=True)

        spans: list[TextSpan] = []
        state = _ParseState()
        i = 0
        key_idx = 0
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

            block_start_off = line_start
            block_lines = [line]
            i += 1
            while i < len(lines):
                peek = lines[i]
                if is_comment(peek) or not peek.strip():
                    break
                if _CN_TAG_RE.match(peek.strip()) or _TAG_LINE_RE.match(peek.strip()):
                    break
                block_lines.append(peek)
                i += 1

            block_text = "".join(block_lines)
            key = f"t{key_idx:06d}"
            key_idx += 1
            spans.append(TextSpan(key=key, start=block_start_off, end=block_start_off + len(block_text), speaker=state.speaker))

        return spans


# Registration (import side-effect).
register_engine(KirikiriKsParser.engine_id, KirikiriKsParser)

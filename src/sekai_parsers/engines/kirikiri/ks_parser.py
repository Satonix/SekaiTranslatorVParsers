from __future__ import annotations

import re
from typing import List

from sekai_parsers.api import Entry, ParseResult


_CN_TAG_RE = re.compile(r'^\[cn\s+name="([^"]+)"(?:[^\]]*)\]\s*$', re.IGNORECASE)
_TAG_LINE_RE = re.compile(r'^\s*(\[[^\]]*\]|\*[^\s].*)\s*$')


class KiriKiriKsParser:
    engine_id = "kirikiri.ks"
    extensions = (".ks",)

    # ----------------------------------------------------------
    # Optional but recommended for autodetect
    # ----------------------------------------------------------

    def can_parse(self, *, file_path: str | None, data: bytes) -> bool:
        if not file_path:
            return False
        return file_path.lower().endswith(".ks")

    # ----------------------------------------------------------
    # Parse
    # ----------------------------------------------------------

    def parse(self, data: bytes, *, file_path: str | None = None) -> ParseResult:
        text = data.decode("utf-8", errors="replace")
        lines = text.splitlines(keepends=True)

        entries: List[Entry] = []
        speaker: str | None = None

        offset = 0
        key_idx = 0

        for line in lines:
            stripped = line.strip()

            # comment
            if stripped.startswith(";"):
                offset += len(line)
                continue

            # speaker tag
            m = _CN_TAG_RE.match(stripped)
            if m:
                speaker = m.group(1)
                offset += len(line)
                continue

            # control/tag line
            if _TAG_LINE_RE.match(stripped):
                offset += len(line)
                continue

            # empty
            if not stripped:
                offset += len(line)
                continue

            start = offset
            end = offset + len(line)

            key = f"{file_path or 'file'}:{key_idx}"
            key_idx += 1

            entries.append(
                Entry(
                    key=key,
                    text=line,
                    speaker=speaker,
                    meta={
                        "start": start,
                        "end": end,
                    },
                )
            )

            offset += len(line)

        return ParseResult(
            engine_id=self.engine_id,
            entries=entries,
        )

    # ----------------------------------------------------------
    # Export
    # ----------------------------------------------------------

    def export(
        self,
        data: bytes,
        entries: list[Entry],
        *,
        file_path: str | None = None,
    ) -> bytes:

        original_text = data.decode("utf-8", errors="replace")

        # apply replacements from back to front
        replacements = sorted(
            entries,
            key=lambda e: e.meta.get("start", 0),
            reverse=True,
        )

        out = original_text

        for e in replacements:
            meta = e.meta or {}
            start = meta.get("start")
            end = meta.get("end")

            if start is None or end is None:
                continue

            out = out[:start] + e.text + out[end:]

        return out.encode("utf-8")

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from ...api import Entry, ParseResult
from ...utils.text import normalize_newlines


# ------------------------------------------------------------------
# Profile
# ------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class KiriKiriProfile:
    id: str
    speaker_tag: re.Pattern
    rx_comment: re.Pattern
    rx_label: re.Pattern
    rx_tag_only: re.Pattern


# Profile default (compatível com seu parser antigo)
DEFAULT_PROFILE = KiriKiriProfile(
    id="default",
    speaker_tag=re.compile(r'^\[cn\s+name="([^"]+)"(?:[^\]]*)\]\s*$', re.IGNORECASE),
    rx_comment=re.compile(r'^\s*;'),
    rx_label=re.compile(r'^\s*\*'),
    rx_tag_only=re.compile(r'^\s*(?:\[[^\]]+\]\s*)+$'),
)


# ------------------------------------------------------------------
# Parser
# ------------------------------------------------------------------

@dataclass(slots=True)
class _ParseState:
    speaker: str | None = None


class KiriKiriKsParser:
    """
    Parser KiriKiri (.ks)

    Regras:
    - 1 entry por linha de texto
    - [r] e [cr] NÃO causam merge
    - speaker definido por tag do profile
    - round-trip estável
    """

    extensions = (".ks",)

    def __init__(self, profile: KiriKiriProfile = DEFAULT_PROFILE):
        self.profile = profile
        self.engine_id = f"kirikiri.ks.{profile.id}"

    # -----------------------
    # Detecção
    # -----------------------

    def can_parse(self, *, file_path: str | None = None, data: bytes | None = None) -> bool:
        fp = (file_path or "").lower()
        if fp.endswith(".ks"):
            return True
        return False

    # -----------------------
    # Parse
    # -----------------------

    def parse(self, data: bytes, *, file_path: str | None = None) -> ParseResult:
        text = data.decode("utf-8", errors="replace")
        text_nl = normalize_newlines(text)

        entries: list[Entry] = []
        state = _ParseState()
        key_idx = 0

        lines = text_nl.splitlines(keepends=True)

        for line in lines:
            stripped = line.strip()

            if not stripped:
                continue

            # comentário
            if self.profile.rx_comment.match(stripped):
                continue

            # label (*scene, *|)
            if self.profile.rx_label.match(stripped):
                continue

            # tag de speaker
            m_speaker = self.profile.speaker_tag.match(stripped)
            if m_speaker:
                state.speaker = m_speaker.group(1)
                continue

            # linha só de tag (ex: [cm], [GL ...], [quake ...][wq])
            if self.profile.rx_tag_only.match(stripped):
                continue

            # TEXTO (1 entry por linha)
            key = f"{file_path or 'file'}:{key_idx}"
            key_idx += 1

            entries.append(
                Entry(
                    key=key,
                    text=line,
                    speaker=state.speaker,
                    meta={},
                )
            )

        return ParseResult(engine_id=self.engine_id, entries=entries)

    # -----------------------
    # Export
    # -----------------------

    def export(
        self,
        data: bytes,
        entries: list[Entry],
        *,
        file_path: str | None = None,
    ) -> bytes:

        original_text = normalize_newlines(data.decode("utf-8", errors="replace"))
        lines = original_text.splitlines(keepends=True)

        by_key: dict[str, str] = {
            e.key: e.text for e in entries if getattr(e, "key", None)
        }

        out_lines: list[str] = []
        key_idx = 0
        state = _ParseState()

        for line in lines:
            stripped = line.strip()

            if not stripped:
                out_lines.append(line)
                continue

            if self.profile.rx_comment.match(stripped):
                out_lines.append(line)
                continue

            if self.profile.rx_label.match(stripped):
                out_lines.append(line)
                continue

            m_speaker = self.profile.speaker_tag.match(stripped)
            if m_speaker:
                state.speaker = m_speaker.group(1)
                out_lines.append(line)
                continue

            if self.profile.rx_tag_only.match(stripped):
                out_lines.append(line)
                continue

            key = f"{file_path or 'file'}:{key_idx}"
            key_idx += 1

            repl = by_key.get(key)
            if repl is None:
                out_lines.append(line)
            else:
                out_lines.append(repl)

        return "".join(out_lines).encode("utf-8")
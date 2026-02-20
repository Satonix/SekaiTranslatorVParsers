from __future__ import annotations

import re
from dataclasses import dataclass

from ...api import Entry, ParseResult


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


DEFAULT_PROFILE = KiriKiriProfile(
    id="default",
    speaker_tag=re.compile(r'^\[cn\s+name="([^"]+)"(?:[^\]]*)\]\s*$', re.IGNORECASE),
    rx_comment=re.compile(r"^\s*;"),
    rx_label=re.compile(r"^\s*\*"),
    rx_tag_only=re.compile(r"^\s*(?:\[[^\]]+\]\s*)+$"),
)


# ------------------------------------------------------------------
# Helpers (encoding + EOL)
# ------------------------------------------------------------------

def _detect_encoding(data: bytes) -> str:
    try:
        data.decode("utf-8")
        return "utf-8"
    except UnicodeDecodeError:
        return "cp932"


def _decode_text(data: bytes) -> tuple[str, str]:
    enc = _detect_encoding(data)
    return data.decode(enc, errors="replace"), enc


def _encode_text(text: str, enc: str) -> bytes:
    return text.encode(enc, errors="replace")


def _line_eol(line: str) -> str:
    # preserva o EOL exato do original
    if line.endswith("\r\n"):
        return "\r\n"
    if line.endswith("\n"):
        return "\n"
    if line.endswith("\r"):
        return "\r"
    return ""


# ------------------------------------------------------------------
# Parser
# ------------------------------------------------------------------

@dataclass(slots=True)
class _ParseState:
    speaker: str | None = None


class KiriKiriKsParser:
    extensions = (".ks",)

    def __init__(self, profile: KiriKiriProfile = DEFAULT_PROFILE):
        self.profile = profile
        self.engine_id = f"kirikiri.ks.{profile.id}"

    def can_parse(self, *, file_path: str | None = None, data: bytes | None = None) -> bool:
        return (file_path or "").lower().endswith(".ks")

    # -----------------------
    # Parse
    # -----------------------

    def parse(self, data: bytes, *, file_path: str | None = None) -> ParseResult:
        # NÃO normaliza newlines — preserva CRLF/LF
        text, _enc = _decode_text(data)

        entries: list[Entry] = []
        state = _ParseState()
        key_idx = 0

        lines = text.splitlines(keepends=True)

        for line in lines:
            stripped = line.strip()

            if not stripped:
                continue

            if self.profile.rx_comment.match(stripped):
                continue

            if self.profile.rx_label.match(stripped):
                continue

            m_speaker = self.profile.speaker_tag.match(stripped)
            if m_speaker:
                state.speaker = m_speaker.group(1)
                continue

            if self.profile.rx_tag_only.match(stripped):
                continue

            key = f"{file_path or 'file'}:{key_idx}"
            key_idx += 1

            # Entry.text mantém a linha original (incluindo EOL)
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

    def export(self, data: bytes, entries: list[Entry], *, file_path: str | None = None) -> bytes:
        # NÃO normaliza newlines — preserva CRLF/LF
        original_text, enc = _decode_text(data)
        lines = original_text.splitlines(keepends=True)

        by_key: dict[str, str] = {e.key: e.text for e in entries if getattr(e, "key", None)}

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
                continue

            # FIX: garantir que a linha substituída preserve o EOL do original
            eol = _line_eol(line)
            if eol and not repl.endswith(("\r\n", "\n", "\r")):
                repl = repl + eol

            out_lines.append(repl)

        return _encode_text("".join(out_lines), enc)

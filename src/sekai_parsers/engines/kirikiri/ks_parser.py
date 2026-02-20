from __future__ import annotations

import re
from dataclasses import dataclass

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


DEFAULT_PROFILE = KiriKiriProfile(
    id="default",
    speaker_tag=re.compile(r'^\[cn\s+name="([^"]+)"(?:[^\]]*)\]\s*$', re.IGNORECASE),
    rx_comment=re.compile(r"^\s*;"),
    rx_label=re.compile(r"^\s*\*"),
    rx_tag_only=re.compile(r"^\s*(?:\[[^\]]+\]\s*)+$"),
)


# ------------------------------------------------------------------
# Helpers (encoding)
# ------------------------------------------------------------------

def _detect_encoding(data: bytes) -> str:
    """
    KiriKiri .ks antigos frequentemente são CP932 (Shift-JIS).
    Estratégia mínima:
    - se decodificar utf-8 sem UnicodeDecodeError -> utf-8
    - senão -> cp932
    """
    try:
        data.decode("utf-8")
        return "utf-8"
    except UnicodeDecodeError:
        return "cp932"


def _decode_text(data: bytes) -> tuple[str, str]:
    enc = _detect_encoding(data)
    text = data.decode(enc, errors="replace")
    return text, enc


def _encode_text(text: str, enc: str) -> bytes:
    return text.encode(enc, errors="replace")


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
        return fp.endswith(".ks")

    # -----------------------
    # Parse
    # -----------------------

    def parse(self, data: bytes, *, file_path: str | None = None) -> ParseResult:
        text, _enc = _decode_text(data)
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

            # mantém o newline do original (keepends=True)
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
        original_text, enc = _decode_text(data)
        original_text = normalize_newlines(original_text)
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

            # --- FIX: preservar o final de linha do original ---
            # Se o original tinha '\n' (normalize_newlines), e a tradução veio sem '\n', adiciona.
            if line.endswith("\n") and not repl.endswith("\n"):
                repl = repl + "\n"

            out_lines.append(repl)

        return _encode_text("".join(out_lines), enc)

from __future__ import annotations

import re
from dataclasses import dataclass

from ...api import Entry, ParseResult


# Profile
@dataclass(frozen=True, slots=True)
class KiriKiriProfile:
    id: str
    speaker_tag: re.Pattern
    rx_comment: re.Pattern
    rx_label: re.Pattern
    rx_tag_only: re.Pattern


DEFAULT_PROFILE = KiriKiriProfile(
    id="default",
    # Common speaker tags across KiriKiri/KAG dialects.
    # - Standard KAG: [cn name="Name"]
    # - Yandere dialect: [P_NAME s_cn="Name"]
    # Keep it anchored to full tag lines to avoid false positives.
    speaker_tag=re.compile(
        r'^(?:\[cn\s+name="([^"]+)"(?:[^\]]*)\]\s*$|'
        r'\[P_NAME\b[^\]]*\bs_cn="([^"]+)"[^\]]*\]\s*$)',
        re.IGNORECASE,
    ),
    rx_comment=re.compile(r"^\s*;"),
    rx_label=re.compile(r"^\s*\*"),
    rx_tag_only=re.compile(r"^\s*(?:\[[^\]]+\]\s*)+$"),
)


# KiriKiri control suffixes often found at end of dialogue lines.
# Examples: "Hello.[r]", "Hello?[cr]", "Line[r][cr]".
_RX_TRAILING_CONTROLS = re.compile(r"(?:\[(?:cr|r)\])+$", re.IGNORECASE)


# Helpers (encoding + EOL)
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


# Parser
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

    # Parse
    def parse(self, data: bytes, *, file_path: str | None = None) -> ParseResult:
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

            # Speaker tags may appear inside a tag line; use search() for robustness.
            m_speaker = self.profile.speaker_tag.search(stripped)
            if m_speaker:
                # Support profiles/patterns with multiple capture groups.
                sp = ""
                try:
                    sp = (m_speaker.group(1) or "")
                    if not sp and m_speaker.lastindex and m_speaker.lastindex >= 2:
                        sp = (m_speaker.group(2) or "")
                except Exception:
                    sp = ""
                state.speaker = sp or state.speaker
                continue

            if self.profile.rx_tag_only.match(stripped):
                continue

            key = f"{file_path or 'file'}:{key_idx}"
            key_idx += 1

            # Strip trailing KiriKiri control tags like [r]/[cr] from the stored entry text,
            # but keep them in meta so export can restore them deterministically.
            eol = _line_eol(line)
            body = line[:-len(eol)] if eol else line
            m_tail = _RX_TRAILING_CONTROLS.search(body)
            tail = m_tail.group(0) if m_tail else ""
            body_wo_tail = body[: -len(tail)] if tail else body

            # Entry.text mantém a linha original
            entries.append(
                Entry(
                    key=key,
                    text=body_wo_tail + eol,
                    speaker=state.speaker,
                    meta={"kk_tail": tail},
                )
            )

        return ParseResult(engine_id=self.engine_id, entries=entries)

    # Export
    def export(self, data: bytes, entries: list[Entry], *, file_path: str | None = None) -> bytes:
        original_text, enc = _decode_text(data)
        lines = original_text.splitlines(keepends=True)

        by_key: dict[str, Entry] = {e.key: e for e in entries if getattr(e, "key", None)}

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

            m_speaker = self.profile.speaker_tag.search(stripped)
            if m_speaker:
                sp = ""
                try:
                    sp = (m_speaker.group(1) or "")
                    if not sp and m_speaker.lastindex and m_speaker.lastindex >= 2:
                        sp = (m_speaker.group(2) or "")
                except Exception:
                    sp = ""
                state.speaker = sp or state.speaker
                out_lines.append(line)
                continue

            if self.profile.rx_tag_only.match(stripped):
                out_lines.append(line)
                continue

            key = f"{file_path or 'file'}:{key_idx}"
            key_idx += 1

            ent = by_key.get(key)
            if ent is None:
                out_lines.append(line)
                continue

            repl = ent.text

            # Restore trailing KiriKiri control tags that were stripped on parse.
            tail = ""
            try:
                tail = (ent.meta or {}).get("kk_tail") or ""
            except Exception:
                tail = ""

            eol = _line_eol(line)
            # Normalize replacement to have the original EOL.
            if eol:
                # separate any existing eol
                repl_body = repl
                repl_eol = _line_eol(repl_body)
                if repl_eol:
                    repl_body = repl_body[:-len(repl_eol)]

                # avoid duplicating tail if user kept it
                if tail and not repl_body.endswith(tail):
                    repl_body = repl_body + tail

                repl = repl_body + eol
            else:
                # no original eol; still restore tail if needed
                if tail and not repl.endswith(tail):
                    repl = repl + tail

            out_lines.append(repl)

        return _encode_text("".join(out_lines), enc)

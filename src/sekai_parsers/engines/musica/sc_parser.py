from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Tuple

from ...api import Entry, ParseResult


MAP_ENCODE: Dict[str, str] = {
    "Á": "ﾁ",
    "É": "ﾉ",
    "Í": "ﾍ",
    "Ó": "ﾓ",
    "Ú": "ﾚ",
    "á": "$",
    "ã": "^",
    "à": "<",
    "â": ">",
    "ç": "&",
    "é": "%",
    "ú": "(",
    "ó": ")",
    "õ": "*",
}
MAP_DECODE: Dict[str, str] = {v: k for k, v in MAP_ENCODE.items()}

_RX_MESSAGE = re.compile(
    r"^(\s*)"
    r"(?:(\[[^\]]+\]\.)\s*)?"
    r"\.message(\s+)(\d+)(\s+)(.*?)(\r?\n)?$"
)

_RE_WS_LEAD = re.compile(r"^\s*")
_RE_WS_TAIL = re.compile(r"\s*$")
_RX_SUFFIX = re.compile(
    r"(?s)^(.*?)(\\(?:[A-Za-z]+[0-9]*))(\\(?:[A-Za-z]+[0-9]*))*?(\s*)$"
)
_RX_CONTROL_ONLY = re.compile(r"^\s*(?:\\[A-Za-z]+[0-9]*)+\s*$")


@dataclass(frozen=True, slots=True)
class MusicaProfile:
    id: str
    dialog_pairs: tuple[tuple[str, str], ...] = ()


DEFAULT_PROFILE = MusicaProfile(
    id="default",
    dialog_pairs=(),
)


def _decode_table(s: str) -> str:
    if not s:
        return s
    return "".join(MAP_DECODE.get(ch, ch) for ch in s)


def _encode_table(s: str) -> str:
    if not s:
        return s
    return "".join(MAP_ENCODE.get(ch, ch) for ch in s)


def _detect_encoding(data: bytes) -> str:
    for enc in ("utf-8-sig", "utf-8", "cp932", "shift_jis"):
        try:
            data.decode(enc)
            return enc
        except UnicodeDecodeError:
            pass
    return "utf-8"


def _decode_text(data: bytes) -> tuple[str, str]:
    enc = _detect_encoding(data)
    return data.decode(enc, errors="replace"), enc


def _encode_text(text: str, enc: str) -> bytes:
    return text.encode(enc, errors="replace")


def _line_eol(line: str) -> str:
    if line.endswith("\r\n"):
        return "\r\n"
    if line.endswith("\n"):
        return "\n"
    if line.endswith("\r"):
        return "\r"
    return ""


def _split_suffix(text: str) -> Tuple[str, str]:
    if not text:
        return text, ""

    m = _RX_SUFFIX.match(text)
    if not m:
        return text, ""

    body = m.group(1) or ""
    suf = text[len(body):]
    return body, suf


def _is_id_like(tok: str) -> bool:
    return bool(tok and "-" in tok and any(ch.isdigit() for ch in tok))


def _split_lead_tail_ws(s: str) -> Tuple[str, str, str]:
    lead = _RE_WS_LEAD.match(s).group(0) if s else ""
    tail = _RE_WS_TAIL.search(s).group(0) if s else ""
    core = s[len(lead): len(s) - len(tail)]
    return lead, core, tail


def _unwrap_nested_dialog_wrappers(text: str, profile: MusicaProfile) -> Tuple[str, str, str]:
    if not text:
        return text, "", ""

    current = text
    opens: list[str] = []
    closes: list[str] = []

    while True:
        matched = False
        for op, cl in profile.dialog_pairs:
            if current.startswith(op) and current.endswith(cl) and len(current) >= len(op) + len(cl):
                current = current[len(op):-len(cl)]
                opens.append(op)
                closes.insert(0, cl)
                matched = True
                break
        if not matched:
            break

    return current, "".join(opens), "".join(closes)


def _parse_rest_prefix_speaker_and_body(rest: str) -> Tuple[str, str, str, str]:
    rest_no_nl = rest.rstrip("\r\n")
    lead_ws = rest_no_nl[: len(rest_no_nl) - len(rest_no_nl.lstrip(" "))]
    s = rest_no_nl.lstrip(" ")

    if not s:
        return lead_ws, "", "", ""

    if s.startswith(("", '"', "“", "「", "『")):
        body_raw, suf = _split_suffix(s)
        return lead_ws, "", body_raw, suf

    m_id = re.match(r"^(\S+)(\s+)(.*)$", s)
    if m_id and _is_id_like(m_id.group(1)):
        after_id = m_id.group(3)
        prefix_base = lead_ws + s[: m_id.start(3)]

        m_next = re.match(r"^(\S+)(\s+)(.*)$", after_id)
        if m_next:
            cand = m_next.group(1)
            rest_after_cand = m_next.group(3)

            if cand.startswith(("@", "#")):
                speaker = cand[1:].strip()
                body_raw, suf = _split_suffix(rest_after_cand)
                prefix = lead_ws + s[: m_id.start(3) + m_next.start(3)]
                return prefix, speaker, body_raw, suf

            if re.fullmatch(r"[A-Za-z0-9_]+", cand) and rest_after_cand.startswith(("", '"', "“", "「", "『")):
                speaker = cand.strip()
                body_raw, suf = _split_suffix(rest_after_cand)
                prefix = lead_ws + s[: m_id.start(3) + m_next.start(3)]
                return prefix, speaker, body_raw, suf

        body_raw, suf = _split_suffix(after_id)
        return prefix_base, "", body_raw, suf

    m_sp = re.match(r"^([A-Za-z0-9_]+)(\s+)(.*)$", s)
    if m_sp:
        cand = m_sp.group(1)
        rest_after = m_sp.group(3)
        if rest_after.startswith(("", '"', "“", "「", "『")):
            prefix = lead_ws + s[: m_sp.start(3)]
            body_raw, suf = _split_suffix(rest_after)
            return prefix, cand.strip(), body_raw, suf

    body_raw, suf = _split_suffix(s)
    return lead_ws, "", body_raw, suf


class MusicaScParser:
    extensions = (".sc",)

    def __init__(self, profile: MusicaProfile = DEFAULT_PROFILE):
        self.profile = profile
        self.engine_id = "musica.sc" if profile.id == "default" else f"musica.sc.{profile.id}"

    def can_parse(self, *, file_path: str | None = None, data: bytes | None = None) -> bool:
        return (file_path or "").lower().endswith(".sc")

    def parse(self, data: bytes, *, file_path: str | None = None) -> ParseResult:
        text, _enc = _decode_text(data)
        entries: list[Entry] = []

        lines = text.splitlines(keepends=True)

        for i, line in enumerate(lines):
            s = line.lstrip()
            if s.startswith(";") or s.startswith("//"):
                continue

            m = _RX_MESSAGE.match(line)
            if not m:
                continue

            ws, chan, sp1, msgno, sp2, rest, nl = m.groups()
            prefix, speaker, body_raw, suf = _parse_rest_prefix_speaker_and_body(rest)

            visible_full = _decode_table(body_raw)
            if visible_full == "" or visible_full.strip() == "":
                continue
            if _RX_CONTROL_ONLY.match(visible_full):
                continue

            body_lead, body_core_raw, body_tail = _split_lead_tail_ws(body_raw)
            body_core_visible = _decode_table(body_core_raw)

            editor_core, dialog_open, dialog_close = _unwrap_nested_dialog_wrappers(
                body_core_visible,
                self.profile,
            )

            if editor_core == "" and body_core_visible != "":
                editor_core = body_core_visible

            key = f"{file_path or 'file'}:{i}"
            entries.append(
                Entry(
                    key=key,
                    text=f"{body_lead}{editor_core}{body_tail}",
                    speaker=speaker or None,
                    meta={
                        "line_index": i,
                        "ws": ws,
                        "chan": chan or "",
                        "sp1": sp1,
                        "msgno": msgno,
                        "sp2": sp2,
                        "prefix": prefix,
                        "suffix": suf,
                        "newline": nl or "",
                        "body_lead": body_lead,
                        "body_tail": body_tail,
                        "dialog_open": dialog_open,
                        "dialog_close": dialog_close,
                    },
                )
            )

        return ParseResult(engine_id=self.engine_id, entries=entries)

    def export(self, data: bytes, entries: list[Entry], *, file_path: str | None = None) -> bytes:
        original_text, enc = _decode_text(data)
        lines = original_text.splitlines(keepends=True)
        by_key = {e.key: e for e in entries if getattr(e, "key", None)}

        out_lines: list[str] = []

        for i, line in enumerate(lines):
            m = _RX_MESSAGE.match(line)
            if not m:
                out_lines.append(line)
                continue

            key = f"{file_path or 'file'}:{i}"
            ent = by_key.get(key)
            if ent is None:
                out_lines.append(line)
                continue

            ws, chan, sp1, msgno, sp2, _rest, nl = m.groups()
            meta = ent.meta or {}

            prefix = str(meta.get("prefix") or "")
            suf = str(meta.get("suffix") or "")
            newline = str(meta.get("newline") or (nl or ""))
            body_lead = str(meta.get("body_lead") or "")
            body_tail = str(meta.get("body_tail") or "")
            dialog_open = str(meta.get("dialog_open") or "")
            dialog_close = str(meta.get("dialog_close") or "")

            body_txt = ent.text or ""
            repl_eol = _line_eol(body_txt)
            if repl_eol:
                body_txt = body_txt[:-len(repl_eol)]

            body_core = body_txt
            if dialog_open or dialog_close:
                body_core = f"{dialog_open}{body_core}{dialog_close}"

            body_txt_enc = _encode_table(body_core)
            body_txt_enc = f"{body_lead}{body_txt_enc}{body_tail}"

            chan_s = str(meta.get("chan") or (chan or ""))
            out_lines.append(
                f"{ws}{chan_s}.message{sp1}{msgno}{sp2}{prefix}{body_txt_enc}{suf}{newline}"
            )

        return _encode_text("".join(out_lines), enc)
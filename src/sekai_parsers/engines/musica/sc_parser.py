from __future__ import annotations

import re
from typing import Dict

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
_RX_SUFFIX = re.compile(r"(?s)^(.*?)(\\(?:[A-Za-z]+[0-9]*))(\\(?:[A-Za-z]+[0-9]*))*?(\s*)$")
_RX_CONTROL_ONLY = re.compile(r"^\s*(?:\\[A-Za-z]+[0-9]*)+\s*$")


def _detect_encoding(data: bytes) -> str:
    if data.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig"
    for enc in ("utf-8", "cp932", "shift_jis", "latin-1"):
        try:
            data.decode(enc)
            return enc
        except UnicodeDecodeError:
            continue
    return "utf-8"


def _decode_text(data: bytes) -> tuple[str, str]:
    enc = _detect_encoding(data)
    return data.decode(enc, errors="replace"), enc


def _encode_text(text: str, enc: str) -> bytes:
    return text.encode(enc, errors="replace")


def _decode_table(s: str) -> str:
    if not s:
        return s
    return "".join(MAP_DECODE.get(ch, ch) for ch in s)


def _encode_table(s: str) -> str:
    if not s:
        return s
    return "".join(MAP_ENCODE.get(ch, ch) for ch in s)


def _split_suffix(text: str) -> tuple[str, str]:
    if not text:
        return text, ""

    m = _RX_SUFFIX.match(text)
    if not m:
        return text, ""

    body = m.group(1) or ""
    suf = text[len(body) :]
    if not suf:
        return text, ""
    return body, suf


def _is_id_like(tok: str) -> bool:
    return bool(tok and "-" in tok and any(ch.isdigit() for ch in tok))


def _split_lead_tail_ws(s: str) -> tuple[str, str, str]:
    lead = _RE_WS_LEAD.match(s).group(0) if s else ""
    tail = _RE_WS_TAIL.search(s).group(0) if s else ""
    core = s[len(lead) : len(s) - len(tail)]
    return lead, core, tail


def _parse_rest_prefix_speaker_and_body(rest: str) -> tuple[str, str, str, str]:
    rest_no_nl = rest.rstrip("\r\n")

    lead_ws = rest_no_nl[: len(rest_no_nl) - len(rest_no_nl.lstrip(" "))]
    s = rest_no_nl.lstrip(" ")

    if not s:
        return lead_ws, "", "", ""

    if s.startswith(("\x81", '"', "“", "「", "『")):
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

            if re.fullmatch(r"[A-Za-z0-9_]+", cand) and rest_after_cand.startswith(("\x81", '"', "“", "「", "『")):
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
        if rest_after.startswith(("\x81", '"', "“", "「", "『")):
            prefix = lead_ws + s[: m_sp.start(3)]
            body_raw, suf = _split_suffix(rest_after)
            return prefix, cand.strip(), body_raw, suf

    body_raw, suf = _split_suffix(s)
    return lead_ws, "", body_raw, suf


class MusicaScParser:
    engine_id = "musica.sc"
    extensions = (".sc",)

    def can_parse(self, *, file_path: str | None = None, data: bytes | None = None) -> bool:
        fp = (file_path or "").lower()
        if fp.endswith(".sc"):
            return True
        if data:
            try:
                text, _ = _decode_text(data)
            except Exception:
                return False
            head = "\n".join(text.splitlines()[:80])
            return ".message" in head and ".stage" in head
        return False

    def parse(self, data: bytes, *, file_path: str | None = None) -> ParseResult:
        text, _enc = _decode_text(data)
        entries: list[Entry] = []
        lines = text.splitlines(keepends=True)

        key_idx = 0
        for i, line in enumerate(lines):
            s = line.lstrip()
            if s.startswith(";") or s.startswith("//"):
                continue

            m = _RX_MESSAGE.match(line)
            if not m:
                continue

            ws, chan, sp1, msgno, sp2, rest, nl = m.groups()
            prefix, speaker, body_raw, suf = _parse_rest_prefix_speaker_and_body(rest)
            visible = _decode_table(body_raw)

            if visible == "" or visible.strip() == "":
                continue
            if _RX_CONTROL_ONLY.match(visible):
                continue

            body_lead, _body_core, body_tail = _split_lead_tail_ws(body_raw)
            key = f"{file_path or 'file'}:{key_idx}"
            key_idx += 1
            entries.append(
                Entry(
                    key=key,
                    text=visible,
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
                    },
                )
            )

        return ParseResult(engine_id=self.engine_id, entries=entries)

    def export(self, data: bytes, entries: list[Entry], *, file_path: str | None = None) -> bytes:
        original_text, enc = _decode_text(data)
        lines = original_text.splitlines(keepends=True)
        by_key = {e.key: e for e in entries if getattr(e, "key", None)}

        key_idx = 0
        for li, line in enumerate(lines):
            s = line.lstrip()
            if s.startswith(";") or s.startswith("//"):
                continue

            m = _RX_MESSAGE.match(line)
            if not m:
                continue

            candidate_key = f"{file_path or 'file'}:{key_idx}"
            key_idx += 1
            ent = by_key.get(candidate_key)
            if ent is None:
                continue

            ws, chan, sp1, msgno, sp2, _rest, nl = m.groups()
            meta = ent.meta or {}
            prefix = str(meta.get("prefix") or "")
            suf = str(meta.get("suffix") or "")
            newline = str(meta.get("newline") or (nl or ""))
            body_lead = str(meta.get("body_lead") or "")
            body_tail = str(meta.get("body_tail") or "")
            chan_s = str(meta.get("chan") or (chan or ""))

            body_txt = ent.text if isinstance(ent.text, str) and ent.text != "" else ""
            body_txt_enc = _encode_table(body_txt)
            body_txt_enc = f"{body_lead}{body_txt_enc}{body_tail}"
            lines[li] = f"{ws}{chan_s}.message{sp1}{msgno}{sp2}{prefix}{body_txt_enc}{suf}{newline}"

        return _encode_text("".join(lines), enc)

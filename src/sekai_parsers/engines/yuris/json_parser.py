from __future__ import annotations

import json
import re
from dataclasses import dataclass

from ...api import Entry, ParseResult


_RX_NUMBER_ONLY = re.compile(r"^\d+$")


@dataclass(frozen=True, slots=True)
class YuRisProfile:
    id: str = "default"
    ignore_exact: tuple[str, ...] = ()
    ignore_prefixes: tuple[str, ...] = ()
    ignore_regexes: tuple[str, ...] = ()
    speaker_line_regexes: tuple[str, ...] = (r"^([^:\n]{1,40}):\s*(.+)$",)
    dialog_pairs: tuple[tuple[str, str], ...] = (
        ("“", "”"),
        ('"', '"'),
        ("「", "」"),
        ("『", "』"),
    )


DEFAULT_PROFILE = YuRisProfile()


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


def _build_ignore_regexes(profile: YuRisProfile) -> list[re.Pattern[str]]:
    return [re.compile(rx) for rx in profile.ignore_regexes]


def _build_speaker_regexes(profile: YuRisProfile) -> list[re.Pattern[str]]:
    return [re.compile(rx) for rx in profile.speaker_line_regexes]


def _looks_like_command(text: str, profile: YuRisProfile, ignore_regexes: list[re.Pattern[str]]) -> bool:
    s = text.strip()
    if not s:
        return True

    if _RX_NUMBER_ONLY.match(s):
        return True

    if s in profile.ignore_exact:
        return True

    for prefix in profile.ignore_prefixes:
        if s.startswith(prefix):
            return True

    for rx in ignore_regexes:
        if rx.match(s):
            return True

    return False


def _unwrap_dialog(text: str, profile: YuRisProfile) -> tuple[str, str, str]:
    s = text
    opens: list[str] = []
    closes: list[str] = []

    while True:
        matched = False
        for op, cl in profile.dialog_pairs:
            if s.startswith(op) and s.endswith(cl) and len(s) >= len(op) + len(cl):
                s = s[len(op):-len(cl)]
                opens.append(op)
                closes.insert(0, cl)
                matched = True
                break
        if not matched:
            break

    return s, "".join(opens), "".join(closes)


def _looks_like_speaker_name(s: str) -> bool:
    s = s.strip()
    if not s:
        return False

    if len(s) > 32:
        return False

    if s.count(" ") > 2:
        return False

    if any(ch in s for ch in ".!?;()[]{}=/\\"):
        return False

    parts = s.split()
    for part in parts:
        if not part:
            return False
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_\-']*", part):
            return False

    return True


def _split_speaker(
    text: str,
    profile: YuRisProfile,
    speaker_regexes: list[re.Pattern[str]],
    ignore_regexes: list[re.Pattern[str]],
) -> tuple[str | None, str, str, str]:
    s = text.strip()

    for rx in speaker_regexes:
        m = rx.match(s)
        if not m:
            continue

        speaker = m.group(1).strip()
        body = m.group(2)

        if not _looks_like_speaker_name(speaker):
            continue

        if _looks_like_command(speaker, profile, ignore_regexes):
            return None, text, "", ""

        body_clean, dialog_open, dialog_close = _unwrap_dialog(body, profile)
        return speaker, body_clean, dialog_open, dialog_close

    body_clean, dialog_open, dialog_close = _unwrap_dialog(text, profile)
    return None, body_clean, dialog_open, dialog_close


class YuRisJsonParser:
    extensions = (".json",)

    def __init__(self, profile: YuRisProfile = DEFAULT_PROFILE):
        self.profile = profile
        self.engine_id = "yuris.json" if profile.id == "default" else f"yuris.json.{profile.id}"
        self._ignore_regexes = _build_ignore_regexes(profile)
        self._speaker_regexes = _build_speaker_regexes(profile)

    def can_parse(self, *, file_path: str | None = None, data: bytes | None = None) -> bool:
        if (file_path or "").lower().endswith(".json"):
            return True

        if data:
            try:
                text, _ = _decode_text(data)
                obj = json.loads(text)
                return isinstance(obj, dict)
            except Exception:
                return False

        return False

    def parse(self, data: bytes, *, file_path: str | None = None) -> ParseResult:
        text, _enc = _decode_text(data)

        try:
            obj = json.loads(text)
        except Exception as e:
            raise RuntimeError(f"JSON inválido: {e}") from e

        if not isinstance(obj, dict):
            raise RuntimeError("Formato YU-RIS inválido: raiz JSON não é objeto.")

        entries: list[Entry] = []

        for block_id, items in obj.items():
            if not isinstance(items, list):
                continue

            for idx, raw in enumerate(items):
                if not isinstance(raw, str):
                    continue

                if _looks_like_command(raw, self.profile, self._ignore_regexes):
                    continue

                speaker, body, dialog_open, dialog_close = _split_speaker(
                    raw,
                    self.profile,
                    self._speaker_regexes,
                    self._ignore_regexes,
                )

                if not body.strip():
                    continue

                key = f"{block_id}:{idx}"
                entries.append(
                    Entry(
                        key=key,
                        text=body,
                        speaker=speaker,
                        meta={
                            "block_id": block_id,
                            "item_index": idx,
                            "has_speaker_prefix": speaker is not None,
                            "speaker_prefix": f"{speaker}: " if speaker else "",
                            "dialog_open": dialog_open,
                            "dialog_close": dialog_close,
                            "original_raw": raw,
                        },
                    )
                )

        return ParseResult(engine_id=self.engine_id, entries=entries)

    def export(self, data: bytes, entries: list[Entry], *, file_path: str | None = None) -> bytes:
        text, enc = _decode_text(data)

        try:
            obj = json.loads(text)
        except Exception as e:
            raise RuntimeError(f"JSON inválido: {e}") from e

        if not isinstance(obj, dict):
            raise RuntimeError("Formato YU-RIS inválido: raiz JSON não é objeto.")

        by_key = {e.key: e for e in entries if getattr(e, "key", None)}

        for block_id, items in obj.items():
            if not isinstance(items, list):
                continue

            for idx, _raw in enumerate(items):
                key = f"{block_id}:{idx}"
                ent = by_key.get(key)
                if ent is None:
                    continue

                meta = ent.meta or {}
                has_speaker_prefix = bool(meta.get("has_speaker_prefix"))
                speaker_prefix = str(meta.get("speaker_prefix") or "")
                dialog_open = str(meta.get("dialog_open") or "")
                dialog_close = str(meta.get("dialog_close") or "")
                new_text = ent.text or ""

                if dialog_open or dialog_close:
                    new_text = f"{dialog_open}{new_text}{dialog_close}"

                if has_speaker_prefix:
                    items[idx] = f"{speaker_prefix}{new_text}"
                else:
                    items[idx] = new_text

        out = json.dumps(obj, ensure_ascii=False, indent=3)
        return _encode_text(out, enc)
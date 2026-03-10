from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from ...api import Entry, ParseResult


_RX_SPEAKER_LINE = re.compile(r"^([^:\n]{1,80}):\s*(.+)$")
_RX_NUMBER_ONLY = re.compile(r"^\d+$")


@dataclass(frozen=True, slots=True)
class YuRisProfile:
    id: str = "default"
    ignore_exact: tuple[str, ...] = ()
    ignore_prefixes: tuple[str, ...] = ()
    ignore_regexes: tuple[str, ...] = ()
    speaker_line_regexes: tuple[str, ...] = (r"^([^:\n]{1,80}):\s*(.+)$",)


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
    out: list[re.Pattern[str]] = []
    for rx in profile.ignore_regexes:
        out.append(re.compile(rx))
    return out


def _build_speaker_regexes(profile: YuRisProfile) -> list[re.Pattern[str]]:
    out: list[re.Pattern[str]] = []
    for rx in profile.speaker_line_regexes:
        out.append(re.compile(rx))
    return out


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


def _split_speaker(
    text: str,
    profile: YuRisProfile,
    speaker_regexes: list[re.Pattern[str]],
    ignore_regexes: list[re.Pattern[str]],
) -> tuple[str | None, str]:
    s = text.strip()

    for rx in speaker_regexes:
        m = rx.match(s)
        if not m:
            continue

        speaker = m.group(1).strip()
        body = m.group(2)

        if _looks_like_command(speaker, profile, ignore_regexes):
            return None, text

        return speaker, body

    return None, text


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

                speaker, body = _split_speaker(
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

            for idx, raw in enumerate(items):
                key = f"{block_id}:{idx}"
                ent = by_key.get(key)
                if ent is None:
                    continue

                meta = ent.meta or {}
                has_speaker_prefix = bool(meta.get("has_speaker_prefix"))
                speaker_prefix = str(meta.get("speaker_prefix") or "")
                new_text = ent.text or ""

                if has_speaker_prefix:
                    items[idx] = f"{speaker_prefix}{new_text}"
                else:
                    items[idx] = new_text

        out = json.dumps(obj, ensure_ascii=False, indent=3)
        return _encode_text(out, enc)
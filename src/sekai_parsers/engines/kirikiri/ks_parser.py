from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from ...api import Entry, ParseResult
from ...utils.text import normalize_newlines


_CN_TAG_RE = re.compile(r'^\[cn\s+name="([^"]+)"(?:[^\]]*)\]\s*$', re.IGNORECASE)
# Linha de tag/comando (não-texto): [tag ...] ou label *xxx
_TAG_LINE_RE = re.compile(r'^\s*(\[[^\]]*\]|\*[^\s].*)\s*$')


@dataclass(slots=True)
class _ParseState:
    speaker: str | None = None


class KiriKiriKsParser:
    """
    Parser KiriKiri (.ks) focado em round-trip estável.

    Padrão suportado (ex.: Forbidden Love Wife Sister):
    - Tag de personagem: [cn name="..."] (pode ter outros atributos)
    - As linhas seguintes (não-tag) viram texto até a próxima tag/label
    - Linhas começando com ';' são comentários (ignoradas)
    """

    engine_id = "kirikiri.ks"
    extensions = (".ks",)

    # -----------------------
    # Detecção
    # -----------------------

    def can_parse(self, *, file_path: str | None = None, data: bytes | None = None) -> bool:
        # Heurística simples:
        # - extensão .ks OU presença de padrões comuns (@, [tag], *label, ;comment)
        fp = (file_path or "").lower()
        if fp.endswith(".ks"):
            return True

        sample = (data or b"")[:4096]
        try:
            s = sample.decode("utf-8", errors="ignore")
        except Exception:
            return False

        s_strip = s.strip()
        if not s_strip:
            return False

        if "[cn " in s or "\n@" in s or s_strip.startswith("@") or "\n[" in s or s_strip.startswith("["):
            return True
        if "\n*" in s or s_strip.startswith("*"):
            return True
        if "\n;" in s or s_strip.startswith(";"):
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
        i = 0
        key_idx = 0

        lines = text_nl.splitlines(keepends=True)

        def is_comment(line: str) -> bool:
            return line.lstrip().startswith(";")

        while i < len(lines):
            line = lines[i]

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

            # Texto: consome linhas consecutivas que não sejam tag/comment/blank
            block_lines = [line]
            i += 1
            while i < len(lines):
                nxt = lines[i]
                if is_comment(nxt) or not nxt.strip():
                    break
                if _CN_TAG_RE.match(nxt.strip()):
                    break
                if _TAG_LINE_RE.match(nxt.strip()):
                    break
                block_lines.append(nxt)
                i += 1

            block_text = "".join(block_lines)

            key = f"{file_path or 'file'}:{key_idx}"
            key_idx += 1

            entries.append(
                Entry(
                    key=key,
                    text=block_text,
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
        """
        Export simples:
        - Reparseia o arquivo para obter a mesma segmentação/keys
        - Substitui os blocos na ordem, usando entries[*].text como conteúdo final
          (a UI vai fornecer text=tradução no adapter)
        """
        # Reparse para gerar as keys em ordem estável
        parsed = self.parse(data, file_path=file_path)
        parsed_entries = parsed.entries

        # Map key -> replacement text (Entry.text)
        by_key: dict[str, str] = {e.key: e.text for e in entries if getattr(e, "key", None)}

        # Reconstrói mantendo tudo que não é texto como estava:
        # Estratégia simples: re-walk do arquivo e substitui cada bloco de texto encontrado.
        original_text = normalize_newlines(data.decode("utf-8", errors="replace"))
        lines = original_text.splitlines(keepends=True)

        def is_comment(line: str) -> bool:
            return line.lstrip().startswith(";")

        out_lines: list[str] = []
        i = 0
        key_idx = 0
        state = _ParseState()

        while i < len(lines):
            line = lines[i]

            if is_comment(line) or not line.strip():
                out_lines.append(line)
                i += 1
                continue

            m_cn = _CN_TAG_RE.match(line.strip())
            if m_cn:
                state.speaker = m_cn.group(1)
                out_lines.append(line)
                i += 1
                continue

            if _TAG_LINE_RE.match(line.strip()):
                out_lines.append(line)
                i += 1
                continue

            # texto (mesma regra do parse)
            block_lines = [line]
            i += 1
            while i < len(lines):
                nxt = lines[i]
                if is_comment(nxt) or not nxt.strip():
                    break
                if _CN_TAG_RE.match(nxt.strip()):
                    break
                if _TAG_LINE_RE.match(nxt.strip()):
                    break
                block_lines.append(nxt)
                i += 1

            key = f"{file_path or 'file'}:{key_idx}"
            key_idx += 1

            repl = by_key.get(key)
            if repl is None:
                out_lines.extend(block_lines)
            else:
                out_lines.append(repl)

        return "".join(out_lines).encode("utf-8")

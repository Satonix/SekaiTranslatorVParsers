# src/sekai_parsers/engines/kirikiri/ks_parser.py
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Iterable, Optional

from ...utils.text import normalize_newlines
from .ks_model import TextSpan

# ---------------------------------------------------------------------
# Regras do dialeto (Forbidden Love Wife Sister)
# ---------------------------------------------------------------------

_CN_TAG_RE = re.compile(r'^\[cn\s+name="([^"]+)"(?:[^\]]*)\]\s*$', re.IGNORECASE)
# Qualquer linha que seja um comando/tag (ex: [xxx] ou *label) é controle.
_TAG_LINE_RE = re.compile(r'^\s*(\[[^\]]*\]|\*[^\s].*)\s*$')


@dataclass(slots=True)
class _ParseState:
    speaker: str | None = None

@dataclass(slots=True)
class _LegacyEntry:
    key: str
    text: str
    speaker: str | None = None
    meta: dict | None = None


# ---------------------------------------------------------------------
# Tipos mínimos para compat com o sekai-ui (manager espera .blocks e .meta)
# ---------------------------------------------------------------------

@dataclass(slots=True)
class TextBlock:
    block_id: str
    text: str
    speaker: str | None = None
    translatable: bool = True
    meta: dict[str, Any] | None = None


@dataclass(slots=True)
class ParseOutput:
    blocks: list[TextBlock]
    meta: Any  # vamos guardar o ParseResult legacy aqui


@dataclass(slots=True)
class CompileOutput:
    data: bytes


# ---------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------

class KiriKiriKsParser:
    """
    KiriKiri `.ks` parser focado em round-trip estável.

    Padrão suportado (como em *Forbidden Love Wife Sister*):
    - Tag de speaker: [cn name="..."] (pode ter outros atributos)
    - As linhas seguintes NÃO-tag são texto até a próxima tag
    - Linhas começando com ';' são comentários e são ignoradas
    """

    engine_id = "kirikiri.ks"
    extensions = (".ks",)

    # -------------------------
    # Contrato NOVO (sekai-ui)
    # -------------------------

    def can_parse(self, *, file_path: str = "", data: bytes = b"") -> bool:
        # Detecção simples por extensão
        fp = (file_path or "").lower()
        if fp.endswith(".ks"):
            return True
        return False

    def parse(self, *, file_path: str = "", data: bytes = b"") -> ParseOutput:
        legacy = self.parse_legacy(data, file_path=file_path)

        blocks: list[TextBlock] = []
        for e in legacy.entries:
            blocks.append(
                TextBlock(
                    block_id=str(e.key),
                    text=str(getattr(e, 'text', '')),
                    speaker=getattr(e, "speaker", None),
                    translatable=True,
                    meta=getattr(e, "meta", {}) or {},
                )
            )

        # meta carrega o ParseResult legacy inteiro (necessário pro export)
        return ParseOutput(blocks=blocks, meta=legacy)

    def compile(
        self,
        *,
        file_path: str = "",
        blocks: list[Any] | None = None,
        meta: Any = None,
    ) -> CompileOutput:
        """
        Converte blocks -> entries e chama export_legacy(meta, entries).
        IMPORTANTE: meta DEVE ser o ParseResult original retornado pelo parse().
        """
        if meta is None:
            raise RuntimeError("compile() requer meta=ParseResult (round-trip).")

        # Import local pra não quebrar imports em tempo de carga
        from ...api import Entry  # type: ignore

        entries: list[Entry] = []
        for b in (blocks or []):
            key = getattr(b, "block_id", None) or getattr(b, "key", None)
            if not key:
                continue

            text = getattr(b, "text", "")
            speaker = getattr(b, "speaker", None)
            bmeta = getattr(b, "meta", None) or {}

            # export_legacy usa translation se não vazia, senão original.
            # Para manter original quando não houver tradução, colocamos original=text também.
            entries.append(
                Entry(
                    key=str(key),
                    original=str(text),
                    translation=str(text),
                    speaker=speaker,
                    meta=dict(bmeta) if isinstance(bmeta, dict) else {},
                )
            )

        out = self.export_legacy(meta, entries)
        return CompileOutput(data=out)

    # -------------------------
    # Contrato LEGACY (repo antigo)
    # -------------------------

    def parse_legacy(self, data: bytes, *, file_path: str | None = None):
        # Import local pra evitar ciclos no import do pacote
# type: ignore

        text = data.decode("utf-8", errors="replace")
        text_nl = normalize_newlines(text)

        spans: list[TextSpan] = []
        entries: list[Entry] = []

        state = _ParseState()
        i = 0
        key_idx = 0

        lines = text_nl.splitlines(keepends=True)
        offset = 0

        def is_comment(line: str) -> bool:
            stripped = line.lstrip()
            return stripped.startswith(";")

        while i < len(lines):
            line = lines[i]
            line_start = offset
            offset += len(line)

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

            # Text block: consome linhas consecutivas que não são tag/comentário
            block_start_off = line_start
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

            start = block_start_off
            end = block_start_off + len(block_text)

            key = f"{file_path or 'file'}:{key_idx}"
            key_idx += 1

            entries.append(
                _LegacyEntry(
                    key=key,
                    text=block_text,
                    speaker=state.speaker,
                    meta={},
                )
            )
            spans.append(TextSpan(start=start, end=end, key=key))

        return LegacyParseResult(
            engine_id=self.engine_id,
            original_text=text_nl,
            entries=entries,
            spans=spans,
        )

    def export_legacy(self, result: Any, entries: Iterable[Any]) -> bytes:
        # Map block_id -> replacement text (block.text)
        by_key: dict[str, str] = {}
        for b in entries:
            bid = str(getattr(b, "block_id", "") or "")
            if not bid:
                continue
            by_key[bid] = str(getattr(b, "text", "") or "")

        out = str(getattr(result, "original_text", ""))

        spans = getattr(result, "spans", None) or []
        # aplica de trás pra frente pra manter offsets
        for sp in sorted(spans, key=lambda s: s.start, reverse=True):
            repl = by_key.get(getattr(sp, "key", None))
            if repl is None:
                continue
            out = out[: sp.start] + repl + out[sp.end :]

        return out.encode("utf-8")

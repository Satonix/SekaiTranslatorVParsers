from __future__ import annotations

from sekai_parsers.engines.musica.sc_parser import MusicaScParser
from sekai_parsers.api import Entry


def test_parse_and_export_roundtrip():
    parser = MusicaScParser()
    data = (
        b".stage 1\r\n"
        b".message 0 abc-01 @Alice \"Ol$ mundo\"\\a\r\n"
        b".message 1 xyz-02 \"T)quio\"\\v\\a\r\n"
    )

    parsed = parser.parse(data, file_path="sample.sc")
    assert parsed.engine_id == "musica.sc"
    assert len(parsed.entries) == 2
    assert parsed.entries[0].speaker == "Alice"
    assert "Olá mundo" in parsed.entries[0].text
    assert "Tóquio" in parsed.entries[1].text

    out = parser.export(data, parsed.entries, file_path="sample.sc")
    assert out == data


def test_translation_edit_applies():
    parser = MusicaScParser()
    data = b".stage 1\n.message 0 abc-01 @Alice \"Ol$ mundo\"\\a\n"
    parsed = parser.parse(data, file_path="sample.sc")
    e0 = parsed.entries[0]
    parsed.entries[0] = Entry(key=e0.key, text='"Tradu&$o"', speaker=e0.speaker, meta=e0.meta)
    out = parser.export(data, parsed.entries, file_path="sample.sc")
    assert b'Tradu&$o' in out

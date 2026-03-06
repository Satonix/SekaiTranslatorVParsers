from __future__ import annotations

from sekai_parsers.engines.musica.sc_parser import MusicaScParser


def test_roundtrip_preserves_original_bytes_for_unmodified_script():
    parser = MusicaScParser()
    text = (
        ".stage bg001\r\n"
        ".message 0 001-01 @Hero 「Ola」\\a\r\n"
        ".message 0 \\w\\a\r\n"
        ".message 0 001-02 「Narration」\r\n"
    )
    data = text.encode("cp932", errors="replace")

    parsed = parser.parse(data, file_path="scene.sc")
    assert len(parsed.entries) == 2
    assert parsed.entries[0].speaker == "Hero"
    assert parsed.entries[0].text == "「Ola」"
    assert parsed.entries[1].speaker is None
    assert parsed.entries[1].text == "「Narration」"

    out = parser.export(data, parsed.entries, file_path="scene.sc")
    assert out == data


def test_translation_edit_reencodes_custom_portuguese_map_and_preserves_suffix():
    parser = MusicaScParser()
    text = ".message 0 001-01 @Hero 「Teste」\\a\r\n"
    data = text.encode("cp932", errors="replace")

    parsed = parser.parse(data, file_path="scene.sc")
    e0 = parsed.entries[0]
    parsed.entries[0] = type(e0)(
        key=e0.key,
        speaker=e0.speaker,
        meta=e0.meta,
        text="çáãéóú",
    )

    out = parser.export(data, parsed.entries, file_path="scene.sc")
    out_text = out.decode("cp932")
    assert "&$^%)(" in out_text
    assert out_text.endswith("\\a\r\n")

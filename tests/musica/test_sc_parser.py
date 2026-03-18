from __future__ import annotations

from sekai_parsers.engines.musica.sc_parser import MusicaScParser
from sekai_parsers.engines.musica.profiles.ef import EF_PROFILE


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
    assert parsed.entries[0].text == "Ola"
    assert parsed.entries[1].speaker is None
    assert parsed.entries[1].text == "Narration"

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



def test_ascii_only_script_keeps_cp932_without_bom():
    parser = MusicaScParser()
    data = b"#include 111_05_ero.sc\r\n.chain 111_06.sc\r\n.end\r\n"

    parsed = parser.parse(data, file_path="scene.sc")
    out = parser.export(data, parsed.entries, file_path="scene.sc")

    assert out == data
    assert not out.startswith(b"\xef\xbb\xbf")



def test_trailing_whitespace_roundtrip_is_preserved():
    parser = MusicaScParser()
    text = ".message 0 001-01 @Hero \"Line with tail \"\r\n"
    data = text.encode("cp932", errors="replace")

    parsed = parser.parse(data, file_path="scene.sc")
    out = parser.export(data, parsed.entries, file_path="scene.sc")

    assert out == data



def test_speaker_plus_control_only_line_is_not_extracted():
    parser = MusicaScParser()
    text = ".message 2240  Yuuko \\v\\a\r\n"
    data = text.encode("cp932", errors="replace")

    parsed = parser.parse(data, file_path="scene.sc")

    assert parsed.entries == []
    out = parser.export(data, parsed.entries, file_path="scene.sc")
    assert out == data


def test_ef_profile_extracts_speaker_and_unwraps_ef_dialog_markers():
    parser = MusicaScParser(EF_PROFILE)
    text = ".message 260 yuk-000_01-0019 #Yuuko 挌Good evening.拮\r\n"
    data = text.encode("cp932", errors="replace")

    parsed = parser.parse(data, file_path="scene.sc")

    assert len(parsed.entries) == 1
    assert parsed.entries[0].speaker == "Yuuko"
    assert parsed.entries[0].text == "Good evening."

    out = parser.export(data, parsed.entries, file_path="scene.sc")
    assert out == data


def test_control_with_symbol_suffix_is_not_extracted():
    parser = MusicaScParser(EF_PROFILE)
    text = ".message 0 \\a戞\r\n"
    data = text.encode("cp932", errors="replace")

    parsed = parser.parse(data, file_path="scene.sc")

    assert parsed.entries == []
    out = parser.export(data, parsed.entries, file_path="scene.sc")
    assert out == data

<<<<<<< HEAD
from __future__ import annotations

from pathlib import Path

from sekai_parsers.engines.kirikiri.ks_parser import KirikiriKsParser


def test_roundtrip_fixture():
    parser = KirikiriKsParser()
    p = Path(__file__).parent.parent / "fixtures" / "forbidden_love_wife_sister" / "01_01_01.ks"
    data = p.read_bytes()

    parsed = parser.parse(data, file_path=str(p))
    exported = parser.export(data, parsed.entries, file_path=str(p))

    assert exported == data


def test_translation_edit_applies_and_keeps_structure():
    parser = KirikiriKsParser()
    p = Path(__file__).parent.parent / "fixtures" / "forbidden_love_wife_sister" / "01_01_01.ks"
    data = p.read_bytes()

    parsed = parser.parse(data)
    assert len(parsed.entries) >= 2

    # Change first narrative line
    e0 = parsed.entries[0]
    parsed.entries[0] = type(e0)(
        key=e0.key,
        speaker=e0.speaker,
        meta=e0.meta,
        text=e0.text.replace("A few days later", "A couple days later"),
    )

    out = parser.export(data, parsed.entries)
    assert b"A couple days later" in out
    assert b"[cn name=" in out  # tags still present
=======
from __future__ import annotations

from pathlib import Path

from sekai_parsers.engines.kirikiri.ks_parser import KirikiriKsParser


def test_roundtrip_fixture():
    parser = KirikiriKsParser()
    p = Path(__file__).parent.parent / "fixtures" / "forbidden_love_wife_sister" / "01_01_01.ks"
    data = p.read_bytes()

    parsed = parser.parse(data, file_path=str(p))
    exported = parser.export(data, parsed.entries, file_path=str(p))

    assert exported == data


def test_translation_edit_applies_and_keeps_structure():
    parser = KirikiriKsParser()
    p = Path(__file__).parent.parent / "fixtures" / "forbidden_love_wife_sister" / "01_01_01.ks"
    data = p.read_bytes()

    parsed = parser.parse(data)
    assert len(parsed.entries) >= 2

    # Change first narrative line
    e0 = parsed.entries[0]
    parsed.entries[0] = type(e0)(
        key=e0.key,
        speaker=e0.speaker,
        meta=e0.meta,
        text=e0.text.replace("A few days later", "A couple days later"),
    )

    out = parser.export(data, parsed.entries)
    assert b"A couple days later" in out
    assert b"[cn name=" in out  # tags still present
>>>>>>> 824d17b2d4c0216bd447d690127f0ff6d4259d4a

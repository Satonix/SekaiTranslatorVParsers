from __future__ import annotations

from ..ast_parser import ArtemisProfile, DEFAULT_PROFILE

NUKITASHI_PROFILE = ArtemisProfile(
    id="nukitashi",
    rx_en_block=DEFAULT_PROFILE.rx_en_block,
    rx_text=DEFAULT_PROFILE.rx_text,
)

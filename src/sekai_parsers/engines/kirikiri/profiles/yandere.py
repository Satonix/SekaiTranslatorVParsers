from __future__ import annotations
import re
from ..ks_parser import KiriKiriProfile

YANDERE_PROFILE = KiriKiriProfile(
    id="yandere",
    speaker_tag=re.compile(r'\[P_NAME\b[^\]]*\bs_cn="([^"]+)"', re.IGNORECASE),
    rx_comment=re.compile(r'^\s*;'),
    rx_label=re.compile(r'^\s*\*'),
    rx_tag_only=re.compile(r'^\s*(?:\[[^\]]+\]\s*)+$'),
)
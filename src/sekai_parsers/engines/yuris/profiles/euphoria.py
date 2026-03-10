from __future__ import annotations

from ..json_parser import YuRisProfile


EUPHORIA_PROFILE = YuRisProfile(
    id="euphoria",
    ignore_exact=(
        "NEM",
    ),
    ignore_prefixes=(
        "\\\\GO(",
        "KOE_",
        "SE_",
        "bg_",
        "st_",
    ),
    ignore_regexes=(
        r"^\\\\[A-Za-z_]+\s*\(.*\)$",
        r"^KOE_[A-Za-z0-9_]+$",
        r"^SE_[A-Za-z0-9_]+$",
        r"^bg_[A-Za-z0-9_]+$",
        r"^st_[A-Za-z0-9_]+$",
        r"^[A-Z0-9_]{2,12}$",
    ),
    speaker_line_regexes=(
        r"^([^:\n]{1,80}):\s*(.+)$",
    ),
)
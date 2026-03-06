from ...engine_registry import register_engine
from .sc_parser import MusicaScParser, DEFAULT_PROFILE
from .profiles.ef import EF_PROFILE
from .profiles.eden import EDEN_PROFILE

register_engine("musica.sc", lambda: MusicaScParser(DEFAULT_PROFILE))
register_engine("musica.sc.ef", lambda: MusicaScParser(EF_PROFILE))
register_engine("musica.sc.eden", lambda: MusicaScParser(EDEN_PROFILE))
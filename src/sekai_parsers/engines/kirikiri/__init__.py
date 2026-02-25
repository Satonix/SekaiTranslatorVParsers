from ...engine_registry import register_engine
from .ks_parser import KiriKiriKsParser, DEFAULT_PROFILE
from .profiles.yandere import YANDERE_PROFILE

register_engine("kirikiri.ks", lambda: KiriKiriKsParser(DEFAULT_PROFILE))
register_engine("kirikiri.ks.yandere", lambda: KiriKiriKsParser(YANDERE_PROFILE))
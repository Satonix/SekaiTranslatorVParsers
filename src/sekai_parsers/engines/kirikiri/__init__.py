<<<<<<< HEAD
from ...engine_registry import register_engine
from .ks_parser import KiriKiriKsParser, DEFAULT_PROFILE
from .profiles.yandere import YANDERE_PROFILE

register_engine("kirikiri.ks", lambda: KiriKiriKsParser(DEFAULT_PROFILE))
=======
from ...engine_registry import register_engine
from .ks_parser import KiriKiriKsParser, DEFAULT_PROFILE
from .profiles.yandere import YANDERE_PROFILE

register_engine("kirikiri.ks", lambda: KiriKiriKsParser(DEFAULT_PROFILE))
>>>>>>> 824d17b2d4c0216bd447d690127f0ff6d4259d4a
register_engine("kirikiri.ks.yandere", lambda: KiriKiriKsParser(YANDERE_PROFILE))
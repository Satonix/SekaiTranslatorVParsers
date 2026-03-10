from ...engine_registry import register_engine
from .json_parser import YuRisJsonParser, DEFAULT_PROFILE
from .profiles.euphoria import EUPHORIA_PROFILE

register_engine("yuris.json", lambda: YuRisJsonParser(DEFAULT_PROFILE))
register_engine("yuris.json.euphoria", lambda: YuRisJsonParser(EUPHORIA_PROFILE))
from ...engine_registry import register_engine
from .ast_parser import ArtemisAstParser, DEFAULT_PROFILE
from .profiles.nukitashi import NUKITASHI_PROFILE

register_engine("artemis.ast",            lambda: ArtemisAstParser(DEFAULT_PROFILE))
register_engine("artemis.ast.nukitashi",  lambda: ArtemisAstParser(NUKITASHI_PROFILE))

from ...engine_registry import register_engine
from .sc_parser import MusicaScParser

register_engine("musica.sc", MusicaScParser)

<<<<<<< HEAD
class ParserError(Exception):
    """Base error for parser failures."""


class UnsupportedFormatError(ParserError):
    """Raised when a parser cannot handle the given file."""


class RoundTripError(ParserError):
    """Raised when a round-trip invariant is violated in strict mode."""
=======
class ParserError(Exception):
    """Base error for parser failures."""


class UnsupportedFormatError(ParserError):
    """Raised when a parser cannot handle the given file."""


class RoundTripError(ParserError):
    """Raised when a round-trip invariant is violated in strict mode."""
>>>>>>> 824d17b2d4c0216bd447d690127f0ff6d4259d4a

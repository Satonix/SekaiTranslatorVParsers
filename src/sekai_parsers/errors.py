class ParserError(Exception):
    """Base error for parser failures."""


class UnsupportedFormatError(ParserError):
    """Raised when a parser cannot handle the given file."""


class RoundTripError(ParserError):
    """Raised when a round-trip invariant is violated in strict mode."""

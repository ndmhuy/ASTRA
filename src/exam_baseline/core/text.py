"""Lexical comparison shared by matrix validation and input preparation."""

import unicodedata


def normalized_text(text: str) -> str:
    """Conservative lexical comparison, not semantic duplicate detection."""
    # Preserve operators: 'x+1' and 'x-1' must never collapse to the same stem.
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split()).rstrip(".?!")

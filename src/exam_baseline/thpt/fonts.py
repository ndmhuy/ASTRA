"""Explicit output compatibility profile; never modify the archived original template."""

from typing import Literal

FontProfile = Literal["unicode_times", "original_t5"]
DEFAULT_FONT_PROFILE: FontProfile = "unicode_times"


def apply_font_profile(source: bytes, profile: FontProfile = DEFAULT_FONT_PROFILE) -> bytes:
    if profile == "original_t5":
        return source
    if profile != "unicode_times":
        raise ValueError("Unknown font profile")
    old = b"\\usepackage[utf8]{inputenc}\n\\usepackage[T5]{fontenc}"
    new = (
        b"\\usepackage{fontspec}\n"
        b"\\IfFontExistsTF{Times New Roman}{\\setmainfont{Times New Roman}}"
        b"{\\IfFontExistsTF{TeX Gyre Termes}{\\setmainfont{TeX Gyre Termes}}"
        b"{\\IfFontExistsTF{Liberation Serif}{\\setmainfont{Liberation Serif}}"
        b"{\\setmainfont{DejaVu Serif}}}}"
    )
    if old not in source:
        old, new = old.replace(b"\n", b"\r\n"), new.replace(b"\n", b"\r\n")
    if source.count(old) != 1:
        raise ValueError("Expected original T5 font declarations exactly once")
    return source.replace(old, new, 1)

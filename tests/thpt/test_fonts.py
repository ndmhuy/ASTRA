from hashlib import sha256

import pytest

from exam_baseline.thpt.fonts import apply_font_profile
from exam_baseline.thpt.template import TEMPLATE_SHA256, original


@pytest.mark.parametrize("newline", [b"\n", b"\r\n"])
def test_unicode_profile_changes_only_font_lines(newline):
    source = original().replace(b"\r\n", b"\n").replace(b"\n", newline)
    generated = apply_font_profile(source)
    old = b"\\usepackage[utf8]{inputenc}" + newline + b"\\usepackage[T5]{fontenc}"
    new = (
        b"\\usepackage{fontspec}"
        + newline
        + b"\\IfFontExistsTF{Times New Roman}{\\setmainfont{Times New Roman}}"
        b"{\\IfFontExistsTF{TeX Gyre Termes}{\\setmainfont{TeX Gyre Termes}}"
        b"{\\IfFontExistsTF{Liberation Serif}{\\setmainfont{Liberation Serif}}"
        b"{\\setmainfont{DejaVu Serif}}}}"
    )
    assert generated.replace(new, old, 1) == source
    assert sha256(original()).hexdigest() == TEMPLATE_SHA256


def test_original_profile_and_unknown_profile():
    assert apply_font_profile(original(), "original_t5") == original()
    with pytest.raises(ValueError, match="Unknown"):
        apply_font_profile(original(), "unknown")

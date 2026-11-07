import unicodedata

import pytest
from pydantic import ValidationError

from exam_baseline.thpt.content import choice_latex, content_latex
from exam_baseline.thpt.models import Statement


@pytest.mark.parametrize(
    "expression",
    [
        r"x^2+\cos x+C",
        r"(1;+\infty)",
        r"2\sqrt{3}",
        "I(1;-2;3), R=4",
        "2a^3/3",
        "1/2",
    ],
)
def test_bare_mathematical_choices_use_math_mode(expression):
    rendered = choice_latex(expression)
    assert rendered == "$" + expression + "$"
    assert r"\textbackslash" not in rendered
    assert r"\textasciicircum" not in rendered


def test_explicit_math_and_vietnamese_prose_are_preserved():
    assert choice_latex(r"$x^2+\cos x+C$") == r"$x^2+\cos x+C$"
    assert choice_latex("Hàm số đồng biến.") == "Hàm số đồng biến."
    assert choice_latex(r"Bán kính $R=2\sqrt{3}$.") == r"Bán kính $R=2\sqrt{3}$."


def test_bare_numeric_sets_keep_their_visible_braces():
    assert choice_latex("{7}") == r"$\{7\}$"


@pytest.mark.parametrize("value", [r"Bán kính R=2\sqrt{3}", r"\input{key}", r"x^{2"])
def test_ambiguous_or_unsafe_math_is_rejected(value):
    with pytest.raises(ValueError):
        choice_latex(value)


@pytest.mark.parametrize(
    "value",
    [
        r"Dây chuyền $A(60\%, 3\% lỗi)$.",
        r"\(5\% lỗi\)",
        r"\[5\% lỗi\]",
        r"$$5\% lỗi$$",
        unicodedata.normalize("NFD", r"$3\% lỗi$"),
    ],
)
def test_vietnamese_words_in_math_are_rejected(value):
    with pytest.raises(ValueError, match="Vietnamese prose"):
        content_latex(value)


@pytest.mark.parametrize(
    "value",
    [
        r"Dây chuyền $A$ (60\%, 3\% lỗi).",
        r"$A(60\%, 3\%\text{ lỗi})$",
        r"$\text{Tỉ lệ \textbf{lỗi} là }3\%$",
        r"$\alpha=3\%$",
    ],
)
def test_vietnamese_text_outside_math_or_in_text_groups_is_preserved(value):
    content_latex(value)


def test_invalid_math_prose_fails_agent_schema_validation():
    with pytest.raises(ValidationError):
        Statement(text=r"$3\% lỗi$", answer=True, solution="Dữ liệu cho trước.")

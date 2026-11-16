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


@pytest.mark.parametrize(
    "value",
    [
        r"Emitted at 90^\circ above nadir.",
        "r = (Nn/N0)^(1/n) - 1",
        "p^2 AA + 2pq Aa + q^2 aa = 1",
        "delta P = R P^2 / (U^2 cos^2 phi)",
        "pH = pKa + log([A-]/[HA])",
        r"The value is \cos x.",
        "Use N_0 as the initial population.",
        "r=(Nn/N0)-1",
        "$\x0crac{1}{2}$",
        "$\text{label}$".replace("\\t", "\t"),
    ],
)
def test_unwrapped_or_corrupted_formulas_do_not_silently_render_as_text(value):
    with pytest.raises(ValueError):
        content_latex(value)


@pytest.mark.parametrize(
    "value",
    [
        r"Emitted at $90^{\circ}$ above nadir.",
        r"$r=\left(\frac{N_n}{N_0}\right)^{1/n}-1$",
        r"$p^2+2pq+q^2=1$",
        r"$\Delta P=\frac{RP^2}{U^2\cos^2\varphi}$",
        r"$H=\frac{P-\Delta P}{P}$",
    ],
)
def test_complete_formulas_keep_their_latex(value):
    assert content_latex(value) == value


def test_fill_in_blanks_and_literal_underscores_are_not_math_errors():
    blank = r"\underline{\hspace{2cm}}"
    assert content_latex(r"Điền " + blank + ".") == r"Điền " + blank + "."
    assert content_latex("Choose ____ now.") == "Choose " + blank + " now."
    assert content_latex("Fixture g73_74") == r"Fixture g73\_74"
    assert content_latex(r"Tỉ lệ 3\%, điền ____.") == r"Tỉ lệ 3\%, điền " + blank + "."

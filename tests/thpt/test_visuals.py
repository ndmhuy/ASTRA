import pytest
from pydantic import ValidationError

from exam_baseline.thpt.models import Question
from exam_baseline.thpt.visuals import visual_issues
from tests.thpt.test_generation import question, request


@pytest.mark.parametrize(
    "stem",
    [
        "Cho hàm số có đồ thị như hình vẽ. Tìm khoảng đồng biến.",
        "Cho hàm số có bảng biến thiên như sau.",
        "Dựa vào bảng số liệu sau, tính trung bình.",
    ],
)
def test_referenced_visual_requires_illustrator(stem):
    raw = question(request().slots[0]).model_dump()
    raw["stem"] = stem
    with pytest.raises(ValidationError, match="missing_illustration_request"):
        Question.model_validate(raw)
    raw["illustration_request"] = "Draw the table from explicitly supplied mathematical data"
    assert Question.model_validate(raw).illustration_request


def test_pipe_table_rejected_even_when_drawing_is_requested():
    assert (
        "pseudo_table"
        in visual_issues("$x$ | $-1$ | $0$ | $1$\n$y$ | $2$ | $3$ | $4$", "Draw a table")[0]
    )


@pytest.mark.parametrize(
    "stem",
    [
        r"Tính $|x|+|y|+|z|$.",
        "Cho hình chóp có đáy là hình vuông.",
        "Cho hàm số có đồ thị là một parabol.",
        "Mẫu có nhóm $[0;10)$ tần số 3.",
    ],
)
def test_text_only_math_does_not_require_a_drawing(stem):
    assert not visual_issues(stem, None)

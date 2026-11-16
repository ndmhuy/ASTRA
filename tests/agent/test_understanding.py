import pytest

from exam_baseline.agent.understanding import normalize_vietnamese, understand


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Tạo đề Toán lớp 12", {"subject": "mathematics", "grade": 12}),
        ("tao de toan lop 11", {"subject": "mathematics", "grade": 11}),
        ("20 câu, 45 phút, phần đạo hàm", {"question_count": 20, "duration_minutes": 45}),
        ("Physics khối 10", {"subject": "physics", "grade": 10}),
    ],
)
def test_extract_slots(text, expected):
    result = understand(text)
    for key, value in expected.items():
        assert result.slots[key] == value


def test_preserves_original_while_normalizing():
    result = understand("Đổi ĐỀ Toán")
    assert result.original_text == "Đổi ĐỀ Toán"
    assert result.normalized_text == "doi de toan"
    assert normalize_vietnamese("tích phân") == "tich phan"


def test_remark_is_not_edit():
    result = understand("Câu 3 khó quá")
    assert result.intents == ["difficulty_remark"]
    assert result.display_question_index == 3


def test_explicit_question_edit():
    result = understand("Sửa câu 3 dễ hơn")
    assert "explicit_edit" in result.intents


def test_correction_and_negation():
    result = understand("À thôi đổi còn 15 câu, không lấy phần tích phân")
    assert result.slots["question_count"] == 15
    assert "tích phân" in result.removed_topics
    assert "explicit_edit" in result.intents


def test_multi_intent():
    result = understand("Tạo đề Toán 12 và ASTRA xuất Word được không?")
    assert {"generate_exam", "app_help"} <= set(result.intents)


def test_unknown_is_safe():
    assert understand("xyzzy").intents == ["unknown"]

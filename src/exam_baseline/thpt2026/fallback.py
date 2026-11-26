"""Realistic offline/fallback exam builders for the 6 THPT 2026 contract formats."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Callable
from pathlib import Path

from exam_baseline.thpt2026.contract import validate_contract_exam
from exam_baseline.thpt2026.rendering import render_contract_exam_tex


def _mcq(
    qid: str,
    stem: str,
    choices: dict[str, str],
    answer: str,
    solution: str,
    *,
    passage_id: str | None = None,
) -> dict:
    item = {
        "id": qid,
        "type": "mcq",
        "stem": stem,
        "choices": choices,
        "answer": answer,
        "solution": solution,
    }
    if passage_id:
        item["passage_id"] = passage_id
    return item


def _tf(
    qid: str,
    stem: str,
    statements: list[tuple[str, bool, str]],
    *,
    solution: str = "",
) -> dict:
    return {
        "id": qid,
        "type": "true_false",
        "stem": stem,
        "statements": [
            {"text": text, "answer": ans, "solution": sol} for text, ans, sol in statements
        ],
        "solution": solution,
    }


def _short(qid: str, stem: str, answer: str, solution: str) -> dict:
    return {
        "id": qid,
        "type": "short_answer",
        "stem": stem,
        "answer": answer,
        "solution": solution,
    }


def _written(
    qid: str,
    task: str,
    stem: str,
    solution: str,
    *,
    points: float,
    word_count_target: int | None = None,
    passage_id: str | None = None,
) -> dict:
    item: dict = {
        "id": qid,
        "type": "written",
        "task": task,
        "stem": stem,
        "solution": solution,
        "points": points,
    }
    if word_count_target is not None:
        item["word_count_target"] = word_count_target
    if passage_id:
        item["passage_id"] = passage_id
    return item


def _build_literature() -> tuple[list[dict], list[dict], list[str]]:
    passages = [
        {
            "id": "reading_1",
            "section": "P1",
            "kind": "reading",
            "questionRange": [1, 5],
            "instruction": "Đọc văn bản sau và thực hiện các yêu cầu từ câu 1 đến câu 5:",
            "heading": "ÁNH ĐÈN TRONG XƯỞNG ĐÊM",
            "text": (
                "Cửa xưởng sửa đồng hồ của ông Tư nằm lùi vào một khoảng sân nhỏ cuối hẻm. "
                "Mỗi tối, khi hàng quán hai bên đường đã kéo cửa sắt, ngọn đèn bàn vàng ấm "
                "trong ô kính hẹp vẫn thức cùng tiếng tích tắc đều đặn. Ông hay nói với đứa "
                "cháu ngoại: mỗi bánh răng mòn đều mang theo thói quen chờ đợi của một người "
                "chủ nào đó, sửa kỹ một chút là giữ lại cho họ thêm một quãng yên tâm.\n\n"
                "Những đêm mưa đầu mùa, nước tạt qua mái hiên cũ, thằng bé ngồi gấp lại mấy "
                "tờ lịch bàn đã úa màu nghe ông kể chuyện phố xá thời chưa có đèn cao áp. "
                "Trong ánh sáng chật hẹp nhưng bền bỉ ấy, thời gian dường như không trôi tuột "
                "đi vội vã mà lắng lại qua từng cử động chậm rãi của đôi bàn tay gầy."
            ),
            "source": "Truyện ngắn viết riêng cho bộ đề ôn luyện THPT 2026",
        }
    ]
    questions = [
        _written(
            "P1-1",
            "reading_response",
            "Xác định ngôi kể được sử dụng trong đoạn trích trên.",
            "Hướng dẫn chấm (0,5 điểm): Nêu đúng ngôi kể thứ ba (người kể chuyện giấu mình).",
            points=0.5,
            passage_id="reading_1",
        ),
        _written(
            "P1-2",
            "reading_response",
            "Chỉ ra hai chi tiết miêu tả không gian xưởng sửa đồng hồ vào buổi tối.",
            "Hướng dẫn chấm (0,5 điểm): Nêu được 2 chi tiết hợp lệ như cửa xưởng lùi vào khoảng "
            "sân nhỏ cuối hẻm, ngọn đèn bàn vàng ấm trong ô kính hẹp, tiếng tích tắc đều đặn.",
            points=0.5,
            passage_id="reading_1",
        ),
        _written(
            "P1-3",
            "reading_response",
            "Phân tích tác dụng của biện pháp tu từ nhân hóa trong câu: 'ngọn đèn bàn vàng ấm "
            "trong ô kính hẹp vẫn thức cùng tiếng tích tắc đều đặn'.",
            "Hướng dẫn chấm (1,0 điểm): Chỉ ra từ ngữ nhân hóa ('vẫn thức'); làm rõ tác dụng gợi "
            "sự bền bỉ, ấm áp và gắn bó lặng lẽ giữa người thợ với công việc.",
            points=1.0,
            passage_id="reading_1",
        ),
        _written(
            "P1-4",
            "reading_response",
            "Nhận xét về thái độ làm nghề của nhân vật ông Tư qua lời nói với cháu ngoại.",
            "Hướng dẫn chấm (1,0 điểm): Ông Tư trân trọng nghề nghiệp, tận tâm, cẩn trọng và xem "
            "sự hài lòng, yên tâm của khách hàng là giá trị cốt lõi.",
            points=1.0,
            passage_id="reading_1",
        ),
        _written(
            "P1-5",
            "reading_response",
            "Từ câu chuyện trong văn bản, anh/chị hãy rút ra một thông điệp ý nghĩa về thái độ "
            "sống chậm và trân trọng giá trị lao động thường nhật (trình bày 5–7 dòng).",
            "Hướng dẫn chấm (1,0 điểm): Trình bày thông điệp rõ ràng, lập luận thuyết phục và "
            "liên hệ phù hợp thực tiễn cuộc sống hiện đại.",
            points=1.0,
            passage_id="reading_1",
        ),
        _written(
            "P2-1",
            "paragraph",
            "Viết đoạn văn nghị luận (khoảng 200 chữ) phân tích vẻ đẹp của ánh sáng và nhịp thời "
            "gian trong đoạn trích 'Ánh đèn trong xưởng đêm'.",
            "Hướng dẫn chấm (2,0 điểm): Đúng hình thức đoạn văn ~200 chữ (0,25 điểm); xác định "
            "đúng vấn đề (0,25 điểm); phân tích ánh đèn ấm và nhịp tích tắc gắn với tình người, "
            "sự bền bỉ (1,0 điểm); diễn đạt chuẩn xác, sáng tạo (0,5 điểm).",
            points=2.0,
            word_count_target=200,
            passage_id="reading_1",
        ),
        _written(
            "P2-2",
            "essay",
            "Trong kỷ nguyên công nghệ số nhiều biến động, người trẻ cần giữ gìn bản sắc cá nhân "
            "song song với năng lực thích ứng linh hoạt. Hãy viết bài văn nghị luận (khoảng 600 "
            "chữ) trình bày suy nghĩ của anh/chị về vấn đề trên.",
            "Hướng dẫn chấm (4,0 điểm): Mở-Thân-Kết rõ ràng (0,5 điểm); giải thích khái niệm bản "
            "sắc cá nhân và thích ứng linh hoạt (0,5 điểm); phân tích vai trò, mối quan hệ bổ trợ "
            "và nêu dẫn chứng thực tế (2,0 điểm); phản đề và bài học nhận thức (0,5 điểm); chuẩn "
            "chính tả, diễn đạt sâu sắc (0,5 điểm).",
            points=4.0,
            word_count_target=600,
        ),
    ]
    return questions, passages, []


def _build_english() -> tuple[list[dict], list[dict], list[str]]:
    passages = [
        {
            "id": "cloze_1",
            "section": "P1",
            "kind": "cloze",
            "questionRange": [6, 10],
            "instruction": (
                "Read the following leaflet and mark the letter A, B, C, or D on your answer "
                "sheet to indicate the option that best fits each of the numbered blanks "
                "from 6 to 10."
            ),
            "heading": "COMMUNITY GREEN CYCLING WEEKEND",
            "text": (
                "Are you looking for an eco-friendly way to stay active this Sunday? Join our "
                "monthly cycling event at City Riverside Park, which (6) _____ local residents to "
                "leave their motorbikes at home.\n\n"
                "Participants will follow a 10-kilometer route (7) _____ shaded tree-lined paths. "
                "Free helmet checks and water refill stations are (8) _____ at three rest points. "
                "(9) _____ the early morning heat, please wear breathable clothing and bring a "
                "reusable bottle. Anyone wishing to volunteer should sign up (10) _____ "
                "Friday noon."
            ),
        },
        {
            "id": "reading_1",
            "section": "P1",
            "kind": "reading",
            "questionRange": [11, 20],
            "instruction": (
                "Read the following passage and mark the letter A, B, C, or D on your answer "
                "sheet to indicate the best answer to each of the following questions from "
                "11 to 20."
            ),
            "heading": "URBAN COOLING CORRIDORS",
            "text": (
                "[I] As concrete districts expand, daytime surface temperatures in city "
                "centers often "
                "exceed those of nearby rural fields by several degrees. [II] Urban "
                "planners call this "
                "gap the heat-island effect, which raises summer electricity demand and "
                "affects public "
                "health. [III] To counter heat islands without halting housing growth, "
                "several cities "
                "have turned narrow roadside strips into shaded green corridors. [IV]\n\n"
                "Unlike isolated pocket parks, connected corridors allow cool evening breezes to "
                "travel into dense neighborhoods. Selecting drought-tolerant native trees lowers "
                "irrigation costs and maintains reliable canopy cover during dry months. "
                "Researchers "
                "note that permeable pavements laid beneath the trees also absorb sudden storm "
                "runoff, turning seasonal flood zones into walkable community streets."
            ),
        },
        {
            "id": "reading_2",
            "section": "P1",
            "kind": "reading",
            "questionRange": [21, 28],
            "instruction": (
                "Read the following passage and mark the letter A, B, C, or D on your answer "
                "sheet to indicate the best answer to each of the following questions from "
                "21 to 28."
            ),
            "heading": "OPEN ARCHIVES FOR LOCAL HISTORY",
            "text": (
                "Over the past decade, municipal libraries across Asia have partnered with high "
                "schools to digitize fragile newspapers, hand-drawn maps, and oral interviews. "
                "Students trained in basic metadata tagging verify dates and street names before "
                "files go online. Once hidden inside basement boxes, thousands of everyday stories "
                "can now be searched in seconds by families and historians.\n\n"
                "Beyond preservation, open archives shift how young learners view "
                "historical study. "
                "Instead of memorizing fixed timelines, classes compare conflicting "
                "letters from the "
                "same week and notice how neighborhood priorities evolved. Archivists "
                "emphasize that "
                "careful source attribution remains essential so digital convenience never "
                "encourages "
                "careless citation."
            ),
        },
        {
            "id": "cloze_2",
            "section": "P1",
            "kind": "cloze",
            "questionRange": [29, 34],
            "instruction": (
                "Read the following passage and mark the letter A, B, C, or D on your answer "
                "sheet to indicate the option that best fits each of the numbered blanks "
                "from 29 to 34."
            ),
            "heading": "LEARNING WITH SHARED NOTES",
            "text": (
                "Preparing for final exams often feels overwhelming when students review thick "
                "textbooks alone. Setting up a small peer study group (29) _____ learners to split "
                "complex chapters into clear visual summaries. Each member checks one topic and "
                "explains key concepts in plain terms, (30) _____ makes gaps in understanding easy "
                "to spot early. (31) _____ sessions follow a fixed forty-minute timer, "
                "groups rarely "
                "drift off task. Short breaks between rounds keep concentration steady and "
                "(32) _____ "
                "unnecessary fatigue. By the end of the term, students gain not only "
                "stronger recall "
                "(33) _____ practical habits of listening carefully to differing "
                "viewpoints (34) _____ "
                "solve tough problems together."
            ),
        },
        {
            "id": "cloze_3",
            "section": "P1",
            "kind": "cloze",
            "questionRange": [35, 40],
            "instruction": (
                "Read the following announcement and mark the letter A, B, C, or D on your answer "
                "sheet to indicate the option that best fits each of the numbered blanks "
                "from 35 to 40."
            ),
            "heading": "SCHOOL SCIENCE FAIR REGISTRATION",
            "text": (
                "Our annual Science & Sustainability Fair will open on Saturday morning in "
                "the Main "
                "Hall. Teams of two or three students are invited to submit a short "
                "proposal (35) _____ "
                "a testable environmental question. Entries judged most practical will "
                "receive basic "
                "lab sensors on loan from the physics department, (36) _____ allow "
                "accurate tracking "
                "of humidity and light levels. Past winners stressed that keeping a tidy logbook "
                "(37) _____ a decisive difference during final interviews. Please ensure "
                "every graph "
                "carries clear units before uploading your poster draft, as incomplete labels may "
                "delay (38) _____ approval. Finalists will present three-minute live "
                "demonstrations "
                "(39) _____ visiting teachers and younger classes eager to learn (40) _____ real "
                "experiments work outside textbooks."
            ),
        },
    ]

    ordering_items = [
        (
            "P1-1",
            "Mark the letter A, B, C, or D to indicate the best arrangement of utterances to make "
            "a meaningful exchange:\n"
            "a. Lan: Sounds great! Let's meet at the school gate at 7 a.m.\n"
            "b. Minh: Are you joining the book donation drive this Saturday?\n"
            "c. Minh: Deal. I'll bring extra cardboard boxes for packing.",
            {"A": "b - a - c", "B": "a - b - c", "C": "b - c - a", "D": "c - a - b"},
            "A",
            (
                "Trình tự hội thoại tự nhiên: câu hỏi rủ tham gia (b) -> đồng ý và hẹn giờ (a) "
                "-> chốt chuẩn bị (c)."
            ),
        ),
        (
            "P1-2",
            "Mark the letter A, B, C, or D to indicate the best arrangement of utterances:\n"
            "a. Tutor: Try breaking each long paragraph into one main claim and one example.\n"
            "b. Student: I keep running out of time on reading passages.\n"
            "c. Tutor: Do you underline topic sentences first?\n"
            "d. Student: Not consistently, so I often re-read twice.",
            {
                "A": "b - c - d - a",
                "B": "c - b - d - a",
                "C": "b - d - c - a",
                "D": "a - b - c - d",
            },
            "A",
            (
                "Học sinh nêu khó khăn (b) -> gia sư hỏi thói quen (c) -> học sinh trả lời (d) "
                "-> gia sư gợi ý cách sửa (a)."
            ),
        ),
        (
            "P1-3",
            "Mark the letter A, B, C, or D to indicate the best arrangement of a short letter:\n"
            "Hi Alex,\n"
            "a. Thank you so much for lending me your chemistry revision notebook last week.\n"
            "b. Could we grab coffee after Friday's lab so I can return it in person?\n"
            "c. The summary charts in chapter three helped me solve almost every "
            "equilibrium problem.\n"
            "Best, Hoa",
            {"A": "a - c - b", "B": "c - a - b", "C": "b - a - c", "D": "a - b - c"},
            "A",
            "Thư mở đầu bằng lời cảm ơn (a), nêu hiệu quả cụ thể (c), rồi hẹn gặp trả vở (b).",
        ),
        (
            "P1-4",
            "Mark the letter A, B, C, or D to indicate the best arrangement of sentences "
            "into a paragraph:\n"
            "a. First, setting a consistent sleep schedule helps the brain consolidate "
            "daily lessons.\n"
            "b. Maintaining strong study performance requires balanced daily habits rather "
            "than late-night cramming.\n"
            "c. Finally, brief outdoor walks refresh attention between afternoon subjects.\n"
            "d. In addition, drinking enough water prevents afternoon headaches during "
            "long classes.",
            {
                "A": "b - a - d - c",
                "B": "a - b - d - c",
                "C": "b - d - a - c",
                "D": "d - a - b - c",
            },
            "A",
            "Câu chủ đề (b) mở đoạn, tiếp theo lần lượt First (a), In addition (d), Finally (c).",
        ),
        (
            "P1-5",
            "Mark the letter A, B, C, or D to indicate the best arrangement of sentences:\n"
            "a. Consequently, commuters save money while lowering rush-hour emissions.\n"
            "b. Several towns now offer free bicycle transfers near major metro stations.\n"
            "c. This simple link solves the difficult last kilometer between trains and offices.\n"
            "d. Over the next year, planners intend to add covered bike racks at every stop.",
            {
                "A": "b - c - a - d",
                "B": "c - b - a - d",
                "C": "b - a - d - c",
                "D": "a - b - c - d",
            },
            "A",
            (
                "Giới thiệu giải pháp (b) -> nêu tác dụng kết nối chặng cuối (c) -> hệ quả (a) "
                "-> kế hoạch tiếp theo (d)."
            ),
        ),
    ]
    questions = [_mcq(qid, stem, ch, ans, sol) for qid, stem, ch, ans, sol in ordering_items]

    cloze1_data = [
        (
            "P1-6",
            {"A": "encourages", "B": "refuses", "C": "ignores", "D": "prevents"},
            "A",
            "encourage someone to do something = khuyến khích.",
        ),
        (
            "P1-7",
            {"A": "along", "B": "between", "C": "since", "D": "during"},
            "A",
            "follow a route along paths = chạy dọc theo lối đi.",
        ),
        (
            "P1-8",
            {"A": "available", "B": "expensive", "C": "crowded", "D": "fragile"},
            "A",
            "available at rest points = luôn sẵn có tại các điểm nghỉ.",
        ),
        (
            "P1-9",
            {"A": "Because of", "B": "Although", "C": "Unless", "D": "Whereas"},
            "A",
            "Because of + cụm danh từ ('the early morning heat').",
        ),
        (
            "P1-10",
            {"A": "before", "B": "among", "C": "into", "D": "onto"},
            "A",
            "sign up before Friday noon = đăng ký trước trưa thứ Sáu.",
        ),
    ]
    for qid, ch, ans, sol in cloze1_data:
        questions.append(_mcq(qid, "", ch, ans, sol, passage_id="cloze_1"))

    reading1_data = [
        (
            "P1-11",
            "Which of the following best summarizes the main topic of the passage?",
            {
                "A": "How green roadside corridors reduce urban heat and storm runoff",
                "B": "Why rural farming produces higher electricity bills in summer",
                "C": "Methods for replacing all city roads with concrete highways",
                "D": "Ways to measure indoor air quality inside apartment buildings",
            },
            "A",
            "Toàn bài nói về dải cây xanh ven đường làm mát đô thị và thấm nước mưa.",
        ),
        (
            "P1-12",
            "According to paragraph 1, what drives the heat-island effect in cities?",
            {
                "A": "Expanding concrete surfaces trapping daytime heat",
                "B": "Excessive evening breezes from nearby fields",
                "C": "Lack of summer electricity demand in rural zones",
                "D": "Low density of apartment buildings in city centers",
            },
            "A",
            "Đoạn 1 nêu khu vực bê tông mở rộng làm nhiệt độ bề mặt cao hơn vùng nông thôn.",
        ),
        (
            "P1-13",
            (
                "Where in paragraph 1 does the following sentence best fit? 'That extra "
                "cooling demand often strains local power grids during peak afternoons.'"
            ),
            {"A": "[III]", "B": "[I]", "C": "[II]", "D": "[IV]"},
            "A",
            "Đặt tại [III] nối trực tiếp ý 'raises summer electricity demand' ngay câu trước.",
        ),
        (
            "P1-14",
            "The word 'gap' in paragraph 1 refers to:",
            {
                "A": "the temperature difference between city centers and rural areas",
                "B": "a physical crack in permeable sidewalk tiles",
                "C": "the distance between two public housing blocks",
                "D": "a shortage of electricity meters during winter",
            },
            "A",
            (
                "'this gap' nhắc lại sự chênh lệch nhiệt độ giữa trung tâm thành phố và vùng "
                "nông thôn."
            ),
        ),
        (
            "P1-15",
            "Why do planners prefer connected corridors over isolated pocket parks?",
            {
                "A": "Connected corridors channel cool evening breezes into dense blocks.",
                "B": "Pocket parks require imported pavement stones from abroad.",
                "C": "Connected corridors eliminate the need for any municipal budget.",
                "D": "Pocket parks increase surface temperatures above concrete levels.",
            },
            "A",
            (
                "Đoạn 2 chỉ rõ hành lang liên kết giúp gió mát ban tối lưu thông vào khu dân "
                "cư đông đúc."
            ),
        ),
        (
            "P1-16",
            "The phrase 'drought-tolerant' in paragraph 2 is closest in meaning to:",
            {
                "A": "able to survive with limited water",
                "B": "requiring daily greenhouse heating",
                "C": "unable to grow near street curbs",
                "D": "producing bright flowers only in winter",
            },
            "A",
            "drought-tolerant = chịu hạn tốt, sống được với ít nước.",
        ),
        (
            "P1-17",
            "What benefit do permeable pavements provide according to paragraph 2?",
            {
                "A": "They absorb sudden rainwater runoff beneath roadside trees.",
                "B": "They block rainwater from reaching underground soil layers.",
                "C": "They reflect sunlight straight into upper apartment windows.",
                "D": "They triple the irrigation needed for native tree roots.",
            },
            "A",
            "Câu cuối nêu mặt lát thấm nước hấp thụ nước mưa bất chợt, giảm ngập cục bộ.",
        ),
        (
            "P1-18",
            "Which statement is NOT supported by the passage?",
            {
                "A": "Cities must halt all housing construction to cool streets.",
                "B": "Native trees help reduce watering costs in dry periods.",
                "C": "High urban heat raises summer demand for electricity.",
                "D": "Green corridors can improve neighborhood walkability.",
            },
            "A",
            "Bài nói rõ tìm cách hạ nhiệt 'without halting housing growth', trái với đáp án A.",
        ),
        (
            "P1-19",
            (
                "It can be inferred from paragraph 2 that native tree species are chosen "
                "mainly because they:"
            ),
            {
                "A": "offer dependable shade with lower maintenance needs",
                "B": "grow only inside enclosed botanical museums",
                "C": "prevent pedestrians from crossing residential streets",
                "D": "require deeper concrete basins than non-native plants",
            },
            "A",
            "Cây bản địa chịu hạn giảm chi phí tưới và giữ tán che ổn định.",
        ),
        (
            "P1-20",
            "The overall tone of the passage is:",
            {
                "A": "informative and practical",
                "B": "sarcastic and skeptical",
                "C": "alarmist and pessimistic",
                "D": "playful and fictional",
            },
            "A",
            "Giọng văn khách quan, cung cấp thông tin và giải pháp quy hoạch thực tế.",
        ),
    ]
    for qid, stem, ch, ans, sol in reading1_data:
        questions.append(_mcq(qid, stem, ch, ans, sol, passage_id="reading_1"))

    reading2_data = [
        (
            "P1-21",
            "What is the main purpose of the digitization partnerships described in paragraph 1?",
            {
                "A": "To preserve fragile local records and make them searchable online",
                "B": "To replace school history textbooks with printed magazines",
                "C": "To sell antique maps to private international collectors",
                "D": "To limit access to municipal libraries after school hours",
            },
            "A",
            "Đoạn 1 nhấn mạnh số hóa tư liệu dễ hỏng và giúp mọi người tìm kiếm trực tuyến.",
        ),
        (
            "P1-22",
            "What role do high school students play in these library projects?",
            {
                "A": "They check dates and street names while tagging basic metadata.",
                "B": "They transport basement boxes to landfill recycling sites.",
                "C": "They write fictional stories about medieval European castles.",
                "D": "They operate heavy printing presses for city newspapers.",
            },
            "A",
            "Học sinh được hướng dẫn gắn thẻ siêu dữ liệu và đối chiếu ngày tháng, tên đường.",
        ),
        (
            "P1-23",
            "The word 'fragile' in paragraph 1 is closest in meaning to:",
            {"A": "delicate", "B": "waterproof", "C": "ordinary", "D": "boundless"},
            "A",
            "fragile = dễ rách/hỏng, đồng nghĩa với delicate.",
        ),
        (
            "P1-24",
            "Before digitization, where were many local historical documents kept?",
            {
                "A": "Inside storage boxes in library basements",
                "B": "On public display boards at bus stations",
                "C": "Inside commercial shopping mall kiosks",
                "D": "On digital cloud servers run by airlines",
            },
            "A",
            "Văn bản nêu 'Once hidden inside basement boxes'.",
        ),
        (
            "P1-25",
            "How do open archives change students' approach to studying history?",
            {
                "A": "Students compare firsthand letters instead of merely memorizing dates.",
                "B": "Students stop checking historical sources altogether.",
                "C": "Students focus exclusively on memorizing fixed timelines.",
                "D": "Students avoid reading newspapers from past decades.",
            },
            "A",
            "Đoạn 2 chỉ rõ thay vì học vẹt mốc thời gian, học sinh đối chiếu thư từ cùng thời kỳ.",
        ),
        (
            "P1-26",
            "The word 'evolved' in paragraph 2 can best be replaced by:",
            {
                "A": "gradually changed",
                "B": "remained identical",
                "C": "vanished instantly",
                "D": "became illegal",
            },
            "A",
            "evolved = chuyển biến dần theo thời gian.",
        ),
        (
            "P1-27",
            "Why do archivists stress source attribution for digital collections?",
            {
                "A": "To prevent easy online access from leading to sloppy citations",
                "B": "To hide the names of towns where newspapers were printed",
                "C": "To discourage historians from reading community interviews",
                "D": "To ensure scanned files expire after one week online",
            },
            "A",
            "Câu cuối nêu rõ để sự tiện lợi số không dẫn tới trích dẫn cẩu thả.",
        ),
        (
            "P1-28",
            "Which title best suits the entire passage?",
            {
                "A": "Bringing Community Archives Online Through Schools",
                "B": "Replacing Libraries With Social Media Feeds",
                "C": "How to Repair Basement Flooding in Summer",
                "D": "Memorizing World Timelines Without Primary Sources",
            },
            "A",
            (
                "Bao quát toàn bộ nội dung hợp tác trường học - thư viện đưa lưu trữ địa "
                "phương lên mạng."
            ),
        ),
    ]
    for qid, stem, ch, ans, sol in reading2_data:
        questions.append(_mcq(qid, stem, ch, ans, sol, passage_id="reading_2"))

    cloze2_data = [
        (
            "P1-29",
            {"A": "enables", "B": "denies", "C": "forbids", "D": "delays"},
            "A",
            "enable someone to do something = giúp có thể làm gì.",
        ),
        (
            "P1-30",
            {"A": "which", "B": "who", "C": "whose", "D": "whom"},
            "A",
            "Mệnh đề quan hệ không xác định thay cho cả mệnh đề trước -> dùng which.",
        ),
        (
            "P1-31",
            {"A": "When", "B": "Despite", "C": "Unless", "D": "Without"},
            "A",
            "When sessions follow... = Khi buổi học tuân theo đồng hồ hẹn giờ.",
        ),
        (
            "P1-32",
            {"A": "reduce", "B": "invite", "C": "expand", "D": "deepen"},
            "A",
            "Song song với 'keep': reduce unnecessary fatigue = giảm mệt mỏi.",
        ),
        (
            "P1-33",
            {"A": "but also", "B": "neither", "C": "or else", "D": "so that"},
            "A",
            "Cấu trúc not only ... but also ...",
        ),
        (
            "P1-34",
            {"A": "and", "B": "yet", "C": "nor", "D": "than"},
            "A",
            "Kết hợp đồng đẳng hai hành động hợp tác: listening ... and solve.",
        ),
    ]
    for qid, ch, ans, sol in cloze2_data:
        questions.append(_mcq(qid, "", ch, ans, sol, passage_id="cloze_2"))

    cloze3_data = [
        (
            "P1-35",
            {"A": "exploring", "B": "explored", "C": "to exploring", "D": "explore"},
            "A",
            "Rút gọn mệnh đề quan hệ chủ động: proposal exploring ...",
        ),
        (
            "P1-36",
            {"A": "which", "B": "that", "C": "who", "D": "what"},
            "A",
            "Sau dấu phẩy thay cho 'basic lab sensors' -> dùng which.",
        ),
        (
            "P1-37",
            {"A": "made", "B": "took", "C": "went", "D": "gave"},
            "A",
            "Cụm cố định make a difference.",
        ),
        (
            "P1-38",
            {"A": "poster", "B": "noise", "C": "traffic", "D": "weather"},
            "A",
            "Ngữ cảnh duyệt bản thảo áp phích dự thi (poster approval).",
        ),
        (
            "P1-39",
            {"A": "for", "B": "at", "C": "against", "D": "since"},
            "A",
            "present demonstrations for teachers = trình diễn trước/cho thầy cô.",
        ),
        (
            "P1-40",
            {"A": "how", "B": "which", "C": "whose", "D": "whom"},
            "A",
            "learn how real experiments work = hiểu cách thí nghiệm vận hành.",
        ),
    ]
    for qid, ch, ans, sol in cloze3_data:
        questions.append(_mcq(qid, "", ch, ans, sol, passage_id="cloze_3"))

    return questions, passages, []


def _build_history() -> tuple[list[dict], list[dict], list[str]]:
    mcqs = [
        (
            "Nhân tố hàng đầu thúc đẩy sự ra đời của tổ chức ASEAN (năm 1967) là nhu cầu",
            {
                "A": "hợp tác để cùng phát triển và giữ vững ổn định khu vực.",
                "B": "thành lập một liên minh quân sự chung đối đầu với châu Âu.",
                "C": "xây dựng một đồng tiền chung thay thế toàn bộ tiền bản địa.",
                "D": "xóa bỏ hoàn toàn biên giới quốc gia giữa các nước sáng lập.",
            },
            "A",
            "Các nước Đông Nam Á cần hợp tác kinh tế, văn hóa và duy trì hòa bình ổn định.",
        ),
        (
            "Hiến chương Liên hợp quốc được thông qua tại Hội nghị Xan Phranxixcô vào năm nào?",
            {"A": "1945", "B": "1948", "C": "1954", "D": "1960"},
            "A",
            "Hiến chương Liên hợp quốc được thông qua tháng 6/1945 và có hiệu lực tháng 10/1945.",
        ),
        (
            (
                "Sự kiện nào đánh dấu cuộc Tổng tiến công và nổi dậy mùa Xuân năm 1975 kết "
                "thúc thắng lợi hoàn toàn?"
            ),
            {
                "A": "Chiến dịch Hồ Chí Minh toàn thắng (30/4/1975).",
                "B": "Chiến thắng Phước Long đầu năm 1975.",
                "C": "Chiến dịch Tây Nguyên mở màn tháng 3/1975.",
                "D": "Hội nghị Giơnevơ được ký kết năm 1954.",
            },
            "A",
            (
                "Ngày 30/4/1975 chiến dịch Hồ Chí Minh giành toàn thắng, giải phóng hoàn toàn "
                "miền Nam."
            ),
        ),
        (
            (
                "Một trong những xu thế phát triển chính của thế giới sau khi Chiến tranh lạnh "
                "chấm dứt là"
            ),
            {
                "A": "lấy phát triển kinh tế làm trọng tâm.",
                "B": "chạy đua vũ trang hạt nhân toàn cầu.",
                "C": "đối đầu gay gắt giữa hai khối quân sự.",
                "D": "thu hẹp quan hệ hợp tác đa phương.",
            },
            "A",
            "Sau Chiến tranh lạnh, các quốc gia điều chỉnh chiến lược lấy kinh tế làm trọng tâm.",
        ),
        (
            "Cộng đồng ASEAN chính thức được thành lập vào thời điểm nào?",
            {
                "A": "Ngày 31/12/2015.",
                "B": "Ngày 8/8/1967.",
                "C": "Ngày 28/7/1995.",
                "D": "Ngày 24/2/1976.",
            },
            "A",
            "Ngày 31/12/2015 Cộng đồng ASEAN chính thức đi vào hoạt động với ba trụ cột.",
        ),
        (
            (
                "Cuộc Cách mạng tháng Tám năm 1945 ở Việt Nam giành chính quyền nhanh gọn trên "
                "phạm vi cả nước trước hết nhờ"
            ),
            {
                "A": "sự lãnh đạo đúng đắn, chuẩn bị chu đáo của Đảng và Mặt trận Việt Minh.",
                "B": "viện trợ kinh tế trực tiếp từ các nước Tây Âu ngay trong tháng 8.",
                "C": "hiệp định đình chiến đã ký giữa Nhật và Mặt trận Việt Minh.",
                "D": "quân Pháp tự nguyện trao trả độc lập trước khi Nhật đầu hàng.",
            },
            "A",
            (
                "Đảng và Chủ tịch Hồ Chí Minh đã chuẩn bị kỹ lưỡng lực lượng chính trị, vũ "
                "trang và chớp thời cơ."
            ),
        ),
        (
            (
                "Chiến thắng nào của quân và dân Việt Nam năm 1954 buộc thực dân Pháp phải ký "
                "Hiệp định Giơnevơ?"
            ),
            {
                "A": "Chiến thắng Điện Biên Phủ.",
                "B": "Chiến dịch Biên giới thu - đông.",
                "C": "Chiến dịch Việt Bắc thu - đông.",
                "D": "Phong trào Đồng khởi.",
            },
            "A",
            (
                "Chiến thắng lịch sử Điện Biên Phủ (7/5/1954) tạo bước ngoặt quyết định trên "
                "bàn đàm phán Giơnevơ."
            ),
        ),
        (
            (
                "Nội dung trọng tâm của đường lối Đổi mới do Đảng Cộng sản Việt Nam đề ra từ "
                "Đại hội VI (1986) là"
            ),
            {
                "A": "đổi mới tư duy kinh tế, xóa bỏ cơ chế tập trung quan liêu bao cấp.",
                "B": "duy trì độc quyền hoàn toàn của kinh tế nhà nước trong mọi lĩnh vực.",
                "C": "hạn chế mở rộng quan hệ thương mại với các nước ngoài khu vực.",
                "D": "ngừng phát triển công nghiệp nhẹ và dịch vụ tiêu dùng.",
            },
            "A",
            "Đại hội VI mở đầu công cuộc Đổi mới với trọng tâm là đổi mới kinh tế.",
        ),
        (
            "Việt Nam chính thức gia nhập Hiệp hội các quốc gia Đông Nam Á (ASEAN) vào năm nào?",
            {"A": "1995", "B": "1991", "C": "2000", "D": "2007"},
            "A",
            "Ngày 28/7/1995 Việt Nam trở thành thành viên thứ 7 của ASEAN.",
        ),
        (
            (
                "Trong giai đoạn 1965–1968, quân dân miền Nam Việt Nam đã chiến đấu chống "
                "chiến lược chiến tranh nào của Mỹ?"
            ),
            {
                "A": "Chiến tranh cục bộ.",
                "B": "Chiến tranh đơn phương.",
                "C": "Chiến tranh đặc biệt.",
                "D": "Việt Nam hóa chiến tranh.",
            },
            "A",
            "Từ giữa 1965 đến 1968 Mỹ triển khai chiến lược Chiến tranh cục bộ.",
        ),
        (
            "Một trong ba trụ cột của Cộng đồng ASEAN là",
            {
                "A": "Cộng đồng Văn hóa - Xã hội ASEAN (ASCC).",
                "B": "Liên minh Quốc phòng Toàn cầu.",
                "C": "Ngân hàng Tiền tệ Chung châu Á.",
                "D": "Nghị viện Lập pháp Thống nhất ASEAN.",
            },
            "A",
            "Ba trụ cột gồm Chính trị - An ninh, Kinh tế và Văn hóa - Xã hội.",
        ),
        (
            (
                "Hội nghị Ianta (tháng 2/1945) diễn ra với sự tham dự của nguyên thủ ba cường "
                "quốc nào?"
            ),
            {
                "A": "Liên Xô, Mỹ, Anh.",
                "B": "Liên Xô, Pháp, Đức.",
                "C": "Mỹ, Nhật, Trung Quốc.",
                "D": "Anh, Pháp, Ý.",
            },
            "A",
            (
                "Ba cường quốc tham dự Hội nghị Ianta là Liên Xô (Xtalin), Mỹ (Rudơven) và Anh "
                "(Sớcsin)."
            ),
        ),
        (
            (
                "Phong trào 'Đồng khởi' (1959–1960) ở miền Nam Việt Nam bùng nổ mạnh mẽ nhất "
                "đầu tiên tại tỉnh nào?"
            ),
            {"A": "Bến Tre.", "B": "Quảng Trị.", "C": "Lạng Sơn.", "D": "Nghệ An."},
            "A",
            "Phong trào Đồng khởi tiêu biểu nổ ra tại huyện Mỏ Cày (Bến Tre) tháng 1/1960.",
        ),
        (
            "Quốc gia nào ở Đông Nam Á trở thành thành viên thứ 10 của ASEAN vào năm 1999?",
            {"A": "Campuchia.", "B": "Lào.", "C": "Mi-an-ma.", "D": "Bru-nây."},
            "A",
            "Tháng 4/1999 Campuchia gia nhập, hoàn thành ASEAN-10.",
        ),
        (
            (
                "Trong Chiến dịch Biên giới thu - đông 1950, trận mở màn mang tính đột phá "
                "diễn ra tại cứ điểm"
            ),
            {"A": "Đông Khê.", "B": "Thất Khê.", "C": "Phú Thọ.", "D": "Hòa Bình."},
            "A",
            "Quân ta chọn Đông Khê làm điểm đột phá mở màn chiến dịch ngày 16/9/1950.",
        ),
        (
            "Bài học xuyên suốt trong chính sách đối ngoại của Việt Nam thời kỳ Đổi mới là",
            {
                "A": (
                    "giữ vững độc lập tự chủ đồng thời đa phương hóa, đa dạng hóa quan hệ quốc tế."
                ),
                "B": "chỉ phát triển quan hệ song phương với một đối tác duy nhất.",
                "C": "đứng ngoài các diễn đàn hợp tác kinh tế đa phương.",
                "D": "giải quyết bất đồng bằng đối đầu quân sự.",
            },
            "A",
            (
                "Việt Nam là bạn, đối tác tin cậy và thành viên có trách nhiệm trên cơ sở độc "
                "lập tự chủ."
            ),
        ),
        (
            "Cuộc Tổng tiến công và nổi dậy Tết Mậu Thân năm 1968 đã buộc chính quyền Mỹ phải",
            {
                "A": (
                    "chấm dứt không điều kiện chiến tranh phá hoại miền Bắc và ngồi vào bàn "
                    "đàm phán Pari."
                ),
                "B": "rút toàn bộ quân viễn chinh khỏi miền Nam ngay trong tháng 2/1968.",
                "C": "ký kết ngay Hiệp định Giơnevơ về Đông Dương.",
                "D": "ngừng viện trợ tài chính cho toàn bộ khu vực châu Á.",
            },
            "A",
            "Thắng lợi Tết Mậu Thân 1968 làm lung lay ý chí xâm lược, mở đường cho đàm phán Pari.",
        ),
        (
            "Thành tựu nổi bật về chính trị - an ninh của ASEAN thông qua Hiệp ước Bali (1976) là",
            {
                "A": "xác lập nguyên tắc cơ bản trong quan hệ giữa các nước thành viên.",
                "B": "thành lập lực lượng hải quân chung kiểm soát Thái Bình Dương.",
                "C": "loại bỏ hoàn toàn thuế quan nội khối ngay trong năm 1976.",
                "D": "hợp nhất hiến pháp của năm nước sáng lập.",
            },
            "A",
            (
                "Hiệp ước Thân thiện và Hợp tác (Hiệp ước Bali 1976) xác định các nguyên tắc "
                "chung sống hòa bình."
            ),
        ),
        (
            (
                "Chiến thắng 'Điện Biên Phủ trên không' cuối năm 1972 gắn liền với việc quân "
                "dân miền Bắc đánh bại"
            ),
            {
                "A": "cuộc tập kích đường không chiến lược bằng B-52 của Mỹ.",
                "B": "cuộc hành quân Lam Sơn 719 ở Đường 9 - Nam Lào.",
                "C": "cuộc tấn công quy mô lớn vào căn cứ địa Việt Bắc.",
                "D": "kế hoạch Nava tại đồng bằng Bắc Bộ.",
            },
            "A",
            (
                "Trong 12 ngày đêm cuối tháng 12/1972, quân dân miền Bắc đập tan cuộc tập kích "
                "chiến lược B-52."
            ),
        ),
        (
            "Tác phẩm 'Đường Kách mệnh' (1927) của Nguyễn Ái Quốc tập hợp các bài giảng tại",
            {
                "A": "lớp huấn luyện cán bộ cách mạng ở Quảng Châu (Trung Quốc).",
                "B": "Hội nghị thành lập Đảng ở Cửu Long (Hương Cảng).",
                "C": "tòa soạn báo Người cùng khổ tại Pari.",
                "D": "căn cứ địa Pác Bó (Cao Bằng).",
            },
            "A",
            "Đây là tập bài giảng tại Quảng Châu nhằm truyền bá lý luận giải phóng dân tộc.",
        ),
        (
            (
                "Năm 2007, sự kiện đánh dấu bước tiến mới về thể chế pháp lý của ASEAN là việc "
                "thông qua"
            ),
            {
                "A": "Hiến chương ASEAN.",
                "B": "Tuyên bố Băng Cốc.",
                "C": "Hiệp ước Đông Nam Á không có vũ khí hạt nhân.",
                "D": "Tuyên bố Khu vực Hòa bình, Tự do và Trung lập.",
            },
            "A",
            "Hiến chương ASEAN được thông qua năm 2007 và có hiệu lực năm 2008.",
        ),
        (
            (
                "Nhiệm vụ hàng đầu của nước Việt Nam Dân chủ Cộng hòa ngay sau Cách mạng tháng "
                "Tám 1945 trong hoàn cảnh 'ngàn cân treo sợi tóc' là"
            ),
            {
                "A": "bảo vệ chính quyền cách mạng, diệt giặc đói, giặc dốt và giặc ngoại xâm.",
                "B": "tiến hành công nghiệp hóa nặng trên phạm vi toàn quốc ngay lập tức.",
                "C": "mở rộng liên minh thuế quan xuyên đại dương.",
                "D": "triển khai xây dựng hạ tầng giao thông cao tốc.",
            },
            "A",
            (
                "Chủ tịch Hồ Chí Minh phát động diệt giặc đói, giặc dốt, củng cố chính quyền "
                "và chống ngoại xâm."
            ),
        ),
        (
            "Từ thập niên 1990, công cuộc Đổi mới ở Việt Nam bước sang giai đoạn đẩy mạnh",
            {
                "A": "công nghiệp hóa, hiện đại hóa và hội nhập kinh tế quốc tế.",
                "B": "thu hẹp hoạt động xuất khẩu nông sản sang thị trường ngoài.",
                "C": "tái lập cơ chế tem phiếu phân phối lương thực.",
                "D": "giảm tỷ trọng kinh tế tư nhân trong nước.",
            },
            "A",
            "Sau khi thoát khủng hoảng, Việt Nam đẩy mạnh CNH-HĐH và hội nhập sâu rộng.",
        ),
        (
            (
                "Vai trò nổi bật của Việt Nam tại Liên hợp quốc trong những năm gần đây thể "
                "hiện rõ qua việc"
            ),
            {
                "A": (
                    "hai lần đảm nhiệm Ủy viên không thường trực Hội đồng Bảo an và tham gia "
                    "lực lượng gìn giữ hòa bình."
                ),
                "B": "trở thành thành viên sáng lập khối NATO năm 1949.",
                "C": "chủ trì soạn thảo toàn bộ Hiến chương Xan Phranxixcô năm 1945.",
                "D": "đặt trụ sở thường trực Tòa án Công lý Quốc tế tại Hà Nội.",
            },
            "A",
            (
                "Việt Nam hai lần trúng cử Ủy viên không thường trực HĐBA (2008-2009 và "
                "2020-2021) và cử lực lượng GGHB."
            ),
        ),
    ]
    questions = [
        _mcq(f"P1-{i}", stem, ch, ans, sol) for i, (stem, ch, ans, sol) in enumerate(mcqs, 1)
    ]

    tfs = [
        (
            "P2-1",
            "Đọc đoạn tư liệu sau:\n'Trật tự thế giới hai cực Ianta hình thành sau Chiến tranh thế "
            "giới thứ hai gắn với sự đối đầu giữa Mỹ và Liên Xô, trước khi từng bước suy yếu và "
            "sụp đổ vào đầu thập niên 1990.'",
            [
                (
                    (
                        "Trật tự Ianta phản ánh tương quan lực lượng mới sau Chiến tranh thế "
                        "giới thứ hai."
                    ),
                    True,
                    "Đúng: Hội nghị Ianta phân chia phạm vi ảnh hưởng giữa các nước thắng trận.",
                ),
                (
                    (
                        "Mối quan hệ Mỹ - Liên Xô trong trật tự Ianta luôn duy trì hợp tác "
                        "đồng minh chặt chẽ suốt 40 năm."
                    ),
                    False,
                    "Sai: Hai bên chuyển sang đối đầu Chiến tranh lạnh.",
                ),
                (
                    (
                        "Sự sụp đổ của Liên Xô năm 1991 đánh dấu sự chấm dứt hoàn toàn của "
                        "trật tự hai cực Ianta."
                    ),
                    True,
                    "Đúng: Trật tự hai cực chính thức kết thúc năm 1991.",
                ),
                (
                    "Trong giai đoạn hậu Chiến tranh lạnh, xu thế đa cực dần hình thành.",
                    True,
                    "Đúng: Nhiều trung tâm quyền lực kinh tế - chính trị vươn lên.",
                ),
            ],
        ),
        (
            "P2-2",
            "Đọc đoạn tư liệu sau:\n'Ngày 2/9/1945, tại Quảng trường Ba Đình, Chủ tịch Hồ "
            "Chí Minh đọc "
            "bản Tuyên ngôn Độc lập, khai sinh nước Việt Nam Dân chủ Cộng hòa.'",
            [
                (
                    (
                        "Tuyên ngôn Độc lập khẳng định quyền tự do, độc lập thiêng liêng của "
                        "dân tộc Việt Nam."
                    ),
                    True,
                    "Đúng: Đây là văn kiện pháp lý tuyên bố độc lập trước quốc dân và thế giới.",
                ),
                (
                    "Bản Tuyên ngôn Độc lập mở đầu sự kiện phát động Tổng khởi nghĩa tháng Tám.",
                    False,
                    "Sai: Tổng khởi nghĩa tháng Tám thắng lợi trước khi đọc Tuyên ngôn Độc lập.",
                ),
                (
                    "Sự ra đời của nước Việt Nam Dân chủ Cộng hòa mở ra kỷ nguyên độc lập, tự do.",
                    True,
                    "Đúng: Chấm dứt chế độ thực dân phong kiến.",
                ),
                (
                    (
                        "Văn kiện này trích dẫn tư tưởng bình đẳng từ Tuyên ngôn Độc lập Mỹ "
                        "(1776) và Tuyên ngôn Nhân quyền và Dân quyền Pháp (1791)."
                    ),
                    True,
                    "Đúng: Bác Hồ đã mở rộng quyền con người thành quyền dân tộc.",
                ),
            ],
        ),
        (
            "P2-3",
            "Đọc đoạn tư liệu sau:\n'Hiệp định Pari năm 1973 về chấm dứt chiến tranh, lập "
            "lại hòa bình "
            "ở Việt Nam quy định Hoa Kỳ tôn trọng độc lập, chủ quyền, thống nhất và toàn "
            "vẹn lãnh thổ của Việt Nam.'",
            [
                (
                    (
                        "Hiệp định Pari đánh dấu thắng lợi kết hợp giữa đấu tranh quân sự, "
                        "chính trị và ngoại giao."
                    ),
                    True,
                    "Đúng: Là thành quả của ba mặt trận đấu tranh suốt nhiều năm.",
                ),
                (
                    "Theo Hiệp định Pari, Mỹ rút quân viễn chinh khỏi miền Nam Việt Nam.",
                    True,
                    "Đúng: Tạo cục diện 'đánh cho Mỹ cút' thuận lợi cho ta.",
                ),
                (
                    "Hiệp định Pari được ký kết ngay trước khi Chiến dịch Điện Biên Phủ diễn ra.",
                    False,
                    "Sai: Điện Biên Phủ diễn ra năm 1954; Pari ký năm 1973.",
                ),
                (
                    (
                        "Hiệp định này tạo thời cơ thuận lợi tiến lên giải phóng hoàn toàn "
                        "miền Nam năm 1975."
                    ),
                    True,
                    "Đúng: So sánh lực lượng thay đổi có lợi cho cách mạng miền Nam.",
                ),
            ],
        ),
        (
            "P2-4",
            "Đọc đoạn tư liệu sau:\n'Từ năm 1986 đến nay, công cuộc Đổi mới đưa Việt Nam từ "
            "nước thiếu "
            "lương thực trở thành quốc gia xuất khẩu nông sản lớn, từng bước hội nhập sâu rộng vào "
            "nền kinh tế thế giới.'",
            [
                (
                    "Đổi mới là quá trình thay đổi mục tiêu độc lập dân tộc và chủ nghĩa xã hội.",
                    False,
                    (
                        "Sai: Đổi mới kiên định mục tiêu độc lập dân tộc và CNXH, chỉ đổi mới "
                        "cách làm."
                    ),
                ),
                (
                    (
                        "Chuyển sang kinh tế thị trường định hướng xã hội chủ nghĩa giúp giải "
                        "phóng sức sản xuất."
                    ),
                    True,
                    "Đúng: Thúc đẩy tăng trưởng kinh tế và đa dạng hóa thành phần kinh tế.",
                ),
                (
                    (
                        "Việc gia nhập WTO (2007) là một dấu mốc quan trọng của tiến trình hội "
                        "nhập kinh tế quốc tế."
                    ),
                    True,
                    "Đúng: Việt Nam trở thành thành viên thứ 150 của WTO.",
                ),
                (
                    (
                        "Thành tựu Đổi mới chứng minh đường lối kết hợp sức mạnh dân tộc và "
                        "sức mạnh thời đại là đúng đắn."
                    ),
                    True,
                    "Đúng: Củng cố thế và lực của đất nước.",
                ),
            ],
        ),
    ]
    for qid, stem, stmts in tfs:
        questions.append(_tf(qid, stem, stmts))
    return questions, [], []


def _build_geography() -> tuple[list[dict], list[dict], list[str]]:
    mcqs = [
        (
            "Nước ta nằm ở vị trí tiếp giáp giữa lục địa Á - Âu và",
            {
                "A": "Thái Bình Dương.",
                "B": "Đại Tây Dương.",
                "C": "Bắc Băng Dương.",
                "D": "Địa Trung Hải.",
            },
            "A",
            "Việt Nam nằm ở rìa đông bán đảo Đông Dương, giáp Biển Đông thông ra Thái Bình Dương.",
        ),
        (
            "Nguyên nhân chủ yếu làm cho miền Bắc nước ta có một mùa đông lạnh là do ảnh hưởng của",
            {
                "A": "gió mùa Đông Bắc kết hợp địa hình.",
                "B": "tín phong bán cầu Nam thổi mạnh.",
                "C": "dòng biển nóng từ xích đạo lên.",
                "D": "hiệu ứng phơn từ vịnh Thái Lan.",
            },
            "A",
            (
                "Gió mùa Đông Bắc tràn về kết hợp dãy núi vòng cung và bức chắn địa hình gây "
                "mùa đông lạnh."
            ),
        ),
        (
            (
                "Biểu hiện rõ nét của tính chất nhiệt đới ẩm gió mùa trên địa hình nước ta là "
                "quá trình"
            ),
            {
                "A": "xâm thực mạnh ở vùng đồi núi và bồi tụ ở đồng bằng.",
                "B": "đóng băng quanh năm tại các thung lũng miền Trung.",
                "C": "sa mạc hóa hoàn toàn đồng bằng sông Cửu Long.",
                "D": "giảm lượng phù sa của tất cả các con sông lớn.",
            },
            "A",
            "Mưa lớn tập trung theo mùa thúc đẩy phong hóa, xâm thực miền núi và bồi tụ đồng bằng.",
        ),
        (
            (
                "Loại rừng có vai trò chủ yếu chắn sóng, bảo vệ đê biển và đa dạng sinh học "
                "ven bờ là rừng"
            ),
            {
                "A": "ngập mặn phòng hộ.",
                "B": "thông ôn đới núi cao.",
                "C": "rụng lá mùa khô Tây Nguyên.",
                "D": "tre nứa đầu nguồn.",
            },
            "A",
            "Rừng ngập mặn ven biển phòng hộ đê điều và hạn chế xói lở bờ biển.",
        ),
        (
            "Cơ cấu lao động nước ta hiện nay đang chuyển dịch theo hướng tích cực nhờ",
            {
                "A": "tăng tỷ trọng lao động trong công nghiệp, xây dựng và dịch vụ.",
                "B": "giảm trình độ đào tạo chuyên môn kỹ thuật.",
                "C": "tập trung toàn bộ dân cư về khu vực miền núi.",
                "D": "xóa bỏ lao động khu vực có vốn đầu tư nước ngoài.",
            },
            "A",
            "Công nghiệp hóa và đô thị hóa kéo tỷ trọng lao động nông nghiệp giảm dần.",
        ),
        (
            (
                "Vùng sản xuất cây công nghiệp lâu năm lớn bậc nhất cả nước (cà phê, cao su, "
                "hồ tiêu) là"
            ),
            {
                "A": "Tây Nguyên.",
                "B": "Đồng bằng sông Hồng.",
                "C": "Duyên hải miền Trung.",
                "D": "Bắc Trung Bộ.",
            },
            "A",
            (
                "Tây Nguyên có diện tích đất đỏ bazan rộng lớn và khí hậu phân mùa thuận lợi "
                "cho cà phê, cao su."
            ),
        ),
        (
            (
                "Lợi thế nổi bật để phát triển ngành thủy sản đánh bắt và nuôi trồng ở Đồng "
                "bằng sông Cửu Long là"
            ),
            {
                "A": "mạng lưới sông ngòi kênh rạch dày đặc, ngư trường rộng và rừng ngập mặn.",
                "B": "khí hậu lạnh giá kéo dài giúp cá hồi sinh trưởng quanh năm.",
                "C": "địa hình núi đá vôi dốc đứng ven toàn bộ bờ biển.",
                "D": "không chịu tác động của thủy triều hay xâm nhập mặn.",
            },
            "A",
            (
                "Vùng có nguồn nước ngọt - lợ phong phú và tiếp giáp ngư trường lớn Cà Mau - "
                "Kiên Giang."
            ),
        ),
        (
            (
                "Công nghiệp sản xuất điện tử, thiết bị viễn thông ở nước ta phát triển nhanh "
                "thời gian qua chủ yếu nhờ"
            ),
            {
                "A": "thu hút đầu tư nước ngoài và lực lượng lao động trẻ tiếp thu nhanh kỹ thuật.",
                "B": "sản lượng khai thác quặng sắt nội địa đứng đầu thế giới.",
                "C": "tập trung xây dựng các nhà máy thủy điện công suất siêu lớn ở đồng bằng.",
                "D": "thay thế hoàn toàn nguồn vốn bằng lao động thủ công.",
            },
            "A",
            "Dòng vốn FDI công nghệ và lao động dồi dào giúp xuất khẩu điện tử tăng mạnh.",
        ),
        (
            (
                "Loại hình giao thông vận tải đóng vai trò chủ lực trong xuất nhập khẩu hàng "
                "hóa quốc tế của Việt Nam là"
            ),
            {
                "A": "đường biển.",
                "B": "đường sông nội đồng.",
                "C": "đường sắt đô thị.",
                "D": "đường ống dẫn nước.",
            },
            "A",
            "Đường biển chuyên chở khối lượng lớn hàng hóa đi xa với chi phí hợp lý.",
        ),
        (
            "Trung du và miền núi Bắc Bộ có thế mạnh hàng đầu cả nước về",
            {
                "A": "thủy điện và khoáng sản đa dạng.",
                "B": "trồng lúa thâm canh quy mô lớn nhất nước.",
                "C": "khai thác muối công nghiệp ven vịnh Bắc Bộ.",
                "D": "phát triển du lịch đảo san hô nhiệt đới quanh năm.",
            },
            "A",
            "Sông Đà, sông Lô - Gâm có tiềm năng thủy điện lớn cùng nhiều mỏ than, sắt, apatit.",
        ),
        (
            (
                "Ý nghĩa chủ yếu của việc phát triển lâm nghiệp kết hợp nông nghiệp (nông - "
                "lâm kết hợp) ở Bắc Trung Bộ là"
            ),
            {
                "A": "giữ nước đầu nguồn, chắn cát bay ven biển và nâng cao thu nhập người dân.",
                "B": "thay thế toàn bộ diện tích đất lúa bằng rừng đặc dụng.",
                "C": "giảm hoàn toàn nhu cầu thủy lợi ở đồng bằng.",
                "D": "mở rộng đô thị công nghiệp nặng lên sườn núi cao.",
            },
            "A",
            (
                "Hệ sinh thái đồi núi - đồng bằng - ven biển hẹp ngang đòi hỏi phòng hộ đầu "
                "nguồn và chắn cát."
            ),
        ),
        (
            "Ngành du lịch biển đảo của Duyên hải Nam Trung Bộ phát triển thuận lợi quanh năm nhờ",
            {
                "A": "nhiều bãi biển đẹp, vịnh nước sâu, khí hậu ấm áp và ít mùa đông lạnh.",
                "B": "tất cả các tháng đều có bão đổ bộ trực tiếp giúp sóng lớn.",
                "C": "gần hoàn toàn mạng lưới sông băng cổ đại.",
                "D": "chỉ tập trung một trung tâm du lịch duy nhất.",
            },
            "A",
            (
                "Vịnh Vân Phong, Nha Trang, Quy Nhơn, Mũi Né cùng thời tiết nắng ấm thuận lợi "
                "du lịch quanh năm."
            ),
        ),
        (
            "Đông Nam Bộ là vùng dẫn đầu cả nước về tổng sản phẩm trên địa bàn nhờ hội tụ lợi thế",
            {
                "A": "vị trí cầu nối kinh tế, hạ tầng đồng bộ và nguồn nhân lực chất lượng cao.",
                "B": "diện tích rừng tự nhiên lớn nhất trong cả nước.",
                "C": "địa hình cao nguyên đá vôi trên 2.000m chiếm ưu thế.",
                "D": "ngành khai thác thủy sản chiếm tỷ trọng cao nhất cơ cấu.",
            },
            "A",
            "Vùng có TP.HCM và các tỉnh công nghiệp - dịch vụ năng động nhất nước.",
        ),
        (
            "Biện pháp quan trọng để ứng phó với xâm nhập mặn mùa khô ở Đồng bằng sông Cửu Long là",
            {
                "A": (
                    "chủ động chuyển đổi cơ cấu mùa vụ, cây trồng thích ứng và xây dựng cống "
                    "kiểm soát mặn."
                ),
                "B": "bơm toàn bộ nước biển vào các kênh nội đồng quanh năm.",
                "C": "phá bỏ hết rừng phòng hộ ven biển để mở rộng nuôi bò.",
                "D": "ngừng hoàn toàn sản xuất nông nghiệp ở các tỉnh hạ lưu.",
            },
            "A",
            (
                "Kết hợp giải pháp công trình và thích ứng sinh kế giúp giữ ổn định sản xuất "
                "nông nghiệp."
            ),
        ),
        (
            "Đô thị hóa nước ta góp phần quan trọng thúc đẩy tăng trưởng kinh tế vì đô thị là nơi",
            {
                "A": (
                    "tập trung lao động chuyên môn cao, hạ tầng hiện đại và thị trường tiêu "
                    "thụ lớn."
                ),
                "B": "loại bỏ nhu cầu kết nối giữa nông thôn và thành thị.",
                "C": "chỉ phát triển sản xuất nông nghiệp tự cung tự cấp.",
                "D": "giảm tỷ trọng đóng góp của ngành dịch vụ tài chính.",
            },
            "A",
            "Đô thị tạo động lực đổi mới công nghệ, thương mại và việc làm phi nông nghiệp.",
        ),
        (
            (
                "Khó khăn lớn nhất về tự nhiên đối với sản xuất nông nghiệp ở Đồng bằng sông "
                "Hồng hiện nay là"
            ),
            {
                "A": (
                    "thời tiết thất thường (rét đậm, bão) và quỹ đất nông nghiệp bình quân đầu "
                    "người thấp."
                ),
                "B": "không có nguồn nước ngọt từ hệ thống sông lớn.",
                "C": "địa hình hoàn toàn là núi cao chia cắt sâu.",
                "D": "thiếu lao động truyền thống có kinh nghiệm thâm canh.",
            },
            "A",
            (
                "Dân số đông khiến diện tích đất canh tác bình quân đầu người thấp, lại chịu "
                "thiên tai gió mùa."
            ),
        ),
        (
            "Việc hình thành các khu kinh tế cửa khẩu ở vùng biên giới nhằm mục đích chủ yếu là",
            {
                "A": (
                    "thúc đẩy giao thương biên mậu, hợp tác quốc tế và phát triển kinh tế vùng "
                    "biên."
                ),
                "B": "chuyển toàn bộ cảng biển nước sâu lên vùng núi.",
                "C": "hạn chế xuất khẩu hàng hóa sang nước láng giềng.",
                "D": "ngừng xây dựng đường bộ kết nối liên vùng.",
            },
            "A",
            (
                "Mở rộng trao đổi hàng hóa, dịch vụ logistics qua biên giới và giữ vững an "
                "ninh quốc phòng."
            ),
        ),
        (
            (
                "Phát triển kinh tế biển đảo gắn với bảo vệ chủ quyền tại hai quần đảo Hoàng "
                "Sa và Trường Sa có ý nghĩa"
            ),
            {
                "A": (
                    "vừa khai thác hiệu quả tài nguyên biển vừa khẳng định vững chắc chủ quyền "
                    "quốc gia."
                ),
                "B": "chỉ phục vụ mục tiêu nghiên cứu địa chất thuần túy.",
                "C": "thay thế vai trò của toàn bộ các cảng hàng không đất liền.",
                "D": "tách rời hoạt động kinh tế khỏi nhiệm vụ an ninh quốc phòng.",
            },
            "A",
            "Kinh tế biển gắn chặt với bảo vệ toàn vẹn lãnh thổ vùng biển đảo Tổ quốc.",
        ),
    ]
    questions = [
        _mcq(f"P1-{i}", stem, ch, ans, sol) for i, (stem, ch, ans, sol) in enumerate(mcqs, 1)
    ]

    tfs = [
        (
            "P2-1",
            "Cho thông tin về chế độ nhiệt và mưa tại Hà Nội và TP. Hồ Chí Minh: Hà Nội có nhiệt "
            "độ trung bình tháng 1 khoảng 16,6 °C và tháng 7 khoảng 29,2 °C; TP. Hồ Chí Minh "
            "nhiệt độ tháng thấp nhất trên 25 °C và hai mùa mưa - khô rõ rệt.",
            [
                (
                    "Biên độ nhiệt năm ở Hà Nội cao hơn rõ rệt so với TP. Hồ Chí Minh.",
                    True,
                    "Đúng: Hà Nội chịu ảnh hưởng gió mùa Đông Bắc tạo mùa đông lạnh.",
                ),
                (
                    "TP. Hồ Chí Minh có mùa đông lạnh kéo dài từ tháng 11 đến tháng 3.",
                    False,
                    "Sai: TP.HCM mang tính chất cận xích đạo nóng quanh năm.",
                ),
                (
                    (
                        "Sự khác biệt chế độ nhiệt giữa hai thành phố chủ yếu do vĩ độ và gió "
                        "mùa Đông Bắc."
                    ),
                    True,
                    "Đúng: Vĩ độ tăng dần ra Bắc và tác động suy yếu dần của gió mùa Đông Bắc.",
                ),
                (
                    "Cả hai địa điểm đều nằm trong vùng khí hậu nhiệt đới ẩm gió mùa.",
                    True,
                    "Đúng: Lãnh thổ Việt Nam thuộc vành đai khí hậu nhiệt đới gió mùa.",
                ),
            ],
        ),
        (
            "P2-2",
            "Cho bảng số liệu giả định về cơ cấu trị giá xuất khẩu nhóm hàng công nghiệp chế biến "
            "và nông - lâm - thủy sản giai đoạn 2015–2024: tỷ trọng nhóm công nghiệp chế biến "
            "tăng từ 77% lên 85%, trong khi nhóm nông sản giảm tỷ trọng nhưng tăng về giá "
            "trị tuyệt đối.",
            [
                (
                    "Hàng công nghiệp chế biến ngày càng chiếm ưu thế trong cơ cấu xuất khẩu.",
                    True,
                    "Đúng: Tỷ trọng tăng liên tục đạt 85%.",
                ),
                (
                    "Giá trị tuyệt đối của nhóm nông - lâm - thủy sản giảm đi cùng với tỷ trọng.",
                    False,
                    "Sai: Đề nêu rõ giá trị tuyệt đối vẫn tăng.",
                ),
                (
                    "Xu hướng này phản ánh kết quả quá trình công nghiệp hóa hướng về xuất khẩu.",
                    True,
                    "Đúng: Cơ cấu hàng xuất khẩu chuyển mạnh sang hàng chế biến sâu.",
                ),
                (
                    (
                        "Để nâng cao giá trị gia tăng, cần tăng tỷ lệ nội địa hóa linh kiện "
                        "trong nước."
                    ),
                    True,
                    "Đúng: Giảm phụ thuộc gia công, nâng giá trị nội địa.",
                ),
            ],
        ),
        (
            "P2-3",
            "Cho nhận định về phát triển thủy điện và năng lượng tái tạo ở Việt Nam: Tây Nguyên và "
            "Duyên hải Nam Trung Bộ thu hút mạnh các dự án điện gió, điện mặt trời kết hợp "
            "thủy điện.",
            [
                (
                    (
                        "Số giờ nắng cao và tốc độ gió ổn định là điều kiện tự nhiên thuận lợi "
                        "cho điện mặt trời, điện gió."
                    ),
                    True,
                    "Đúng: Nam Trung Bộ và Tây Nguyên có bức xạ mặt trời và hành lang gió tốt.",
                ),
                (
                    "Phát triển năng lượng tái tạo đòi hỏi nâng cấp đồng bộ lưới điện truyền tải.",
                    True,
                    "Đúng: Tránh quá tải cục bộ vào giờ cao điểm phát điện.",
                ),
                (
                    (
                        "Các tỉnh ven biển Nam Trung Bộ hoàn toàn không có khả năng khai thác "
                        "điện gió ngoài khơi."
                    ),
                    False,
                    (
                        "Sai: Duyên hải Nam Trung Bộ có tiềm năng điện gió trên bờ và ngoài "
                        "khơi rất lớn."
                    ),
                ),
                (
                    "Đa dạng hóa nguồn điện góp phần đảm bảo an ninh năng lượng quốc gia.",
                    True,
                    "Đúng: Giảm rủi ro phụ thuộc một nguồn duy nhất khi thủy văn biến động.",
                ),
            ],
        ),
        (
            "P2-4",
            "Cho nhận định về phát triển vùng Đồng bằng sông Cửu Long: vùng chuyển mạnh từ tư duy "
            "sản xuất nông nghiệp thuần túy sang kinh tế nông nghiệp giá trị cao gắn với chế biến.",
            [
                (
                    (
                        "Việc xây dựng vùng nguyên liệu đạt chuẩn giúp nông sản mở rộng thị "
                        "trường xuất khẩu."
                    ),
                    True,
                    "Đúng: Đáp ứng truy xuất nguồn gốc và tiêu chuẩn kiểm dịch.",
                ),
                (
                    (
                        "Phát triển công nghiệp chế biến làm giảm giá trị thương phẩm của trái "
                        "cây và thủy sản."
                    ),
                    False,
                    "Sai: Chế biến sâu giúp tăng giá trị và kéo dài thời gian bảo quản.",
                ),
                (
                    (
                        "Giao thông đường bộ cao tốc và logistics đường thủy đóng vai trò then "
                        "chốt kết nối với TP.HCM."
                    ),
                    True,
                    "Đúng: Hạ tầng giúp giảm chi phí vận tải và tổn thất sau thu hoạch.",
                ),
                (
                    "Sản xuất gắn với thích ứng biến đổi khí hậu là định hướng lâu dài của vùng.",
                    True,
                    "Đúng: Phù hợp đặc thù vùng đồng bằng châu thổ thấp.",
                ),
            ],
        ),
    ]
    for qid, stem, stmts in tfs:
        questions.append(_tf(qid, stem, stmts))

    shorts = [
        (
            "P3-1",
            (
                "Một tỉnh có diện tích tự nhiên là 8.000 km² và dân số năm 2024 là 2.400.000 "
                "người. Tính mật độ dân số của tỉnh đó (làm tròn kết quả đến hàng đơn vị của "
                "người/km²)."
            ),
            "300",
            "Mật độ = 2.400.000 / 8.000 = 300 người/km².",
        ),
        (
            "P3-2",
            (
                "Nhiệt độ trung bình tháng nóng nhất tại một trạm khí tượng là 29,8 °C, tháng "
                "lạnh nhất là 16,3 °C. Tính biên độ nhiệt năm tại trạm đó (viết kết quả đến "
                "một chữ số thập phân, dùng dấu phẩy)."
            ),
            "13,5",
            "Biên độ nhiệt = 29,8 - 16,3 = 13,5 °C.",
        ),
        (
            "P3-3",
            (
                "Năm 2024, một vùng đạt diện tích gieo trồng lúa 400 nghìn ha với sản lượng "
                "2.520 nghìn tấn. Tính năng suất lúa bình quân (tạ/ha, làm tròn đến hàng đơn "
                "vị)."
            ),
            "63",
            "2.520 nghìn tấn = 25.200 nghìn tạ; Năng suất = 25.200 / 400 = 63 tạ/ha.",
        ),
        (
            "P3-4",
            (
                "Giá trị xuất khẩu của một địa phương đạt 18,4 tỉ USD và nhập khẩu đạt 15,2 tỉ "
                "USD. Tính cán cân xuất nhập khẩu của địa phương đó (tỉ USD, viết đến một chữ "
                "số thập phân)."
            ),
            "3,2",
            "Cán cân XNK = Xuất khẩu - Nhập khẩu = 18,4 - 15,2 = 3,2 tỉ USD.",
        ),
        (
            "P3-5",
            (
                "Tổng sản lượng thủy sản là 1.250 nghìn tấn, trong đó thủy sản nuôi trồng là "
                "900 nghìn tấn. Tính tỷ trọng thủy sản nuôi trồng (%, làm tròn đến hàng đơn "
                "vị)."
            ),
            "72",
            "Tỷ trọng = 900 / 1250 × 100% = 72%.",
        ),
        (
            "P3-6",
            (
                "Tại chân núi sườn đón gió cao 0 m có nhiệt độ là 28,0 °C. Theo quy luật đai "
                "cao (cứ lên 100 m giảm 0,6 °C), tính nhiệt độ ở độ cao 1.500 m (đơn vị °C, "
                "làm tròn đến hàng đơn vị)."
            ),
            "19",
            "Giảm 15 × 0,6 = 9,0 °C; Nhiệt độ = 28,0 - 9,0 = 19 °C.",
        ),
    ]
    for qid, stem, ans, sol in shorts:
        questions.append(_short(qid, stem, ans, sol))

    return questions, [], []


def _build_chemistry() -> tuple[list[dict], list[dict], list[str]]:
    front_matter = [
        "Cho biết nguyên tử khối: H = 1; C = 12; N = 14; O = 16; Na = 23; Mg = 24; Al = 27; "
        "S = 32; Cl = 35,5; Ca = 40; Fe = 56; Cu = 64."
    ]
    passages = [
        {
            "id": "context_7_8",
            "section": "P1",
            "kind": "context",
            "questionRange": [7, 8],
            "instruction": "Dùng thông tin sau để trả lời câu 7 và câu 8:",
            "heading": "ĐIỆN PHÂN DUNG DỊCH MUỐI ĐỒNG(II) SUNFAT",
            "text": (
                "Tiến hành điện phân dung dịch $CuSO_4$ 0,2M với hai điện cực trơ (graphit) bằng "
                "dòng điện một chiều cường độ không đổi. Trong giai đoạn đầu, ở catot có kim loại "
                "đỏ bám vào, còn ở anot thoát ra khí không màu, duy trì sự cháy."
            ),
        }
    ]
    mcqs = [
        (
            (
                "Thủy phân hoàn toàn ethyl acetate ($CH_3COOC_2H_5$) trong dung dịch NaOH đun "
                "nóng thu được muối có công thức là"
            ),
            {"A": "$CH_3COONa$.", "B": "$HCOONa$.", "C": "$C_2H_5COONa$.", "D": "$C_2H_5ONa$."},
            "A",
            "Phản ứng xà phòng hóa tạo muối $CH_3COONa$ và ancol $C_2H_5OH$.",
        ),
        (
            "Chất nào sau đây thuộc loại đisaccarit?",
            {"A": "Saccharose.", "B": "Glucose.", "C": "Fructose.", "D": "Cellulose."},
            "A",
            "Saccharose ($C_{12}H_{22}O_{11}$) là đisaccarit gồm gốc glucose và fructose.",
        ),
        (
            "Dung dịch chất nào sau đây làm quỳ tím hóa xanh?",
            {"A": "Methylamine.", "B": "Glycine.", "C": "Phenol.", "D": "Acetic acid."},
            "A",
            "Amine béo ($CH_3NH_2$) có tính bazơ mạnh hơn amoniac nên làm xanh quỳ tím.",
        ),
        (
            "Tơ nào sau đây thuộc loại tơ tổng hợp?",
            {"A": "Tơ capron.", "B": "Tơ tằm.", "C": "Bông.", "D": "Tơ visco."},
            "A",
            "Tơ capron (nylon-6) điều chế bằng phản ứng tổng hợp hóa học, thuộc tơ tổng hợp.",
        ),
        (
            "Kim loại nào sau đây dẫn điện tốt nhất ở điều kiện thường?",
            {"A": "Ag.", "B": "Cu.", "C": "Al.", "D": "Fe."},
            "A",
            "Thứ tự độ dẫn điện giảm dần: Ag > Cu > Au > Al > Fe.",
        ),
        (
            (
                "Trong pin Galvani $Zn - Cu$ làm việc ở điều kiện chuẩn, cực âm (anot) là "
                "thanh kim loại nào?"
            ),
            {"A": "Zn.", "B": "Cu.", "C": "Cả Zn và Cu.", "D": "Cầu muối $KCl$."},
            "A",
            "Zn có thế điện cực chuẩn âm hơn nên bị oxi hóa ở cực âm (anot).",
        ),
        (
            (
                "Bán phản ứng chính xảy ra tại catot trong giai đoạn đầu của quá trình điện "
                "phân nói trên là"
            ),
            {
                "A": "$Cu^{2+} + 2e \\rightarrow Cu$.",
                "B": "$2H_2O + 2e \\rightarrow H_2 + 2OH^-$.",
                "C": "$2H_2O \\rightarrow O_2 + 4H^+ + 4e$.",
                "D": "$SO_4^{2-} + 2e \\rightarrow SO_2$.",
            },
            "A",
            "Ion $Cu^{2+}$ có tính oxi hóa mạnh hơn $H_2O$ nên bị khử trước tạo Cu bám trên catot.",
        ),
        (
            "Khí không màu thoát ra ở anot trong giai đoạn trên là",
            {"A": "$O_2$.", "B": "$H_2$.", "C": "$SO_2$.", "D": "$Cl_2$."},
            "A",
            (
                "Nước bị oxi hóa ở anot ($2H_2O \\rightarrow O_2 + 4H^+ + 4e$) tạo khí $O_2$ "
                "duy trì sự cháy."
            ),
        ),
        (
            (
                "Ở điều kiện thường, kim loại natri (Na) phản ứng mãnh liệt với nước tạo thành "
                "khí $H_2$ và dung dịch chứa"
            ),
            {"A": "$NaOH$.", "B": "$Na_2O$.", "C": "$NaCl$.", "D": "$Na_2SO_4$."},
            "A",
            "$2Na + 2H_2O \\rightarrow 2NaOH + H_2\\uparrow$.",
        ),
        (
            (
                "Nước cứng vĩnh cửu chứa nhiều các ion $Ca^{2+}$, $Mg^{2+}$ kết hợp với anion "
                "nào sau đây?"
            ),
            {"A": "$Cl^-$ và $SO_4^{2-}$.", "B": "$HCO_3^-$.", "C": "$CO_3^{2-}$.", "D": "$OH^-$."},
            "A",
            "Nước cứng vĩnh cửu gây bởi muối clorua và sunfat của $Ca^{2+}, Mg^{2+}$.",
        ),
        (
            "Số nguyên tử cacbon trong phân tử alanin ($CH_3-CH(NH_2)-COOH$) là",
            {"A": "3", "B": "2", "C": "4", "D": "5"},
            "A",
            "Alanin có công thức phân tử $C_3H_7O_2N$, gồm 3 nguyên tử C.",
        ),
        (
            "Kim loại sắt (Fe) tác dụng với dung dịch $HCl$ loãng dư tạo thành sản phẩm muối là",
            {"A": "$FeCl_2$.", "B": "$FeCl_3$.", "C": "$Fe(OH)_2$.", "D": "$Fe(OH)_3$."},
            "A",
            "Fe khử ion $H^+$ thành $H_2$ và chuyển lên số oxi hóa +2 ($FeCl_2$).",
        ),
        (
            "Chất nào sau đây có thể trùng hợp tạo thành polime PVC?",
            {
                "A": "$CH_2=CH-Cl$.",
                "B": "$CH_2=CH_2$.",
                "C": "$CH_2=CH-CH_3$.",
                "D": "$C_6H_5-CH=CH_2$.",
            },
            "A",
            "Vinyl clorua ($CH_2=CH-Cl$) trùng hợp tạo poly(vinyl chloride) (PVC).",
        ),
        (
            (
                "Phản ứng giữa $Al$ và $Fe_2O_3$ ở nhiệt độ cao trong kỹ thuật hàn đường ray "
                "được gọi là phản ứng"
            ),
            {"A": "nhiệt nhôm.", "B": "điện phân nóng chảy.", "C": "thủy phân.", "D": "tráng bạc."},
            "A",
            "Al khử oxit sắt ở nhiệt độ cao tỏa nhiều nhiệt được gọi là phản ứng nhiệt nhôm.",
        ),
        (
            (
                "Cho glucose tác dụng với lượng dư dung dịch $AgNO_3$ trong $NH_3$ đun nóng. "
                "Nhờ nhóm chức nào mà glucose tham gia phản ứng tráng bạc?"
            ),
            {
                "A": "Nhóm $-CHO$.",
                "B": "Nhóm $-COOH$.",
                "C": "Nhóm $-NH_2$.",
                "D": "Liên kết peptit.",
            },
            "A",
            "Dạng mạch hở của glucose chứa nhóm anđehit $-CHO$ bị oxi hóa bởi $[Ag(NH_3)_2]^+$.",
        ),
        (
            (
                "Trong phức chất bát diện $[Co(NH_3)_6]^{3+}$, số phối tử liên kết với nguyên "
                "tử trung tâm $Co^{3+}$ là"
            ),
            {"A": "6", "B": "3", "C": "4", "D": "2"},
            "A",
            "Sáu phân tử $NH_3$ đóng vai trò phối tử quanh ion trung tâm $Co^{3+}$.",
        ),
        (
            (
                "Biện pháp hiệu quả nhằm bảo vệ vỏ tàu biển bằng thép khỏi ăn mòn điện hóa là "
                "gắn vào phần ngâm dưới nước các tấm kim loại"
            ),
            {"A": "kẽm (Zn).", "B": "đồng (Cu).", "C": "bạc (Ag).", "D": "chì (Pb)."},
            "A",
            "Zn hoạt động hóa học mạnh hơn Fe nên đóng vai trò anot hy sinh bị ăn mòn trước.",
        ),
        (
            "Giá trị pH của dung dịch $HCl$ 0,01M ở $25^\\circ C$ bằng",
            {"A": "2", "B": "1", "C": "3", "D": "12"},
            "A",
            "$[H^+] = 10^{-2} M \\Rightarrow pH = -\\log(10^{-2}) = 2$.",
        ),
    ]
    questions = []
    for idx, (stem, ch, ans, sol) in enumerate(mcqs, 1):
        pid = "context_7_8" if idx in (7, 8) else None
        questions.append(_mcq(f"P1-{idx}", stem, ch, ans, sol, passage_id=pid))

    tfs = [
        (
            "P2-1",
            "Xét phản ứng ester hóa tổng hợp isoamyl acetate (mùi chuối chín) từ isoamyl alcohol "
            "và acetic acid có mặt $H_2SO_4$ đặc xúc tác, đun nóng.",
            [
                (
                    "Phản ứng ester hóa giữa ancol và axit cacboxylic là phản ứng thuận nghịch.",
                    True,
                    "Đúng: Phản ứng đạt cân bằng hóa học.",
                ),
                (
                    (
                        "$H_2SO_4$ đặc vừa làm chất xúc tác vừa hút nước giúp chuyển dịch cân "
                        "bằng theo chiều thuận."
                    ),
                    True,
                    "Đúng: Hấp thụ nước làm tăng hiệu suất tạo ester.",
                ),
                (
                    "Isoamyl acetate tan vô hạn trong nước lạnh.",
                    False,
                    "Sai: Ester ít tan trong nước và nhẹ hơn nước nổi thành lớp trên.",
                ),
                (
                    (
                        "Nhỏ thêm dung dịch NaCl bão hòa vào hỗn hợp sau phản ứng giúp tách "
                        "lớp ester dễ hơn."
                    ),
                    True,
                    "Đúng: Giảm độ tan của ester trong lớp nước và tăng khối lượng riêng lớp nước.",
                ),
            ],
        ),
        (
            "P2-2",
            "Xét tính chất của amino axit glycine ($H_2N-CH_2-COOH$) trong dung dịch nước.",
            [
                (
                    (
                        "Glycine là hợp chất lưỡng tính, vừa tác dụng với dung dịch HCl vừa "
                        "tác dụng với dung dịch NaOH."
                    ),
                    True,
                    "Đúng: Chứa nhóm $-NH_2$ tính bazơ và nhóm $-COOH$ tính axit.",
                ),
                (
                    (
                        "Ở trạng thái rắn kết tinh, glycine tồn tại chủ yếu ở dạng ion lưỡng "
                        "cực $H_3N^+-CH_2-COO^-$."
                    ),
                    True,
                    "Đúng: Do tương tác axit-bazơ nội phân tử.",
                ),
                (
                    "Glycine làm mất màu dung dịch $Br_2$ ngay ở nhiệt độ thường như anilin.",
                    False,
                    "Sai: Glycine không có vòng thơm hoạt hóa như anilin.",
                ),
                (
                    "Đun nóng glycine trong ancol metylic bão hòa khí HCl thu được muối ester hóa.",
                    True,
                    "Đúng: Tạo muối clorua của metyl glyxinat.",
                ),
            ],
        ),
        (
            "P2-3",
            "Xét các kim loại chuyển tiếp dãy thứ nhất từ Sc đến Cu.",
            [
                (
                    (
                        "Kim loại chuyển tiếp dãy thứ nhất thường có nhiều trạng thái oxi hóa "
                        "khác nhau trong hợp chất."
                    ),
                    True,
                    "Đúng: Do có các electron hóa trị trên phân lớp 3d và 4s gần mức năng lượng.",
                ),
                (
                    "Dung dịch muối $Fe^{3+}$ thường có màu vàng nâu đặc trưng.",
                    True,
                    "Đúng: Ion chuyển tiếp có màu trong dung dịch nước.",
                ),
                (
                    (
                        "Đồng (Cu) dễ dàng đẩy được $H_2$ khỏi dung dịch $H_2SO_4$ loãng ở "
                        "nhiệt độ thường."
                    ),
                    False,
                    "Sai: Cu đứng sau H trong dãy điện hóa.",
                ),
                (
                    (
                        "Hợp chất của sắt như $Fe_2O_3$ đóng vai trò xúc tác hoặc chất màu "
                        "quan trọng trong công nghiệp."
                    ),
                    True,
                    "Đúng: Ứng dụng rộng rãi trong sản xuất và vật liệu.",
                ),
            ],
        ),
        (
            "P2-4",
            "Xét quy trình sản xuất amoniac ($NH_3$) theo chu trình Haber-Bosch: "
            "$N_2(g) + 3H_2(g) \\rightleftharpoons 2NH_3(g)$ với $\\Delta_r H^\\circ_{298} < 0$.",
            [
                (
                    "Phản ứng tổng hợp $NH_3$ từ $N_2$ và $H_2$ là phản ứng tỏa nhiệt.",
                    True,
                    "Đúng: Biến thiên enthalpy âm.",
                ),
                (
                    "Tăng áp suất của hệ phản ứng làm cân bằng chuyển dịch theo chiều thuận.",
                    True,
                    "Đúng: Số mol khí giảm từ 4 mol xuống 2 mol.",
                ),
                (
                    "Chất xúc tác sắt (Fe) làm tăng hằng số cân bằng $K_C$ của phản ứng.",
                    False,
                    "Sai: Xúc tác chỉ làm tăng tốc độ đạt cân bằng, không đổi $K_C$.",
                ),
                (
                    "Làm lạnh hỗn hợp khí đi ra khỏi tháp tổng hợp để ngưng tụ thu $NH_3$ lỏng.",
                    True,
                    "Đúng: $NH_3$ có nhiệt độ sôi cao hơn nhiều so với $N_2$ và $H_2$.",
                ),
            ],
        ),
    ]
    for qid, stem, stmts in tfs:
        questions.append(_tf(qid, stem, stmts))

    shorts = [
        (
            "P3-1",
            (
                "Cho các chất: (1) ethylene; (2) methyl methacrylate; (3) caprolactam; (4) "
                "acrylonitrile. Liệt kê số thứ tự theo dãy tăng dần các monome trùng hợp tạo "
                "được polime có chứa nguyên tố nitơ (ví dụ 13)."
            ),
            "34",
            "Caprolactam (3) tạo tơ capron và acrylonitrile (4) tạo tơ nitron đều chứa N.",
        ),
        (
            "P3-2",
            (
                "Cho 4,4 gam ethyl acetate tác dụng vừa đủ với 100 mL dung dịch NaOH 1M. Cô "
                "cạn dung dịch sau phản ứng thu được m gam chất rắn khan. Tính giá trị của m "
                "(làm tròn đến một chữ số thập phân)."
            ),
            "6,1",
            (
                "$n_{ester} = 4,4/88 = 0,05$ mol; $n_{NaOH} = 0,1$ mol (dư 0,05 mol). $m_{rắn} "
                "= 0,05 \\times 82 + 0,05 \\times 40 = 4,1 + 2,0 = 6,1$ g."
            ),
        ),
        (
            "P3-3",
            (
                "Cho 5,6 gam sắt (Fe) tan hết trong dung dịch $H_2SO_4$ loãng dư thu được V "
                "lít khí $H_2$ (đkc: $25^\\circ C$, 1 bar, $V_{mol} = 24,79$ lít/mol). Tính V "
                "(làm tròn đến phần trăm, dùng dấu phẩy)."
            ),
            "2,48",
            (
                "$n_{Fe} = 0,1$ mol $\\Rightarrow n_{H_2} = 0,1$ mol $\\Rightarrow V = 0,1 "
                "\\times 24,79 = 2,479 \\approx 2,48$ lít."
            ),
        ),
        (
            "P3-4",
            "Có bao nhiêu amin bậc một ứng với công thức phân tử $C_3H_9N$?",
            "2",
            "Gồm 2 đồng phân bậc một: $CH_3-CH_2-CH_2-NH_2$ và $CH_3-CH(NH_2)-CH_3$.",
        ),
        (
            "P3-5",
            (
                "Thủy phân hoàn toàn 18 gam glucose lên men rượu với hiệu suất 80% thu được m "
                "gam ancol etylic. Tính giá trị của m (làm tròn đến một chữ số thập phân)."
            ),
            "7,4",
            (
                "$n_{glu} = 0,1$ mol; $n_{C_2H_5OH} = 0,2 \\times 0,8 = 0,16$ mol $\\Rightarrow "
                "m = 0,16 \\times 46 = 7,36 \\approx 7,4$ g."
            ),
        ),
        (
            "P3-6",
            (
                "Cho dung dịch gồm $Cu(NO_3)_2$ 0,1 mol và $AgNO_3$ 0,2 mol phản ứng hết với "
                "bột Mg dư. Tính khối lượng kim loại tối đa thu được sau phản ứng (đơn vị gam, "
                "làm tròn đến hàng đơn vị)."
            ),
            "28",
            "$m = 0,1 \\times 64 + 0,2 \\times 108 = 6,4 + 21,6 = 28$ gam.",
        ),
    ]
    for qid, stem, ans, sol in shorts:
        questions.append(_short(qid, stem, ans, sol))

    return questions, passages, front_matter


def _build_biology() -> tuple[list[dict], list[dict], list[str]]:
    mcqs = [
        (
            "Đơn phân cấu tạo nên phân tử ADN là",
            {"A": "nuclêôtit.", "B": "axit amin.", "C": "glucôzơ.", "D": "axit béo."},
            "A",
            "ADN được cấu tạo từ 4 loại đơn phân nuclêôtit A, T, G, X.",
        ),
        (
            (
                "Trong quá trình nhân đôi ADN, enzim nào lắp ghép các nuclêôtit tự do theo "
                "nguyên tắc bổ sung để tổng hợp mạch mới?"
            ),
            {"A": "ADN pôlimeraza.", "B": "ARN pôlimeraza.", "C": "Restrictaza.", "D": "Lipaza."},
            "A",
            "ADN pôlimeraza tổng hợp mạch mới theo chiều 5' -> 3'.",
        ),
        (
            "Phiên mã là quá trình tổng hợp phân tử nào từ mạch khuôn ADN?",
            {"A": "ARN.", "B": "Prôtêin.", "C": "Lipit.", "D": "Xenlulôzơ."},
            "A",
            "Phiên mã tạo mARN, tARN hoặc rARN từ gen trên ADN.",
        ),
        (
            (
                "Bộ ba mở đầu trên phân tử mARN ở sinh vật nhân thực thường mã hóa axit amin "
                "Methionine là"
            ),
            {"A": "5'-AUG-3'.", "B": "5'-UAA-3'.", "C": "5'-UAG-3'.", "D": "5'-UGA-3'."},
            "A",
            "AUG là bộ ba mở đầu dịch mã; UAA, UAG, UGA là các bộ ba kết thúc.",
        ),
        (
            "Dạng đột biến gen thay thế một cặp nuclêôtit thường dẫn tới",
            {
                "A": "giữ nguyên tổng số nuclêôtit của gen.",
                "B": "làm mất hẳn một nhiễm sắc thể.",
                "C": "gấp đôi số lượng nhiễm sắc thể trong nhân.",
                "D": "tăng chiều dài gen thêm hai cặp nuclêôtit.",
            },
            "A",
            "Thay thế một cặp nuclêôtit không làm thay đổi tổng số nuclêôtit và chiều dài gen.",
        ),
        (
            (
                "Theo quy luật phân li độc lập của Mendel, phép lai $AaBb \\times AaBb$ (mỗi "
                "gen quy định một tính trạng, trội hoàn toàn) cho tối đa bao nhiêu loại kiểu "
                "hình?"
            ),
            {"A": "4", "B": "2", "C": "3", "D": "9"},
            "A",
            "$2 \\times 2 = 4$ loại kiểu hình ở đời con.",
        ),
        (
            (
                "Hiện tượng nhiều gen không alen cùng tác động đến sự hình thành một kiểu hình "
                "duy nhất gọi là"
            ),
            {
                "A": "tương tác gen.",
                "B": "hoán vị gen.",
                "C": "liên kết giới tính.",
                "D": "di truyền ngoài nhân.",
            },
            "A",
            "Hai hay nhiều gen cùng tương tác quy định một tính trạng gọi là tương tác gen.",
        ),
        (
            (
                "Ở loài giao phối, nhân tố tiến hóa nào tạo ra nguồn biến dị sơ cấp phong phú "
                "cho chọn lọc tự nhiên?"
            ),
            {
                "A": "Đột biến.",
                "B": "Phiêu bạt di truyền.",
                "C": "Giao phối không ngẫu nhiên.",
                "D": "Cách li địa lý.",
            },
            "A",
            "Đột biến tạo ra các alen mới làm nguồn nguyên liệu sơ cấp cho tiến hóa.",
        ),
        (
            (
                "Các cơ quan có cùng nguồn gốc phôi thai nhưng thực hiện chức năng khác nhau ở "
                "các loài (ví dụ cánh dơi và tay người) là cơ quan"
            ),
            {
                "A": "tương đồng.",
                "B": "tương tự.",
                "C": "thoái hóa hoàn toàn.",
                "D": "biến dị thường biến.",
            },
            "A",
            "Cơ quan tương đồng phản ánh tiến hóa phân li từ tổ tiên chung.",
        ),
        (
            (
                "Tập hợp cá thể cùng loài sống trong một khoảng không gian xác định, tại một "
                "thời điểm nhất định và có khả năng giao phối sinh sản tạo thế hệ mới hữu thụ "
                "gọi là"
            ),
            {
                "A": "quần thể sinh vật.",
                "B": "quần xã sinh vật.",
                "C": "hệ sinh thái.",
                "D": "sinh quyển.",
            },
            "A",
            "Đây là định nghĩa quần thể sinh vật.",
        ),
        (
            (
                "Mối quan hệ giữa cây tầm gửi sống bám trên thân cây gỗ để hút nước và muối "
                "khoáng là quan hệ"
            ),
            {"A": "kí sinh.", "B": "cộng sinh.", "C": "hội sinh.", "D": "cạnh tranh cùng loài."},
            "A",
            "Tầm gửi gây hại nhẹ cho vật chủ khi lấy nước và chất khoáng.",
        ),
        (
            (
                "Trong hệ sinh thái, sinh vật nào đóng vai trò chuyển hóa năng lượng ánh sáng "
                "mặt trời thành năng lượng hóa học trong chất hữu cơ?"
            ),
            {
                "A": "Sinh vật sản xuất.",
                "B": "Sinh vật tiêu thụ bậc 2.",
                "C": "Sinh vật phân giải xác chết.",
                "D": "Động vật ăn thịt đầu bảng.",
            },
            "A",
            "Thực vật và sinh vật tự dưỡng quang hợp là sinh vật sản xuất.",
        ),
        (
            (
                "Một quần thể có cấu trúc di truyền đạt cân bằng Hardy-Weinberg với tần số "
                "alen $A = 0,6$ và $a = 0,4$. Tỷ lệ kiểu gen dị hợp tử $Aa$ trong quần thể là"
            ),
            {"A": "0,48", "B": "0,36", "C": "0,16", "D": "0,24"},
            "A",
            "Tỷ lệ $Aa = 2pq = 2 \\times 0,6 \\times 0,4 = 0,48$.",
        ),
        (
            (
                "Thể đột biến có bộ nhiễm sắc thể tăng thêm một chiếc ở một cặp tương đồng "
                "($2n + 1$) được gọi là"
            ),
            {"A": "thể ba.", "B": "thể một.", "C": "thể tam bội.", "D": "thể tứ bội."},
            "A",
            "Thể $2n + 1$ là thể ba (ví dụ hội chứng Down ở cặp NST 21).",
        ),
        (
            "Ở thực vật trên cạn, quá trình thoát hơi nước qua khí khổng tạo động lực giúp",
            {
                "A": "vận chuyển nước, muối khoáng từ rễ lên lá và điều hòa nhiệt độ lá.",
                "B": "ngừng hoàn toàn quá trình quang hợp vào ban ngày.",
                "C": "đẩy toàn bộ chất diệp lục xuống hệ rễ.",
                "D": "làm tế bào rễ mất khả năng hút khoáng chủ động.",
            },
            "A",
            "Thoát hơi nước là động lực đầu trên của dòng mạch gỗ và giúp hạ nhiệt bề mặt lá.",
        ),
        (
            (
                "Trong cơ chế điều hòa hoạt động Operon Lac ở vi khuẩn *E. coli*, lactôzơ đóng "
                "vai trò là chất cảm ứng gắn vào"
            ),
            {
                "A": "prôtêin ức chế làm mất hoạt tính bám vào vùng vận hành.",
                "B": "trực tiếp vùng kết thúc phiên mã của gen cấu trúc.",
                "C": "chuỗi pôlipeptit vừa được tổng hợp tại ribôxôm.",
                "D": "phân tử rARN trong nhân thực.",
            },
            "A",
            (
                "Lactôzơ làm thay đổi cấu hình không gian prôtêin ức chế để ARN pôlimeraza "
                "trượt qua phiên mã."
            ),
        ),
        (
            "Đặc trưng nào sau đây chỉ có ở quần xã sinh vật mà không có ở một quần thể đơn lẻ?",
            {
                "A": "Độ đa dạng loài và loài ưu thế.",
                "B": "Tỉ lệ giới tính đực/cái.",
                "C": "Mật độ cá thể cùng loài.",
                "D": "Nhóm tuổi trước sinh sản.",
            },
            "A",
            "Quần xã gồm nhiều quần thể loài khác nhau nên có độ đa dạng và thành phần loài.",
        ),
        (
            "Di truyền ngoài nhân (di truyền qua tế bào chất ở ti thể, lục lạp) thường có đặc điểm",
            {
                "A": "con sinh ra mang kiểu hình giống mẹ ở phép lai thuận nghịch.",
                "B": "phân li kiểu hình đúng tỉ lệ 3 : 1 ở mọi phép lai.",
                "C": "chỉ biểu hiện ở giới đực qua nhiễm sắc thể Y.",
                "D": "không chịu ảnh hưởng của đột biến phân tử ADN.",
            },
            "A",
            "Hợp tử nhận chủ yếu tế bào chất từ trứng của mẹ nên biểu hiện di truyền theo dòng mẹ.",
        ),
    ]
    questions = [
        _mcq(f"P1-{i}", stem, ch, ans, sol) for i, (stem, ch, ans, sol) in enumerate(mcqs, 1)
    ]

    tfs = [
        (
            "P2-1",
            (
                "Xét quá trình truyền đạt thông tin di truyền theo sơ đồ: ADN -> mARN -> "
                "Prôtêin trong tế bào nhân thực."
            ),
            [
                (
                    "Quá trình tổng hợp mARN diễn ra chủ yếu trong nhân tế bào.",
                    True,
                    "Đúng: ADN khuôn nằm trong nhân tế bào.",
                ),
                (
                    (
                        "Mạch mARN sơ khai ở sinh vật nhân thực được dịch mã trực tiếp mà "
                        "không cần cắt bỏ intron."
                    ),
                    False,
                    "Sai: Tiền mARN nhân thực cần cắt bỏ intron, nối exon thành mARN trưởng thành.",
                ),
                (
                    "Quá trình dịch mã có sự tham gia của ribôxôm và tARN vận chuyển axit amin.",
                    True,
                    "Đúng: tARN mang bộ ba đối mã khớp bổ sung với codon trên mARN.",
                ),
                (
                    (
                        "Nhiều ribôxôm cùng trượt trên một mARN (pôliribôxôm) giúp tăng hiệu "
                        "suất tổng hợp prôtêin."
                    ),
                    True,
                    "Đúng: Tổng hợp nhanh nhiều chuỗi pôlipeptit cùng loại.",
                ),
            ],
        ),
        (
            "P2-2",
            (
                "Nghiên cứu một quần thể thực vật tự thụ phấn bắt buộc có kiểu gen xuất phát "
                "ban đầu gồm 100% cá thể dị hợp $Aa$."
            ),
            [
                (
                    "Sau mỗi thế hệ tự thụ phấn, tỷ lệ thể dị hợp $Aa$ giảm đi một nửa.",
                    True,
                    "Đúng: Sau n thế hệ, tỷ lệ $Aa = (1/2)^n$.",
                ),
                (
                    "Tần số alen $A$ và $a$ thay đổi mạnh qua các thế hệ chỉ do tự thụ phấn.",
                    False,
                    (
                        "Sai: Tự thụ phấn không làm thay đổi tần số alen nếu không có chọn lọc "
                        "hay đột biến."
                    ),
                ),
                (
                    (
                        "Tỷ lệ đồng hợp tử tăng dần và có thể làm tăng nguy cơ biểu hiện alen "
                        "lặn có hại."
                    ),
                    True,
                    "Đúng: Tăng đồng hợp $AA$ và $aa$.",
                ),
                (
                    (
                        "Trong điều kiện tự thụ phấn nghiêm ngặt, quần thể tiến tới phân hóa "
                        "thành các dòng thuần."
                    ),
                    True,
                    "Đúng: Là cơ sở tạo dòng thuần chủng trong chọn giống.",
                ),
            ],
        ),
        (
            "P2-3",
            (
                "Phân tích chuỗi thức ăn trên đồng cỏ: Cỏ -> Châu chấu -> Ếch đồng -> Rắn nước "
                "-> Đại bàng."
            ),
            [
                (
                    "Cỏ thuộc bậc dinh dưỡng cấp 1 và là sinh vật sản xuất.",
                    True,
                    "Đúng: Sinh vật tự dưỡng khởi đầu chuỗi thức ăn.",
                ),
                (
                    "Châu chấu là sinh vật tiêu thụ bậc 2.",
                    False,
                    (
                        "Sai: Châu chấu ăn cỏ trực tiếp nên là sinh vật tiêu thụ bậc 1 (bậc "
                        "dinh dưỡng cấp 2)."
                    ),
                ),
                (
                    (
                        "Khi chuyển qua mỗi bậc dinh dưỡng, phần lớn năng lượng bị tiêu hao "
                        "qua hô hấp và chất thải."
                    ),
                    True,
                    "Đúng: Hiệu suất sinh thái chuyển bậc chỉ đạt khoảng 10%.",
                ),
                (
                    (
                        "Loại bỏ toàn bộ ếch đồng sẽ ảnh hưởng trực tiếp tới kích thước quần "
                        "thể châu chấu và rắn nước."
                    ),
                    True,
                    "Đúng: Làm đứt mắt xích trung gian của lưới thức ăn.",
                ),
            ],
        ),
        (
            "P2-4",
            (
                "Xét thí nghiệm theo dõi hoạt động trao đổi nước và quang hợp ở cây xanh trồng "
                "ngoài tự nhiên."
            ),
            [
                (
                    "Cường độ quang hợp chỉ tăng đến điểm bão hòa ánh sáng nhất định.",
                    True,
                    "Đúng: Vượt quá điểm bão hòa ánh sáng, cường độ quang hợp không tăng thêm.",
                ),
                (
                    (
                        "Thực vật C4 thường có điểm bão hòa ánh sáng cao hơn và hiệu suất cố "
                        "định $CO_2$ cao trong điều kiện nóng nắng."
                    ),
                    True,
                    "Đúng: Ngô, mía thích nghi tốt với cường độ sáng mạnh và nhiệt độ cao.",
                ),
                (
                    "Rễ cây hấp thụ khoáng hoàn toàn không tiêu tốn năng lượng ATP.",
                    False,
                    "Sai: Quá trình hút khoáng chủ động ngược gradient nồng độ tiêu tốn ATP.",
                ),
                (
                    (
                        "Bón phân hợp lý kết hợp tưới tiêu chủ động giúp nâng cao năng suất "
                        "sinh học cây trồng."
                    ),
                    True,
                    (
                        "Đúng: Cung cấp đủ nguyên liệu tạo diệp lục, enzim và duy trì áp suất "
                        "thẩm thấu."
                    ),
                ),
            ],
        ),
    ]
    for qid, stem, stmts in tfs:
        questions.append(_tf(qid, stem, stmts))

    shorts = [
        (
            "P3-1",
            (
                "Một gen có tổng số 2.400 nuclêôtit và hiệu số giữa tỷ lệ phần trăm A với G là "
                "10%. Tính số nuclêôtit loại G của gen."
            ),
            "480",
            (
                "$A + G = 50\\%$, $A - G = 10\\% \\Rightarrow G = 20\\% \\Rightarrow N_G = 0,2 "
                "\\times 2400 = 480$."
            ),
        ),
        (
            "P3-2",
            (
                "Cho phép lai hai cá thể dị hợp 2 cặp gen nằm trên 2 cặp NST khác nhau ($AaBb "
                "\\times Aabb$). Tính số loại kiểu gen tối đa thu được ở đời con."
            ),
            "6",
            "Số kiểu gen = $3 (AA, Aa, aa) \\times 2 (Bb, bb) = 6$.",
        ),
        (
            "P3-3",
            (
                "Ở một loài thực vật, cơ thể có kiểu gen $\\frac{AB}{ab}$ xảy ra hoán vị gen "
                "với tần số 20%. Tính tỷ lệ phần trăm loại giao tử hoán vị $\\underline{Ab}$ "
                "tạo ra (viết số nguyên %)."
            ),
            "10",
            "Tỷ lệ mỗi loại giao tử hoán vị = $f / 2 = 20\\% / 2 = 10\\%$.",
        ),
        (
            "P3-4",
            (
                "Trong một hệ sinh thái, sinh vật sản xuất tích lũy $10.000\\text{ kcal}$, hiệu "
                "suất sinh thái chuyển từ bậc dinh dưỡng này sang bậc liền kề là 10%. Sinh vật "
                "tiêu thụ bậc 2 tích lũy bao nhiêu kcal?"
            ),
            "100",
            (
                "Tiêu thụ bậc 1: $10.000 \\times 10\\% = 1.000$ kcal; Tiêu thụ bậc 2: $1.000 "
                "\\times 10\\% = 100$ kcal."
            ),
        ),
        (
            "P3-5",
            (
                "Một phân tử mARN trưởng thành có 300 bộ ba mã hóa tính cả bộ ba mở đầu và kết "
                "thúc. Chuỗi pôlipeptit hoàn chỉnh do mARN đó tổng hợp (đã cắt bỏ axit amin mở "
                "đầu) gồm bao nhiêu axit amin?"
            ),
            "298",
            (
                "Có 299 bộ ba mã hóa axit amin (trừ kết thúc); cắt bỏ 1 axit amin mở đầu còn "
                "298 axit amin."
            ),
        ),
        (
            "P3-6",
            (
                "Ở một quần thể đạt cân bằng di truyền, tỷ lệ cá thể mang kiểu gen đồng hợp "
                "lặn $aa$ chiếm 16%. Tính tần số alen trội $A$ trong quần thể (dùng dấu phẩy)."
            ),
            "0,6",
            "$q^2 = 0,16 \\Rightarrow q(a) = 0,4 \\Rightarrow p(A) = 1 - 0,4 = 0,6$.",
        ),
    ]
    for qid, stem, ans, sol in shorts:
        questions.append(_short(qid, stem, ans, sol))

    return questions, [], []


_BUILDERS = {
    "thpt_literature_2026": _build_literature,
    "thpt_english_2026": _build_english,
    "thpt_history_2026": _build_history,
    "thpt_geography_2026": _build_geography,
    "thpt_chemistry_2026": _build_chemistry,
    "thpt_biology_2026": _build_biology,
}


def build_fallback_exam_data(profile: dict) -> tuple[list[dict], list[dict], list[str]]:
    """Build realistic contract-validated exam items, passages, and front_matter for a profile."""
    format_id = profile["formatId"]
    builder = _BUILDERS.get(format_id)
    if builder is None:
        raise ValueError(f"Unsupported contract formatId: {format_id}")
    questions, passages, front_matter = builder()
    errors = validate_contract_exam(profile, questions, passages)
    if errors:
        raise ValueError("Invalid contract fallback data: " + "; ".join(errors))
    return questions, passages, front_matter


async def run_thpt2026_fallback_job(
    profile: dict,
    output: Path,
    on_progress: Callable[[str, str | None, int], None] | None = None,
    *,
    prompt: str = "",
    fallback_reason: dict | None = None,
    font_profile: str = "unicode_times",
) -> dict:
    """Persist student TeX, answer book, and illustration manifest without calling AI APIs."""
    del prompt
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    if on_progress:
        on_progress("rag", profile["sections"][0]["id"], 1)
    await asyncio.sleep(0.01)

    questions, passages, front_matter = build_fallback_exam_data(profile)
    for sec in profile["sections"]:
        if on_progress:
            on_progress("composer", sec["id"], 1)
        await asyncio.sleep(0.01)

    if on_progress:
        on_progress("reviewer", None, 1)

    source = render_contract_exam_tex(
        profile,
        questions,
        passages,
        front_matter=front_matter,
        font_profile=font_profile,
    )
    (output / "de_thi.tex").write_bytes(source)
    (output / "dap_an_va_loi_giai.json").write_text(
        json.dumps(
            {
                "composer": questions,
                "passages": passages,
                "front_matter": front_matter,
                "independent_solver": {"entries": []},
            },
            ensure_ascii=False,
            indent=2,
        ),
        "utf-8",
    )
    revision_dir = output / "_internal" / "revision_1"
    revision_dir.mkdir(parents=True, exist_ok=True)
    (revision_dir / "illustrations.json").write_text('{"drawings": []}', "utf-8")
    return {
        "execution_status": "completed",
        "revision": 1,
        "demo_mode": True,
        "fallback": fallback_reason,
    }

"""M0 sample matrix: Hóa học (THPTQG, 18 MCQ + 4 TF + 6 short answer = 28 câu, 40 scoring units of 0,25 = 10 điểm, 50 phút).
ORIGINAL and abstract: topics = the Kết nối tri thức Hóa học 12 lesson list (+ two lớp 10-11 foundation units); requirements,
câu numbering, levels, situations are chosen here. Evidence read for shape only (see NOTE.md). Run with the app venv."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from m0lib import Spec

K = {1: "Chương 1: Ester – Lipid", 2: "Chương 2: Carbohydrate", 3: "Chương 3: Hợp chất chứa nitrogen", 4: "Chương 4: Polymer",
     5: "Chương 5: Pin điện và điện phân", 6: "Chương 6: Đại cương về kim loại", 7: "Chương 7: Nguyên tố nhóm IA và nhóm IIA",
     8: "Chương 8: Sơ lược về dãy kim loại chuyển tiếp thứ nhất và phức chất", 9: "Chương 9: Kiến thức nền lớp 10–11"}
T = {
 "b1": (K[1], "Bài 1: Ester – Lipid"), "b2": (K[1], "Bài 2: Xà phòng và chất giặt rửa"),
 "b4": (K[2], "Bài 4: Giới thiệu về carbohydrate. Glucose và fructose"), "b5": (K[2], "Bài 5: Saccharose và maltose"), "b6": (K[2], "Bài 6: Tinh bột và cellulose"),
 "b8": (K[3], "Bài 8: Amine"), "b9": (K[3], "Bài 9: Amino acid và peptide"), "b10": (K[3], "Bài 10: Protein và enzyme"),
 "b12": (K[4], "Bài 12: Đại cương về polymer"), "b13": (K[4], "Bài 13: Vật liệu polymer"),
 "b15": (K[5], "Bài 15: Thế điện cực và nguồn điện hoá học"), "b16": (K[5], "Bài 16: Điện phân"),
 "b19": (K[6], "Bài 19: Tính chất vật lí và tính chất hoá học của kim loại"), "b20": (K[6], "Bài 20: Kim loại trong tự nhiên và phương pháp tách kim loại"),
 "b21": (K[6], "Bài 21: Hợp kim"), "b22": (K[6], "Bài 22: Sự ăn mòn kim loại"),
 "b24": (K[7], "Bài 24: Nguyên tố nhóm IA"), "b25": (K[7], "Bài 25: Nguyên tố nhóm IIA"),
 "b28": (K[8], "Bài 28: Sơ lược về phức chất"), "b29": (K[8], "Bài 29: Một số tính chất và ứng dụng của phức chất"),
 "cb": (K[9], "Cân bằng hoá học (lớp 11)"), "en": (K[9], "Năng lượng hoá học: biến thiên enthalpy (lớp 10)"),
}

CELLS = [
 # P1: 18 câu, 0,25; 10 Biết / 6 Hiểu / 2 Vận dụng
 ("P1", 1, "b1", "NB", "Nhận biết tên gọi, công thức hoặc tính chất vật lí của một ester đơn giản", "khái niệm trực tiếp; bốn phương án là tên hoặc công thức", "NL.1"),
 ("P1", 2, "b2", "NB", "Nhận biết thành phần chính của xà phòng hoặc đặc điểm của chất giặt rửa tổng hợp", "khái niệm trực tiếp", "NL.1"),
 ("P1", 3, "b4", "NB", "Nhận biết đặc điểm cấu tạo hoặc một tính chất của glucose hay fructose", "khái niệm trực tiếp", "NL.1"),
 ("P1", 4, "b6", "NB", "Nhận biết thuốc thử hoặc hiện tượng đặc trưng của tinh bột hoặc cellulose", "khái niệm trực tiếp", "NL.1"),
 ("P1", 5, "b8", "NB", "Xác định bậc của amine hoặc gọi tên một amine theo công thức cho trước", "một công thức; bốn phương án là bậc hoặc tên", "NL.1"),
 ("P1", 6, "b9", "NB", "Nhận biết nhóm chức hoặc tính chất lưỡng tính của amino acid", "khái niệm trực tiếp", "NL.1"),
 ("P1", 7, "b12", "NB", "Nhận biết monomer hoặc loại phản ứng tạo ra một polymer cho trước", "một công thức hoặc tên polymer; bốn phương án là monomer hoặc phản ứng", "NL.1"),
 ("P1", 8, "b15", "NB", "Nhận biết cực âm, cực dương hoặc quá trình xảy ra tại điện cực của pin điện hoá cho trước", "mô tả một dòng; bốn phương án là phát biểu", "NL.1"),
 ("P1", 9, "b19", "NB", "Nhận biết tính chất hoá học chung của kim loại (tính khử) qua một phản ứng cho trước", "phản ứng một dòng; bốn phương án là phát biểu", "NL.1"),
 ("P1", 10, "b24", "NB", "Nhận biết tính chất hoặc ứng dụng của một hợp chất của kim loại nhóm IA", "khái niệm trực tiếp", "NL.1"),
 ("P1", 11, "b5", "TH", "Phân biệt saccharose, maltose và glucose bằng phản ứng hoặc thuốc thử thích hợp", "bốn phương án là thuốc thử hoặc hiện tượng", "NL.1"),
 ("P1", 12, "b10", "TH", "Giải thích sự biến tính của protein hoặc điều kiện hoạt động của enzyme từ một mô tả ngắn", "mô tả 2–3 dòng", "NL.1"),
 ("P1", 13, "b16", "TH", "Xác định sản phẩm tạo thành ở mỗi điện cực khi điện phân dung dịch một muối cho trước", "một dung dịch; bốn phương án là cặp sản phẩm", "NL.1"),
 ("P1", 14, "b22", "TH", "Phân biệt ăn mòn hoá học với ăn mòn điện hoá hoặc chỉ ra điều kiện xảy ra ăn mòn điện hoá", "mô tả 2–3 dòng", "NL.1"),
 ("P1", 15, "b28", "TH", "Xác định nguyên tử trung tâm, phối tử và số oxi hoá của nguyên tử trung tâm trong một phức chất cho trước", "một công thức phức chất; bốn phương án là đáp án tương ứng", "NL.1"),
 ("P1", 16, "cb", "TH", "Xác định chiều chuyển dịch cân bằng khi thay đổi nồng độ, áp suất hoặc nhiệt độ của một phản ứng thuận nghịch", "một phương trình kèm điều kiện thay đổi", "NL.1"),
 ("P1", 17, "b13", "VD", "Tính khối lượng monomer cần dùng để điều chế một lượng polymer cho trước với hiệu suất xác định", "tình huống 3 dòng; nhiều bước; bốn phương án là số kèm đơn vị", "NL.3"),
 ("P1", 18, "b22", "VD", "Tính khối lượng kim loại bị ăn mòn hoặc thời gian ăn mòn từ số liệu trong một tình huống đơn giản", "tình huống 3–4 dòng; nhiều bước", "NL.3"),
 # P2: 4 câu, 4 ý; 5 Biết / 5 Hiểu / 6 Vận dụng
 ("P2", (1, "a"), "b1", "NB", "Nhận biết dụng cụ, điều kiện hoặc sản phẩm của thí nghiệm điều chế ester", "", "NL.2"),
 ("P2", (1, "b"), "b2", "NB", "Nhận biết chất tạo thành khi xà phòng hoá chất béo", "", "NL.1"),
 ("P2", (1, "c"), "b1", "TH", "Giải thích vai trò của chất xúc tác hoặc cách nâng cao hiệu suất của phản ứng ester hoá", "", "NL.1"),
 ("P2", (1, "d"), "b2", "VD", "Tính khối lượng xà phòng hoặc muối thu được từ lượng chất béo cho trước với hiệu suất xác định", "", "NL.3"),
 ("P2", (2, "a"), "b9", "NB", "Nhận biết nhóm chức hoặc tên của amino acid được nêu trong tình huống", "", "NL.1"),
 ("P2", (2, "b"), "b9", "TH", "Xác định môi trường của dung dịch hoặc sản phẩm khi amino acid phản ứng với acid hoặc base", "", "NL.1"),
 ("P2", (2, "c"), "b10", "TH", "Giải thích hiện tượng quan sát được khi protein bị đun nóng hoặc gặp một số tác nhân", "", "NL.2"),
 ("P2", (2, "d"), "b9", "VD", "Tính khối lượng hoặc số mol chất tham gia khi thuỷ phân hoặc trung hoà một lượng peptide hay amino acid", "", "NL.3"),
 ("P2", (3, "a"), "b15", "NB", "Nhận biết cực âm, cực dương của pin điện hoá cho trước", "", "NL.1"),
 ("P2", (3, "b"), "b15", "TH", "Tính sức điện động chuẩn của pin từ bảng thế điện cực chuẩn", "", "NL.1"),
 ("P2", (3, "c"), "b16", "VD", "Tính khối lượng chất thoát ra ở điện cực khi điện phân với cường độ dòng điện và thời gian cho trước", "", "NL.3"),
 ("P2", (3, "d"), "b22", "VD", "Đánh giá một phương pháp bảo vệ kim loại khỏi ăn mòn điện hoá trong tình huống thực tiễn", "", "NL.3"),
 ("P2", (4, "a"), "b24", "NB", "Nhận biết ứng dụng hoặc phương pháp điều chế của một kim loại hay hợp chất nhóm IA, IIA", "", "NL.1"),
 ("P2", (4, "b"), "b25", "TH", "Giải thích hiện tượng hoặc ứng dụng liên quan đến nước cứng hoặc hợp chất của kim loại nhóm IIA", "", "NL.1"),
 ("P2", (4, "c"), "b25", "VD", "Tính lượng chất cần dùng để làm mềm nước cứng hoặc để thu được lượng sản phẩm xác định", "", "NL.3"),
 ("P2", (4, "d"), "b29", "VD", "Đánh giá tính chất hoặc ứng dụng của một phức chất trong tình huống thực tiễn", "", "NL.3"),
 # P3: 6 câu trả lời ngắn, 0,25; 0 Biết / 2 Hiểu / 4 Vận dụng
 ("P3", 1, "b4", "TH", "Tính phần trăm khối lượng một nguyên tố hoặc khối lượng chất trong một phản ứng của glucose", "một phản ứng; đáp số một số làm tròn theo yêu cầu", "NL.3"),
 ("P3", 2, "b12", "TH", "Tính hệ số trùng hợp hoặc số mắt xích của một polymer từ phân tử khối", "một dữ kiện; đáp số một số", "NL.3"),
 ("P3", 3, "b21", "VD", "Tính phần trăm khối lượng các kim loại trong một hợp kim từ dữ kiện phản ứng với dung dịch acid", "tình huống 3–4 dòng; nhiều bước", "NL.3"),
 ("P3", 4, "b16", "VD", "Tính thời gian hoặc điện lượng cần để điện phân thu được một lượng chất cho trước", "tình huống 3–4 dòng; nhiều bước", "NL.3"),
 ("P3", 5, "en", "VD", "Tính biến thiên enthalpy chuẩn của một phản ứng từ nhiệt tạo thành hoặc năng lượng liên kết", "bảng số liệu ngắn; nhiều bước", "NL.3"),
 ("P3", 6, "b20", "VD", "Tính khối lượng kim loại thu được hoặc khối lượng quặng cần dùng khi biết hàm lượng và hiệu suất", "tình huống 3–4 dòng; nhiều bước", "NL.3"),
]

STEMS = {
 ("P2", 1): "thí nghiệm điều chế ester hoặc xà phòng hoá chất béo: mô tả cách làm, hiện tượng, số liệu",
 ("P2", 2): "amino acid hoặc protein trong một thí nghiệm hoặc trong thực phẩm, kèm số liệu",
 ("P2", 3): "pin điện hoá hoặc bình điện phân kèm bảng thế điện cực chuẩn và số liệu dòng điện, thời gian",
 ("P2", 4): "kim loại nhóm IA hoặc IIA trong sản xuất hoặc đời sống (nước cứng, vật liệu), có thể kèm phức chất",
}

SPEC = {
 "subject": "HoaHoc", "exam_type": "THPTQG", "title": "HOÁ HỌC, LỚP 12",
 "intro": "Đề thi tốt nghiệp THPT: 18 câu nhiều lựa chọn (0,25 điểm/câu), 4 câu đúng/sai (4 ý/câu, trung bình 0,25 điểm/ý) và 6 câu trả lời ngắn (0,25 điểm/câu), tổng 10 điểm, 50 phút.",
 "topics": T, "parts": {"P1": {"type": "mcq", "unit": 0.25}, "P2": {"type": "true_false", "unit": 0.25}, "P3": {"type": "short_answer", "unit": 0.25}},
 "cells": CELLS, "stems": STEMS,
 "level_cues": {
  "NB": "nhận biết, nêu, gọi tên, chỉ ra tính chất hoặc ứng dụng; một khái niệm, một phản ứng hoặc một quy tắc trực tiếp",
  "TH": "giải thích hiện tượng, phân biệt chất bằng thuốc thử, xác định sản phẩm hoặc chiều phản ứng, tính toán ngắn trong hai đến ba bước",
  "VD": "tình huống hoặc thí nghiệm mới, kết hợp nhiều kiến thức, tính toán nhiều bước có hiệu suất hoặc hàm lượng, đánh giá phương án",
 },
 "competencies": {"NL.1": "Nhận thức hoá học", "NL.2": "Tìm hiểu thế giới tự nhiên dưới góc độ hoá học", "NL.3": "Vận dụng kiến thức, kĩ năng đã học"},
 "scoring": {"P1": "mỗi câu 0,25 điểm", "P2": "mỗi câu 1,0 điểm (4 ý); ý đúng 1: 0,1; 2: 0,25; 3: 0,5; 4: 1,0; trung bình 0,25 điểm mỗi ý",
             "P3": "mỗi câu 0,25 điểm", "total": 10.0, "duration_minutes": 50},
}

if __name__ == "__main__":
    Spec(SPEC).write(HERE)

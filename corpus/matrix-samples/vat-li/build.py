"""M0 sample matrix: Vật lí (THPTQG, 18 MCQ + 4 TF + 6 short answer = 28 câu, 40 scoring units of 0,25 = 10 điểm, 50 phút).
ORIGINAL and abstract: topics = the Kết nối tri thức Vật lí 12 lesson list; requirements, câu numbering, levels, situations are
chosen here. Evidence read for shape only (see NOTE.md). Run with the app venv; writes next to itself."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from m0lib import Spec

C1 = "Chương I: Vật lí nhiệt"; C2 = "Chương II: Khí lí tưởng"; C3 = "Chương III: Từ trường"; C4 = "Chương IV: Vật lí hạt nhân"
T = {
 "b1": (C1, "Bài 1: Cấu trúc của chất. Sự chuyển thể"),
 "b2": (C1, "Bài 2: Nội năng. Định luật I của nhiệt động lực học"),
 "b3": (C1, "Bài 3: Nhiệt độ. Thang nhiệt độ – nhiệt kế"),
 "b4": (C1, "Bài 4: Nhiệt dung riêng"),
 "b5": (C1, "Bài 5: Nhiệt nóng chảy riêng"),
 "b6": (C1, "Bài 6: Nhiệt hoá hơi riêng"),
 "b8": (C2, "Bài 8: Mô hình động học phân tử chất khí"),
 "b9": (C2, "Bài 9: Định luật Boyle"),
 "b10": (C2, "Bài 10: Định luật Charles"),
 "b11": (C2, "Bài 11: Phương trình trạng thái của khí lí tưởng"),
 "b12": (C2, "Bài 12: Áp suất khí theo mô hình động học phân tử"),
 "b14": (C3, "Bài 14: Từ trường"),
 "b15": (C3, "Bài 15: Lực từ tác dụng lên dây dẫn mang dòng điện. Cảm ứng từ"),
 "b16": (C3, "Bài 16: Từ thông. Hiện tượng cảm ứng điện từ"),
 "b17": (C3, "Bài 17: Máy phát điện xoay chiều"),
 "b18": (C3, "Bài 18: Ứng dụng hiện tượng cảm ứng điện từ"),
 "b19": (C3, "Bài 19: Điện từ trường. Mô hình sóng điện từ"),
 "b21": (C4, "Bài 21: Cấu trúc hạt nhân"),
 "b22": (C4, "Bài 22: Phản ứng hạt nhân và năng lượng liên kết"),
 "b23": (C4, "Bài 23: Hiện tượng phóng xạ"),
 "b24": (C4, "Bài 24: Công nghiệp hạt nhân"),
}

CELLS = [
 # P1: 18 câu, 0,25; 10 Biết / 5 Hiểu / 3 Vận dụng
 ("P1", 1, "b1", "NB", "Nhận biết thể (rắn, lỏng, khí) của một chất hoặc tên của quá trình chuyển thể từ một mô tả cho trước", "mô tả một dòng; bốn phương án là tên quá trình hoặc thể", "NL.1"),
 ("P1", 2, "b2", "NB", "Nhận biết nội năng của một vật phụ thuộc vào những đại lượng nào", "khái niệm trực tiếp", "NL.1"),
 ("P1", 3, "b3", "NB", "Đổi một nhiệt độ từ thang Celsius sang kelvin hoặc ngược lại bằng một phép cộng, trừ", "một giá trị; bốn phương án là số", "NL.1"),
 ("P1", 4, "b4", "NB", "Nhận biết ý nghĩa vật lí của nhiệt dung riêng của một chất", "khái niệm trực tiếp", "NL.1"),
 ("P1", 5, "b8", "NB", "Nhận biết một đặc điểm của chuyển động hoặc của tương tác giữa các phân tử khí theo mô hình động học phân tử", "khái niệm trực tiếp", "NL.1"),
 ("P1", 6, "b9", "NB", "Nhận biết phát biểu hoặc dạng đường biểu diễn của quá trình đẳng nhiệt trong hệ toạ độ cho trước", "đồ thị mô tả bằng lời; bốn phương án là phát biểu hoặc tên đường", "NL.1"),
 ("P1", 7, "b14", "NB", "Nhận biết tính chất của đường sức từ hoặc chiều của từ trường của nam châm hoặc dòng điện", "khái niệm trực tiếp", "NL.1"),
 ("P1", 8, "b15", "NB", "Nhận biết công thức độ lớn lực từ hoặc quy tắc xác định chiều lực từ", "khái niệm trực tiếp", "NL.1"),
 ("P1", 9, "b16", "NB", "Nhận biết điều kiện xuất hiện suất điện động cảm ứng trong một khung dây kín", "mô tả một dòng; bốn phương án là điều kiện", "NL.1"),
 ("P1", 10, "b21", "NB", "Xác định số proton, số neutron của một hạt nhân từ kí hiệu hạt nhân", "một kí hiệu; bốn phương án là số", "NL.1"),
 ("P1", 11, "b5", "TH", "Giải thích nhiệt độ của chất thay đổi hay không trong quá trình nóng chảy, dựa vào một mô tả hoặc bảng số liệu ngắn", "mô tả 2–3 dòng", "NL.1"),
 ("P1", 12, "b10", "TH", "Giải thích sự thay đổi của thể tích hoặc nhiệt độ của khối khí trong quá trình đẳng áp", "mô tả 2–3 dòng; có thể kèm đồ thị mô tả bằng lời", "NL.1"),
 ("P1", 13, "b17", "TH", "Giải thích nguyên tắc hoạt động của máy phát điện xoay chiều hoặc đọc đại lượng từ biểu thức suất điện động xoay chiều", "biểu thức một dòng", "NL.1"),
 ("P1", 14, "b22", "TH", "Hoàn thành một phương trình phản ứng hạt nhân bằng định luật bảo toàn số khối và điện tích", "một phương trình thiếu một hạt; bốn phương án là kí hiệu hạt", "NL.1"),
 ("P1", 15, "b23", "TH", "Giải thích ý nghĩa của chu kì bán rã qua một mô tả về lượng chất phóng xạ còn lại", "mô tả 2–3 dòng", "NL.1"),
 ("P1", 16, "b2", "VD", "Tính độ biến thiên nội năng của một hệ nhận công và truyền nhiệt, chú ý dấu của công và nhiệt lượng", "tình huống 3–4 dòng; bốn phương án là số kèm đơn vị", "NL.3"),
 ("P1", 17, "b11", "VD", "Tính thông số còn lại của một lượng khí khi cả ba thông số trạng thái cùng thay đổi", "tình huống 3–4 dòng; nhiều bước tính", "NL.3"),
 ("P1", 18, "b18", "VD", "Vận dụng công thức máy biến áp để tính điện áp hoặc cường độ dòng điện trong tình huống truyền tải đơn giản", "tình huống 3–4 dòng; nhiều bước tính", "NL.3"),
 # P2: 4 câu, 4 ý; 4 Biết / 6 Hiểu / 6 Vận dụng
 ("P2", (1, "a"), "b4", "NB", "Nhận biết công thức nhiệt lượng vật thu vào hoặc toả ra theo nhiệt dung riêng", "", "NL.1"),
 ("P2", (1, "b"), "b4", "NB", "Nhận biết đại lượng đo được và dụng cụ cần dùng trong phương án thí nghiệm", "", "NL.2"),
 ("P2", (1, "c"), "b5", "TH", "Nhận xét từ bảng số liệu về nhiệt lượng cần cho quá trình nóng chảy", "", "NL.2"),
 ("P2", (1, "d"), "b6", "VD", "Tính nhiệt lượng cần cung cấp để làm nóng rồi hoá hơi một lượng chất và nhận xét sai số so với giá trị đo", "", "NL.3"),
 ("P2", (2, "a"), "b8", "NB", "Nhận biết đại lượng đặc trưng cho trạng thái của khối khí trong xi-lanh", "", "NL.1"),
 ("P2", (2, "b"), "b9", "TH", "Xác định áp suất hoặc thể tích mới của khối khí trong quá trình đẳng nhiệt", "", "NL.1"),
 ("P2", (2, "c"), "b11", "VD", "Tính nhiệt độ hoặc thể tích của khối khí sau quá trình biến đổi trạng thái hai giai đoạn", "", "NL.3"),
 ("P2", (2, "d"), "b12", "VD", "Tính động năng tịnh tiến trung bình hoặc áp suất của khí từ số liệu của mô hình động học phân tử", "", "NL.3"),
 ("P2", (3, "a"), "b16", "NB", "Nhận biết từ thông qua khung dây trong từ trường đều", "", "NL.1"),
 ("P2", (3, "b"), "b16", "TH", "Tính độ lớn suất điện động cảm ứng từ độ biến thiên từ thông trong một khoảng thời gian", "", "NL.1"),
 ("P2", (3, "c"), "b15", "TH", "Xác định chiều của lực từ hoặc của dòng điện cảm ứng bằng quy tắc thích hợp", "", "NL.1"),
 ("P2", (3, "d"), "b16", "VD", "Tính nhiệt lượng toả ra hoặc công suất tiêu thụ trong khung dây khi có suất điện động cảm ứng", "", "NL.3"),
 ("P2", (4, "a"), "b23", "TH", "Phân biệt các loại tia phóng xạ hoặc đặc điểm của hiện tượng phóng xạ", "", "NL.1"),
 ("P2", (4, "b"), "b22", "TH", "Viết hoặc hoàn thành phương trình phản ứng hạt nhân theo các định luật bảo toàn", "", "NL.1"),
 ("P2", (4, "c"), "b23", "VD", "Tính độ phóng xạ hoặc số hạt nhân còn lại sau một khoảng thời gian cho trước", "", "NL.3"),
 ("P2", (4, "d"), "b22", "VD", "Tính năng lượng toả ra hoặc thu vào của phản ứng hạt nhân từ độ hụt khối", "", "NL.3"),
 # P3: 6 câu trả lời ngắn, 0,25; 0 Biết / 2 Hiểu / 4 Vận dụng
 ("P3", 1, "b3", "TH", "Đổi nhiệt độ giữa các thang nhiệt độ trong một tình huống đo và tìm độ chênh lệch", "tình huống 2–3 dòng; đáp số một số", "NL.3"),
 ("P3", 2, "b10", "TH", "Tính thể tích hoặc nhiệt độ cuối của khối khí trong quá trình đẳng áp", "tình huống 3 dòng; đáp số một số", "NL.3"),
 ("P3", 3, "b12", "VD", "Tính số phân tử hoặc áp suất của lượng khí từ khối lượng, thể tích và nhiệt độ cho trước", "tình huống 3–4 dòng; nhiều bước; làm tròn theo yêu cầu", "NL.3"),
 ("P3", 4, "b15", "VD", "Tính độ lớn lực từ hoặc cảm ứng từ trong một thí nghiệm có dòng điện chạy qua đoạn dây", "tình huống 3–4 dòng; nhiều bước", "NL.3"),
 ("P3", 5, "b19", "VD", "Tính bước sóng hoặc tần số của sóng điện từ trong một ứng dụng thông tin", "tình huống 3 dòng; nhiều bước", "NL.3"),
 ("P3", 6, "b23", "VD", "Tính thời gian hoặc khối lượng còn lại của một đồng vị phóng xạ", "tình huống 3–4 dòng; nhiều bước", "NL.3"),
]

STEMS = {
 ("P2", 1): "thí nghiệm đo nhiệt dung riêng hoặc nhiệt nóng chảy riêng: mô tả phương án, bảng số liệu, kết quả đo",
 ("P2", 2): "khối khí trong xi-lanh có pit-tông, hai trạng thái và một quá trình biến đổi",
 ("P2", 3): "khung dây hoặc thanh dẫn trong từ trường biến thiên hoặc có dòng điện, kèm số liệu",
 ("P2", 4): "đồng vị phóng xạ trong y tế hoặc định tuổi mẫu vật, kèm chu kì bán rã và số liệu",
}

SPEC = {
 "subject": "VatLy", "exam_type": "THPTQG", "title": "VẬT LÍ, LỚP 12",
 "intro": "Đề thi tốt nghiệp THPT: 18 câu nhiều lựa chọn (0,25 điểm/câu), 4 câu đúng/sai (4 ý/câu, trung bình 0,25 điểm/ý) và 6 câu trả lời ngắn (0,25 điểm/câu), tổng 10 điểm, 50 phút.",
 "topics": T, "parts": {"P1": {"type": "mcq", "unit": 0.25}, "P2": {"type": "true_false", "unit": 0.25}, "P3": {"type": "short_answer", "unit": 0.25}},
 "cells": CELLS, "stems": STEMS,
 "level_cues": {
  "NB": "nhận biết, nêu, chỉ ra một khái niệm, đơn vị, quy tắc hoặc công thức; thay một giá trị vào một công thức một bước",
  "TH": "giải thích hiện tượng, phân biệt hai khái niệm, đọc ý nghĩa từ đồ thị hoặc bảng số liệu, tính trong hai đến ba bước",
  "VD": "tình huống hoặc thí nghiệm mới, kết hợp nhiều công thức hoặc nhiều giai đoạn, nhiều bước tính, nhận xét kết quả",
 },
 "competencies": {"NL.1": "Nhận thức vật lí", "NL.2": "Tìm hiểu thế giới tự nhiên dưới góc độ vật lí", "NL.3": "Vận dụng kiến thức, kĩ năng đã học"},
 "scoring": {"P1": "mỗi câu 0,25 điểm", "P2": "mỗi câu 1,0 điểm (4 ý); ý đúng 1: 0,1; 2: 0,25; 3: 0,5; 4: 1,0; trung bình 0,25 điểm mỗi ý",
             "P3": "mỗi câu 0,25 điểm", "total": 10.0, "duration_minutes": 50},
}

if __name__ == "__main__":
    Spec(SPEC).write(HERE)

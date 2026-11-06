"""M0 sample matrix: Toán (THPTQG, 12 MCQ + 4 TF + 6 short answer = 22 câu, 34 scoring units, 10 điểm, 90 phút).
ORIGINAL and abstract: topics = the Kết nối tri thức lớp 12 lesson list (+ two lớp 10-11 foundation units); requirements, câu
numbering, levels and situations chosen here. Shape of the tables follows a school matrix+spec form (internal evidence only).
Run with the app venv from anywhere; writes next to itself."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from m0lib import Spec

T = {
 "b1": ("Chủ đề 1: Ứng dụng đạo hàm để khảo sát và vẽ đồ thị hàm số", "Bài 1: Tính đơn điệu và cực trị của hàm số"),
 "b2": ("Chủ đề 1: Ứng dụng đạo hàm để khảo sát và vẽ đồ thị hàm số", "Bài 2: Giá trị lớn nhất và giá trị nhỏ nhất của hàm số"),
 "b3": ("Chủ đề 1: Ứng dụng đạo hàm để khảo sát và vẽ đồ thị hàm số", "Bài 3: Đường tiệm cận của đồ thị hàm số"),
 "b4": ("Chủ đề 1: Ứng dụng đạo hàm để khảo sát và vẽ đồ thị hàm số", "Bài 4: Khảo sát sự biến thiên và vẽ đồ thị của hàm số"),
 "b5": ("Chủ đề 1: Ứng dụng đạo hàm để khảo sát và vẽ đồ thị hàm số", "Bài 5: Ứng dụng đạo hàm để giải quyết một số vấn đề liên quan đến thực tiễn"),
 "b6": ("Chủ đề 2: Vectơ và hệ trục tọa độ trong không gian", "Bài 6: Vectơ trong không gian"),
 "b7": ("Chủ đề 2: Vectơ và hệ trục tọa độ trong không gian", "Bài 7: Hệ trục tọa độ trong không gian"),
 "b8": ("Chủ đề 2: Vectơ và hệ trục tọa độ trong không gian", "Bài 8: Biểu thức tọa độ của các phép toán vectơ"),
 "b9": ("Chủ đề 3: Các số đặc trưng đo mức độ phân tán của mẫu số liệu ghép nhóm", "Bài 9: Khoảng biến thiên và khoảng tứ phân vị"),
 "b10": ("Chủ đề 3: Các số đặc trưng đo mức độ phân tán của mẫu số liệu ghép nhóm", "Bài 10: Phương sai và độ lệch chuẩn"),
 "b11": ("Chủ đề 4: Nguyên hàm và tích phân", "Bài 11: Nguyên hàm"),
 "b12": ("Chủ đề 4: Nguyên hàm và tích phân", "Bài 12: Tích phân"),
 "b13": ("Chủ đề 4: Nguyên hàm và tích phân", "Bài 13: Ứng dụng hình học của tích phân"),
 "b14": ("Chủ đề 5: Phương pháp tọa độ trong không gian", "Bài 14: Phương trình mặt phẳng"),
 "b15": ("Chủ đề 5: Phương pháp tọa độ trong không gian", "Bài 15: Phương trình đường thẳng trong không gian"),
 "b16": ("Chủ đề 5: Phương pháp tọa độ trong không gian", "Bài 16: Công thức tính góc trong không gian"),
 "b17": ("Chủ đề 5: Phương pháp tọa độ trong không gian", "Bài 17: Phương trình mặt cầu"),
 "b18": ("Chủ đề 6: Xác suất có điều kiện", "Bài 18: Xác suất có điều kiện"),
 "b19": ("Chủ đề 6: Xác suất có điều kiện", "Bài 19: Công thức xác suất toàn phần và công thức Bayes"),
 "cs": ("Chủ đề 7: Kiến thức nền lớp 10–11", "Cấp số cộng và cấp số nhân (lớp 11)"),
 "th": ("Chủ đề 7: Kiến thức nền lớp 10–11", "Tổ hợp và xác suất cổ điển (lớp 10–11)"),
}

CELLS = [
 # P1: 12 câu nhiều lựa chọn, 0,25 điểm; 8 Biết / 3 Hiểu / 1 Vận dụng
 ("P1", 1, "b1", "NB", "Đọc bảng biến thiên cho sẵn để chỉ ra khoảng đồng biến, khoảng nghịch biến hoặc điểm cực trị của hàm số", "bảng biến thiên 3–4 cột; bốn phương án là khoảng hoặc giá trị", "TD"),
 ("P1", 2, "b3", "NB", "Nhận biết đường tiệm cận đứng hoặc tiệm cận ngang của đồ thị hàm phân thức cho bởi công thức", "công thức một dòng; bốn phương án là phương trình đường thẳng", "TD"),
 ("P1", 3, "b6", "NB", "Nhận biết kết quả phép cộng, phép trừ hai vectơ trong hình hộp hoặc hình chóp cho trước", "hình mô tả bằng lời kèm kí hiệu; bốn phương án là đẳng thức vectơ", "TD"),
 ("P1", 4, "b15", "NB", "Chỉ ra vectơ chỉ phương hoặc một điểm thuộc đường thẳng từ phương trình tham số hay chính tắc", "một phương trình; bốn phương án là vectơ hoặc điểm", "TD"),
 ("P1", 5, "b11", "NB", "Nhận biết nguyên hàm của một hàm số sơ cấp bằng bảng nguyên hàm", "một hàm số; bốn phương án là biểu thức", "TD"),
 ("P1", 6, "b12", "NB", "Nhận biết giá trị hoặc một tính chất của tích phân của hàm số đơn giản trên một đoạn", "một tích phân; bốn phương án là số", "TD"),
 ("P1", 7, "b9", "NB", "Tính khoảng biến thiên hoặc nhận biết nhóm chứa tứ phân vị từ bảng tần số ghép nhóm có sẵn", "bảng tần số 5–6 nhóm; bốn phương án là số", "TD"),
 ("P1", 8, "cs", "NB", "Tính số hạng thứ n của một cấp số cộng khi biết số hạng đầu và công sai", "một phép thay số; bốn phương án là số", "TD"),
 ("P1", 9, "b2", "TH", "Tìm giá trị lớn nhất hoặc nhỏ nhất của hàm đa thức bậc ba trên một đoạn cho trước", "công thức hàm số và đoạn; làm theo quy trình đã học, 2–3 bước", "GQ"),
 ("P1", 10, "b14", "TH", "Lập phương trình mặt phẳng đi qua một điểm khi biết vectơ pháp tuyến hoặc hai vectơ chỉ phương", "toạ độ cho sẵn; bốn phương án là phương trình mặt phẳng", "GQ"),
 ("P1", 11, "b13", "TH", "Tính diện tích hình phẳng giới hạn bởi hai đường, trong đó có đồ thị của một hàm số cho bằng công thức", "hai công thức; bốn phương án là số", "GQ"),
 ("P1", 12, "b16", "VD", "Tính góc giữa hai mặt phẳng hoặc giữa đường thẳng và mặt phẳng trong một mô hình hình học đã gắn toạ độ", "mô hình 3–4 dòng kèm toạ độ; cần lập vectơ rồi dùng công thức góc", "GQ"),
 # P2: 4 câu đúng/sai; mỗi câu 4 ý; 4 Biết / 7 Hiểu / 5 Vận dụng
 ("P2", (1, "a"), "b1", "NB", "Nhận biết điểm cực trị hoặc khoảng đơn điệu của hàm số từ công thức đạo hàm hay bảng biến thiên đi kèm", "", "TD"),
 ("P2", (1, "b"), "b1", "TH", "Xét dấu đạo hàm để kết luận về tính đơn điệu trên một khoảng", "", "TD"),
 ("P2", (1, "c"), "b2", "TH", "Tìm giá trị lớn nhất hoặc nhỏ nhất của hàm số trên một đoạn và so sánh với một giá trị cho trước", "", "GQ"),
 ("P2", (1, "d"), "b4", "VD", "Biện luận số nghiệm của phương trình dựa vào đồ thị hoặc bảng biến thiên của hàm số", "", "GQ"),
 ("P2", (2, "a"), "b11", "NB", "Nhận biết quãng đường là một nguyên hàm của vận tốc theo thời gian", "", "TD"),
 ("P2", (2, "b"), "b11", "TH", "Tìm hàm quãng đường từ hàm vận tốc và điều kiện ban đầu", "", "TD"),
 ("P2", (2, "c"), "b12", "VD", "Tính quãng đường vật đi được trong một khoảng thời gian bằng tích phân", "", "MHH"),
 ("P2", (2, "d"), "b12", "VD", "Xác định thời điểm hoặc so sánh hai quãng đường dựa trên kết quả tính tích phân", "", "GQ"),
 ("P2", (3, "a"), "b7", "NB", "Nhận biết toạ độ của điểm hoặc của vectơ trong mô hình đã đặt hệ trục Oxyz", "", "TD"),
 ("P2", (3, "b"), "b14", "TH", "Lập hoặc kiểm tra phương trình mặt phẳng chứa ba điểm cho trước", "", "GQ"),
 ("P2", (3, "c"), "b15", "TH", "Xác định giao điểm của một đường thẳng với mặt phẳng trong mô hình", "", "GQ"),
 ("P2", (3, "d"), "b17", "VD", "Kiểm tra một điểm có nằm trong vùng giới hạn bởi mặt cầu hay không và kết luận cho tình huống", "", "MHH"),
 ("P2", (4, "a"), "b18", "NB", "Nhận biết xác suất của một biến cố từ số liệu phần trăm cho trong tình huống", "", "TD"),
 ("P2", (4, "b"), "b18", "TH", "Tính xác suất có điều kiện của một biến cố khi biết biến cố kia đã xảy ra", "", "GQ"),
 ("P2", (4, "c"), "b19", "TH", "Dùng công thức xác suất toàn phần để tính xác suất của một biến cố qua hai nhóm", "", "GQ"),
 ("P2", (4, "d"), "b19", "VD", "Dùng công thức Bayes để tính xác suất nguồn gốc của một kết quả và đánh giá một nhận định", "", "GQ"),
 # P3: 6 câu trả lời ngắn, 0,5 điểm; 0 Biết / 2 Hiểu / 4 Vận dụng
 ("P3", 1, "b5", "TH", "Lập hàm một biến cho bài toán tối ưu thực tiễn (chi phí, diện tích hoặc thể tích) rồi tìm giá trị lớn nhất hoặc nhỏ nhất", "tình huống 3–4 dòng; đáp số một số làm tròn theo yêu cầu", "MHH"),
 ("P3", 2, "b12", "TH", "Tính giá trị tích phân của hàm số cho bởi công thức bằng bảng nguyên hàm và tính chất của tích phân", "một tích phân hai bước; đáp số một số", "TD"),
 ("P3", 3, "b17", "VD", "Vận dụng toạ độ để tính khoảng cách hoặc toạ độ giao điểm trong một tình huống thực tiễn có mô hình mặt cầu hoặc mặt phẳng", "tình huống 4–6 dòng kèm toạ độ; nhiều bước", "MHH"),
 ("P3", 4, "b10", "VD", "So sánh độ phân tán của hai mẫu số liệu ghép nhóm bằng phương sai hoặc độ lệch chuẩn và trả lời bằng một số", "hai bảng tần số; tính toán nhiều bước", "GQ"),
 ("P3", 5, "th", "VD", "Giải một bài toán đếm và xác suất cổ điển có điều kiện về sắp xếp hoặc chọn nhóm", "tình huống 3–4 dòng; đáp số là số nguyên hoặc số thập phân", "GQ"),
 ("P3", 6, "b13", "VD", "Tính thể tích hoặc diện tích của vật thể tạo bởi một miền phẳng trong mô hình thực tiễn bằng tích phân", "tình huống kèm hàm số; nhiều bước", "MHH"),
]

STEMS = {
 ("P2", 1): "hàm số đa thức bậc ba cho bởi công thức, có thể kèm bảng biến thiên",
 ("P2", 2): "chuyển động của một vật: vận tốc cho bởi hàm số theo thời gian, quãng đường tính bằng tích phân",
 ("P2", 3): "mô hình trong không gian Oxyz: mặt phẳng là mặt sàn, đường thẳng là hướng một tia sáng hoặc đường ống, điểm là vị trí thiết bị, mặt cầu là vùng phủ sóng",
 ("P2", 4): "chọn ngẫu nhiên hai giai đoạn (hai nhóm sản phẩm hoặc hai loại khách hàng) có thông tin phần trăm",
}

SPEC = {
 "subject": "Toan", "exam_type": "THPTQG", "title": "TOÁN, LỚP 12",
 "intro": "Đề thi tốt nghiệp THPT: 12 câu nhiều lựa chọn (0,25 điểm/câu), 4 câu đúng/sai (4 ý/câu, trung bình 0,25 điểm/ý) và 6 câu trả lời ngắn (0,5 điểm/câu), tổng 10 điểm, 90 phút.",
 "topics": T, "parts": {"P1": {"type": "mcq", "unit": 0.25}, "P2": {"type": "true_false", "unit": 0.25}, "P3": {"type": "short_answer", "unit": 0.5}},
 "cells": CELLS, "stems": STEMS,
 "level_cues": {
  "NB": "nhận biết, nêu, đọc từ bảng hoặc đồ thị cho sẵn, áp dụng một công thức hoặc một quy tắc một bước",
  "TH": "tính theo quy trình đã học trong hai đến ba bước, giải thích hoặc so sánh kết quả, đọc ý nghĩa của số liệu",
  "VD": "lập mô hình hoặc hàm số từ tình huống mới, kết hợp nhiều kiến thức, nhiều bước tính, kết luận và nêu lí do",
 },
 "competencies": {"TD": "Tư duy và lập luận toán học", "GQ": "Giải quyết vấn đề toán học", "MHH": "Mô hình hoá toán học"},
 "scoring": {"P1": "mỗi câu 0,25 điểm", "P2": "mỗi câu 1,0 điểm (4 ý); ý đúng 1: 0,1; 2: 0,25; 3: 0,5; 4: 1,0; trung bình 0,25 điểm mỗi ý",
             "P3": "mỗi câu 0,5 điểm", "total": 10.0, "duration_minutes": 90},
}

if __name__ == "__main__":
    Spec(SPEC).write(HERE)

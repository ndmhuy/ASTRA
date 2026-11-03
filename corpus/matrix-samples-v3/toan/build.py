# -*- coding: utf-8 -*-
"""Build the 'real matrix' sample for Toán 12 (THPTQG): one block per question slot, no compact codes."""
import collections, pathlib, sys

OUT = pathlib.Path(sys.argv[1])

NL = {
    "TD": "Tư duy và lập luận toán học",
    "GQ": "Giải quyết vấn đề toán học",
    "MH": "Mô hình hóa toán học",
    "CC": "Sử dụng công cụ, phương tiện học toán",
}
LV = {"B": "Biết", "H": "Hiểu", "V": "Vận dụng"}
KIND = {"P1": "Nhiều lựa chọn", "P2": "Đúng/sai", "P3": "Trả lời ngắn"}

K12 = "lớp 12"
K11 = "lớp 11"
K10 = "lớp 10"

# (part, câu, ý, level, chủ đề, bài, lớp, mục tiêu đánh giá, dạng câu hỏi / dữ kiện, năng lực, tần suất)
S = []
def add(*a): S.append(a)

# ---------------- Phần I: 12 câu nhiều lựa chọn, 0,25 điểm/câu ----------------
add("P1", 1, None, "B", "Vectơ và hệ trục tọa độ trong không gian", "Bài 6. Vectơ trong không gian", K12,
    "Áp dụng quy tắc ba điểm hoặc quy tắc hình bình hành để cộng, trừ hai vectơ trên một hình hộp hoặc hình lăng trụ cho sẵn, rồi chọn đẳng thức vectơ đúng.",
    "Một hình hộp hoặc hình lăng trụ có hình vẽ; bốn phương án là bốn đẳng thức vectơ. Không có số liệu.", "TD", "5/7 đề")
add("P1", 2, None, "B", "Quan hệ song song và vuông góc trong không gian", "Quan hệ song song trong không gian (kiến thức nền)", K11,
    "Nhận biết một đường thẳng song song với mặt phẳng nào trong hình hộp hoặc tứ diện, hoặc hai mặt phẳng nào song song.",
    "Hình hộp hoặc tứ diện có hình vẽ, bốn phương án là bốn mặt phẳng hoặc bốn đường thẳng đặt tên bằng đỉnh. Không có số liệu.", "TD", "3/7 đề")
add("P1", 3, None, "B", "Phương pháp tọa độ trong không gian", "Bài 15. Phương trình đường thẳng trong không gian", K12,
    "Đọc phương trình chính tắc hoặc tham số của một đường thẳng và chỉ ra một vectơ chỉ phương, hoặc một điểm thuộc đường thẳng.",
    "Phương trình đường thẳng cho sẵn bằng công thức; bốn phương án là bốn bộ ba số. Chỉ cần đọc hệ số, không tính toán.", "TD", "6/7 đề")
add("P1", 4, None, "B", "Nguyên hàm và tích phân", "Bài 11. Nguyên hàm", K12,
    "Nêu họ nguyên hàm của một hàm cơ bản (lũy thừa của x hoặc hàm mũ a^x) bằng bảng nguyên hàm, một bước.",
    "Một hàm số cho bằng công thức; bốn phương án là bốn biểu thức có hằng số C, trong đó có các phương án sai quen thuộc (quên chia hệ số, sai số mũ).", "TD", "4/7 đề, 2 đề khác có câu liên quan")
add("P1", 5, None, "H", "Các số đặc trưng đo mức độ phân tán của mẫu số liệu ghép nhóm", "Bài 9. Khoảng biến thiên và khoảng tứ phân vị", K12,
    "Tính tứ phân vị thứ nhất hoặc thứ ba, hoặc khoảng tứ phân vị, từ một bảng tần số ghép nhóm bằng công thức đã học.",
    "Bảng tần số ghép nhóm 5 đến 6 nhóm, số liệu một tình huống đời sống (thời lượng cuộc gọi, điểm số, cân nặng). Đáp số là một số, làm tròn nếu cần.", "GQ", "6/7 đề")
add("P1", 6, None, "H", "Dãy số, cấp số cộng và cấp số nhân", "Cấp số cộng và cấp số nhân (kiến thức nền)", K11,
    "Tìm công sai, công bội hoặc một số hạng của cấp số cộng hoặc cấp số nhân từ hai dữ kiện cho trước.",
    "Cho hai số hạng hoặc số hạng đầu cùng công sai; hỏi một đại lượng còn lại. Tính trong hai đến ba bước.", "GQ", "6/7 đề")
add("P1", 7, None, "B", "Ứng dụng đạo hàm để khảo sát và vẽ đồ thị hàm số", "Bài 3. Đường tiệm cận của đồ thị hàm số", K12,
    "Nhận ra tiệm cận đứng hoặc tiệm cận ngang của đồ thị hàm phân thức từ đồ thị cho sẵn hoặc từ công thức.",
    "Đồ thị hàm y = (ax+b)/(cx+d) có đường tiệm cận vẽ nét đứt, hoặc công thức hàm số; bốn phương án là bốn đường thẳng.", "TD", "3/7 đề")
add("P1", 8, None, "H", "Nguyên hàm và tích phân", "Bài 13. Ứng dụng hình học của tích phân", K12,
    "Tính diện tích hình phẳng giới hạn bởi đồ thị một hàm số đơn giản, trục hoành và hai đường thẳng đứng, hoặc thể tích khối tròn xoay, bằng tích phân.",
    "Hàm số bậc nhất hoặc bậc hai cho bằng công thức, cận cho sẵn; đáp số là một số nguyên hoặc phân số.", "GQ", "4/7 đề")
add("P1", 9, None, "H", "Phương pháp tọa độ trong không gian", "Bài 14. Phương trình mặt phẳng", K12,
    "Lập phương trình mặt phẳng đi qua một điểm và có vectơ pháp tuyến cho trước, hoặc chỉ ra vectơ pháp tuyến của mặt phẳng cho bằng phương trình.",
    "Điểm và vectơ cho bằng tọa độ; bốn phương án là bốn phương trình dạng ax+by+cz+d=0 có hệ số d khác nhau.", "GQ", "5/7 đề")
add("P1", 10, None, "H", "Hàm số mũ và hàm số lôgarit", "Phương trình, bất phương trình mũ và lôgarit (kiến thức nền)", K11,
    "Giải phương trình hoặc bất phương trình mũ hoặc lôgarit cơ bản, kết luận nghiệm hoặc tập nghiệm.",
    "Phương trình dạng log_a(f(x)) = m hoặc a^x < b; bốn phương án là bốn nghiệm hoặc bốn tập nghiệm, có phương án quên điều kiện xác định.", "GQ", "7/7 đề")
add("P1", 11, None, "B", "Hàm số lượng giác và phương trình lượng giác", "Phương trình lượng giác cơ bản (kiến thức nền)", K11,
    "Nhận ra tập nghiệm của phương trình sin x = m hoặc cos x = m với m là giá trị đặc biệt (0, 1, -1), viết theo k thuộc tập số nguyên.",
    "Một phương trình lượng giác cơ bản; bốn phương án là bốn tập nghiệm khác nhau ở phần cộng k2π hoặc kπ.", "GQ", "5/7 đề")
add("P1", 12, None, "V", "Hình học không gian", "Khối chóp và khối lăng trụ (kiến thức nền)", K11,
    "Tính thể tích khối chóp hoặc khối lăng trụ mà chiều cao hoặc diện tích đáy phải tự tìm từ góc hoặc quan hệ vuông góc cho trước, rồi tính tiếp.",
    "Hình chóp hoặc lăng trụ cho bằng lời, có một góc hoặc một quan hệ vuông góc; phải tự dựng hoặc tính chiều cao; đáp số là một số.", "GQ", "4/7 đề, 6/7 đề nếu tính cả khối đa diện nói chung")

# ---------------- Phần II: 4 câu đúng/sai, mỗi câu 4 ý ----------------
def tf(no, topic, grade, situation, items):
    """Phần II: the câu belongs to one chủ đề (one chapter of the test scope); no bài is attached, only the ý."""
    for sub, lvl, obj, style, nl in items:
        add("P2", no, sub, lvl, topic, None, grade, obj, style + "  Tình huống chung của câu: " + situation, nl, None)

def tag(n, text):
    for i in range(-n, 0): S[i] = S[i][:10] + (text,)

tf(1, "Ứng dụng đạo hàm để khảo sát và vẽ đồ thị hàm số", K12,
   "một hàm số bậc ba hoặc hàm phân thức cho bằng công thức, có thể gắn với một đại lượng thực tế (lợi nhuận, chi phí) theo biến x.",
   [("a", "B", "Tính đạo hàm của hàm số hoặc giá trị của hàm số tại một điểm cho trước, một bước.", "Phát biểu về giá trị cụ thể, đúng hoặc sai theo phép tính.", "GQ"),
    ("b", "H", "Xét dấu đạo hàm để kết luận khoảng đồng biến hoặc nghịch biến.", "Phát biểu về khoảng đơn điệu.", "TD"),
    ("c", "H", "Tìm giá trị lớn nhất hoặc nhỏ nhất của hàm số trên một đoạn cho trước.", "Phát biểu về giá trị lớn nhất hoặc nhỏ nhất.", "GQ"),
    ("d", "V", "Dùng bảng biến thiên hoặc đồ thị để biện luận số nghiệm của f(x) = m, hoặc so sánh giá trị lớn nhất của tình huống với một ngưỡng rồi kết luận.", "Phát biểu kết luận có kèm lí do bằng số.", "MH")])
tag(4, "6/7 đề")
tf(2, "Nguyên hàm và tích phân", K12,
   "một vật chuyển động với gia tốc hoặc vận tốc cho bằng công thức theo thời gian t, hoặc một miền phẳng bị chặn bởi hai đường cong cho bằng công thức.",
   [("a", "B", "Tính giá trị của hàm vận tốc hoặc hàm quãng đường tại một thời điểm cho trước, hoặc nhận ra nguyên hàm của một hàm đơn giản.", "Phát biểu về một giá trị cụ thể.", "GQ"),
    ("b", "H", "Thiết lập tích phân biểu diễn quãng đường hoặc diện tích (xác định đúng cận và hàm dưới dấu tích phân).", "Phát biểu về biểu thức tích phân.", "TD"),
    ("c", "H", "Tính quãng đường hoặc diện tích bằng tích phân.", "Phát biểu về một số cụ thể.", "GQ"),
    ("d", "V", "Giải yêu cầu ngược hoặc so sánh: tìm thời điểm hoặc tham số để quãng đường hoặc diện tích đạt một giá trị cho trước, và kết luận.", "Phát biểu về thời điểm hoặc tham số, có lí do.", "MH")])
tag(4, "5/7 đề")
tf(3, "Phương pháp tọa độ trong không gian", K12,
   "một vật chuyển động hoặc một công trình đặt trong hệ trục Oxyz (máy bay, đường đi, đài quan sát), đơn vị trên trục cho sẵn.",
   [("a", "B", "Đọc tọa độ điểm hoặc vectơ trực tiếp từ dữ kiện của tình huống.", "Phát biểu về tọa độ cụ thể.", "GQ"),
    ("b", "H", "Viết hoặc nhận ra phương trình đường thẳng (đường đi) hoặc mặt phẳng từ dữ kiện.", "Phát biểu về phương trình.", "TD"),
    ("c", "V", "Tính khoảng cách hoặc độ dài đoạn thẳng trong tình huống rồi so sánh với giới hạn an toàn cho trước.", "Phát biểu kết luận có kèm số liệu.", "MH"),
    ("d", "V", "Xác định vị trí hai đối tượng (cắt nhau, chéo nhau, một điểm có nằm trong mặt cầu hay không) và nêu kết luận.", "Phát biểu về vị trí tương đối.", "TD")])
tag(4, "6/7 đề")
tf(4, "Xác suất có điều kiện", K12,
   "một xét nghiệm hoặc một dây chuyền sản xuất có hai bước, cho tỉ lệ phần trăm của từng bước (độ chính xác của xét nghiệm, tỉ lệ mắc bệnh trong cộng đồng).",
   [("a", "B", "Đọc từ đề bài một xác suất có điều kiện hoặc xác suất của một biến cố đơn.", "Phát biểu về giá trị xác suất cho sẵn.", "GQ"),
    ("b", "H", "Tính xác suất của giao hai biến cố bằng công thức nhân.", "Phát biểu về một số thập phân.", "GQ"),
    ("c", "H", "Tính xác suất toàn phần của một biến cố.", "Phát biểu về một số thập phân.", "GQ"),
    ("d", "V", "Dùng công thức Bayes để tính xác suất một người thật sự mắc bệnh khi xét nghiệm dương tính, rồi nhận xét ý nghĩa của kết quả.", "Phát biểu về kết quả và kết luận kèm lí do.", "MH")])
tag(4, "7/7 đề")

# ---------------- Phần III: 6 câu trả lời ngắn, 0,5 điểm/câu, tất cả Vận dụng ----------------
add("P3", 1, None, "V", "Ứng dụng đạo hàm để khảo sát và vẽ đồ thị hàm số", "Bài 2 và Bài 5. Giá trị lớn nhất, nhỏ nhất và ứng dụng thực tiễn", K12,
    "Lập hàm số một biến từ tình huống sản xuất hoặc kinh doanh (doanh thu, lợi nhuận, chi phí), tìm giá trị lớn nhất trên một đoạn và đọc kết quả đúng đơn vị.",
    "Tình huống một doanh nghiệp có công thức theo số sản phẩm x trong một khoảng cho trước; đáp số là một số nguyên hoặc làm tròn đến hàng phần mười.", "MH", "5/7 đề")
add("P3", 2, None, "V", "Hình học không gian", "Khoảng cách và góc trong không gian (kiến thức nền)", K11,
    "Tính khoảng cách từ một điểm đến mặt phẳng hoặc giữa hai đường thẳng chéo nhau, hoặc góc giữa hai mặt phẳng, trong một khối chóp hoặc lăng trụ có số đo cho trước.",
    "Hình chóp hoặc lăng trụ cho bằng lời, có hình vẽ; phải dựng thêm đoạn vuông góc; đáp số làm tròn đến hàng phần mười.", "TD", "6/7 đề")
add("P3", 3, None, "H", "Tổ hợp và xác suất cổ điển", "Quy tắc đếm, hoán vị, chỉnh hợp, tổ hợp (kiến thức nền)", K11,
    "Đếm số cách sắp xếp hoặc chọn thỏa một điều kiện ràng buộc đơn giản bằng quy tắc nhân, hoán vị hoặc tổ hợp.",
    "Một tình huống xếp chỗ hoặc chọn nhóm có một điều kiện ràng buộc; đáp số là một số nguyên.", "GQ", "5/7 đề")
add("P3", 4, None, "H", "Hệ bất phương trình bậc nhất hai ẩn", "Bất phương trình bậc nhất hai ẩn và quy hoạch tuyến tính (kiến thức nền)", K10,
    "Từ miền nghiệm đã cho (hoặc hệ bất phương trình đã lập sẵn), tìm giá trị lớn nhất hoặc nhỏ nhất của biểu thức mục tiêu tại các đỉnh.",
    "Một cơ sở sản xuất hai loại sản phẩm; miền nghiệm cho sẵn dưới dạng hệ bất phương trình; đáp số là một số nguyên.", "MH", "3/7 đề")
add("P3", 5, None, "V", "Nguyên hàm và tích phân", "Bài 13. Ứng dụng hình học của tích phân", K12,
    "Tính thể tích một vật thể hoặc một khối tròn xoay mô tả bằng đồ vật thật (bình, chân đế, vật trang trí) bằng tích phân, kèm đổi đơn vị.",
    "Hình phẳng cho bằng công thức hàm số quay quanh trục, hoặc diện tích thiết diện cho theo x; đáp số làm tròn.", "MH", "3/7 đề")
add("P3", 6, None, "V", "Phương pháp tọa độ trong không gian", "Bài 7, Bài 14 và Bài 17. Tọa độ, mặt phẳng và mặt cầu", K12,
    "Đặt hệ trục tọa độ vào một tình huống thực tế (Trái Đất, căn phòng, công trình), lập phương trình mặt cầu hoặc mặt phẳng và tính một khoảng cách hay một tham số.",
    "Tình huống có đơn vị đo; phải chọn gốc tọa độ hợp lí; đáp số làm tròn đến hàng phần mười.", "MH", "3/7 đề")

# ---------------- checks ----------------
cnt = collections.Counter((s[0], s[3]) for s in S)
assert cnt[("P1", "B")] == 6 and cnt[("P1", "H")] == 5 and cnt[("P1", "V")] == 1, cnt
assert cnt[("P2", "B")] == 4 and cnt[("P2", "H")] == 7 and cnt[("P2", "V")] == 5, cnt
assert cnt[("P3", "V")] == 4 and cnt[("P3", "B")] == 0 and cnt[("P3", "H")] == 2, cnt
assert (sum(1 for s in S if s[3]=="B"), sum(1 for s in S if s[3]=="H"), sum(1 for s in S if s[3]=="V")) == (10, 14, 10)
assert sum(1 for s in S if s[0] == "P1") == 12
assert len({s[1] for s in S if s[0] == "P2"}) == 4 and sum(1 for s in S if s[0] == "P2") == 16
assert sum(1 for s in S if s[0] == "P3") == 6
unit = {"P1": 0.25, "P2": 0.25, "P3": 0.5}
marks = collections.defaultdict(float)
for s in S: marks[s[3]] += unit[s[0]]
assert abs(sum(marks.values()) - 10) < 1e-9, marks

def vn(x):
    return (f"{x:.2f}".rstrip("0").rstrip(".")).replace(".", ",")

def addr(s):
    if s[0] == "P2":
        return f"Phần II, câu {s[1]}, ý {s[2]}"
    return f"{'Phần I' if s[0]=='P1' else 'Phần III'}, câu {s[1]}"

# per-bài summary (by chủ đề + bài); Phần II has no bài, only the chủ đề of its câu
bytopic = collections.OrderedDict()
for s in S:
    key = (s[4], s[5] or "Phần II không gắn bài, chỉ gắn từng ý", s[6])
    bytopic.setdefault(key, []).append(s)

def counts_sentence(items):
    parts = []
    for p in ("P1", "P2", "P3"):
        for l in ("B", "H", "V"):
            n = sum(1 for s in items if s[0] == p and s[3] == l)
            if n:
                unit_word = "ý" if p == "P2" else "câu"
                parts.append(f"{n} {unit_word} {KIND[p].lower()} mức {LV[l]}")
    return "; ".join(parts)

def lv_counts(part):
    return [sum(1 for s in S if s[0] == part and s[3] == l) for l in "BHV"]

L = []
w = L.append
w("# Toán 12 — ma trận thật (bản mẫu, đã sửa theo 5 câu trả lời ngày 29/10)\n")
w("Mỗi câu hoặc mỗi ý có một khối riêng, viết đầy đủ bằng chữ. Không dùng mã viết tắt như C3, 1C, NL.1. Quy tắc viết rút ra từ bản này nằm ở `docs/release/next/matrix-writing-rules.md`.\n")
w("**Trạng thái:** bản mẫu chờ duyệt cuối. Chưa nạp vào code, chưa chạy check.py, chưa thử sinh đề từ bản này.\n")
w("## 1. Khung đề (lấy từ khung đã đăng ký trong code)\n")
w("- Thời gian: 90 phút. Tổng điểm: 10.")
w("- Phần I: 12 câu nhiều lựa chọn, 0,25 điểm mỗi câu, tổng 3,0 điểm.")
w("- Phần II: 4 câu đúng/sai, mỗi câu 4 ý a, b, c, d. Chấm theo bậc thang: đúng 1 ý được 0,1; đúng 2 ý được 0,25; đúng 3 ý được 0,5; đúng cả 4 ý được 1,0. Ma trận này tính trung bình 0,25 điểm mỗi ý, tổng 4,0 điểm.")
w("- Phần III: 6 câu trả lời ngắn, 0,5 điểm mỗi câu, tổng 3,0 điểm. Đáp số là một số, dấu phẩy thập phân.\n")
w("## 2. Ba mức độ nghĩa là gì\n")
w("- **Biết:** nhận ra, nêu hoặc đọc thông tin có sẵn; áp dụng một công thức hoặc một quy tắc trong một bước.")
w("- **Hiểu:** thực hiện một quy trình đã học trong hai đến ba bước, giải thích hoặc so sánh kết quả, đọc ý nghĩa của số liệu.")
w("- **Vận dụng:** lập mô hình hoặc hàm số từ một tình huống mới, kết hợp nhiều kiến thức, nhiều bước tính, rồi kết luận và nêu lí do.\n")
w("Cách chia: cân bằng hơn số liệu đã gắn nhãn của đề chính thức 2025 mã 0101 (Biết 4, Hiểu 17, Vận dụng 13). Bản này lấy Biết 10, Hiểu 14, Vận dụng 10, vì các đề sở cho thấy Phần I có nhiều câu nhận biết hơn mức 4 câu. Đây là lựa chọn thiết kế, chưa phải số liệu đo.\n")
w("## 3. Tổng hợp bằng số\n")
w("| Phần | Số câu | Số ý chấm | Biết | Hiểu | Vận dụng | Điểm |")
w("|---|---|---|---|---|---|---|")
tot = [0, 0, 0]
for p, name, nc, pts in (("P1", "Phần I (nhiều lựa chọn)", 12, "3,0"), ("P2", "Phần II (đúng/sai)", 4, "4,0"), ("P3", "Phần III (trả lời ngắn)", 6, "3,0")):
    b, h, v = lv_counts(p); units = b + h + v
    tot = [tot[0] + b, tot[1] + h, tot[2] + v]
    w(f"| {name} | {nc} | {units} | {b} | {h} | {v} | {pts} |")
w(f"| **Tổng** | 22 | {sum(tot)} | {tot[0]} | {tot[1]} | {tot[2]} | 10,0 |")
w(f"\nTheo điểm: Biết {vn(marks['B'])} điểm ({vn(marks['B']*10)}%), Hiểu {vn(marks['H'])} điểm ({vn(marks['H']*10)}%), Vận dụng {vn(marks['V'])} điểm ({vn(marks['V']*10)}%).\n")
n11 = len({(s[0], s[1]) for s in S if s[6] in (K10, K11)})
w(f"Kiến thức lớp 10 và 11 chiếm {n11} trên 22 câu ({vn(n11/22*100)}%): 5 câu ở Phần I, 3 câu ở Phần III. Trong 7 đề đã xem, tỉ lệ này khoảng 38% ở Phần I.\n")
assert n11 == 8

w("## 4. Số câu theo chủ đề và bài\n")
w("| Chủ đề | Bài hoặc nội dung | Lớp | Số câu hoặc số ý theo dạng, mức độ | Điểm |")
w("|---|---|---|---|---|")
for (topic, bai, grade), items in bytopic.items():
    pts = sum(unit[s[0]] for s in items)
    w(f"| {topic} | {bai} | {grade} | {counts_sentence(items)} | {vn(pts)} |")
w("\nBài 8, Bài 10 và Bài 16 không có câu nào trong bản mẫu: đây là chủ ý, vì ở mỗi đề ban ra đề phải chọn trong số các nội dung hay gặp và các bài này ít xuất hiện trong 7 đề đã xem.\n")

w("## 5. Chi tiết từng câu và từng ý\n")
cur = None
for s in S:
    part = s[0]
    if part != cur:
        cur = part
        w(f"\n### {'Phần I — Nhiều lựa chọn' if part=='P1' else 'Phần II — Đúng/sai' if part=='P2' else 'Phần III — Trả lời ngắn'}\n")
        if part == "P2":
            w("Mỗi câu của Phần II thuộc một chủ đề, tức một chương của phạm vi bài kiểm tra tổng thể. Phần II không gắn bài; chỉ gắn từng ý.\n")
    pts = unit[part]
    w(f"**{addr(s)}** · {KIND[part]} · {vn(pts)} điểm · mức **{LV[s[3]]}**")
    if part == "P2":
        w(f"- Chủ đề (một chương của phạm vi kiểm tra): {s[4]} ({s[6]})")
    else:
        w(f"- Chủ đề: {s[4]}")
        w(f"- Bài: {s[5]} ({s[6]})")
    w(f"- Mục tiêu đánh giá: {s[7]}")
    w(f"- Dạng câu hỏi và dữ kiện: {s[8]}")
    w(f"- Năng lực: {NL[s[9]]}")
    if s[10]:
        w(f"- Mức độ gặp trong các đề đã xem: {s[10]}")
    w("")

w("## 6. Cơ sở của việc chọn chủ đề\n")
w("Mình xếp các câu của 7 đề Toán 2025–2026 vào bài bằng tay, dựa vào phần đầu của từng câu: đề chính thức 2025 mã 0101 và 6 đề của các sở (Bắc Ninh, Đà Nẵng, Hà Tĩnh, Hải Phòng lần 1 và lần 2, Phú Thọ). Số đề ghi ở mỗi câu là số đề có ít nhất một câu thuộc dạng đó, kiểm đếm tay nên chỉ là ước lượng.\n")
w("Những dạng xuất hiện gần như đề nào cũng có:")
w("- Phần I: phương trình hoặc bất phương trình mũ và lôgarit (7/7); vectơ chỉ phương hoặc vectơ pháp tuyến (6/7 và 5/7); cấp số cộng hoặc cấp số nhân (6/7); tứ phân vị của mẫu số liệu ghép nhóm (6/7); nguyên hàm của hàm cơ bản; thể tích khối chóp hoặc lăng trụ; vectơ trong hình hộp.")
w("- Phần II: gần như mỗi đề có một câu khảo sát hàm số hoặc đạo hàm gắn thực tế, một câu tích phân (vận tốc, diện tích, thể tích), một câu Oxyz tình huống (máy bay, đường đi), và một câu xác suất có điều kiện kiểu xét nghiệm (7/7).")
w("- Phần III: tối ưu bằng đạo hàm, hình học không gian (khoảng cách, góc), đếm tổ hợp, quy hoạch tuyến tính, tích phân thể tích, Oxyz với mặt cầu.\n")
w("**Hạn chế cần biết:**")
w("- Chỉ mã 0101 chắc chắn là đề chính thức. Sáu đề sở là các file trong `outputs/official-exams-2025/drive-provincial-toan`; nguồn gốc chưa được xác minh, có thể là bản dựng lại.")
w("- Mã đề 0101 mới có nhãn mức độ do phiên làm việc gắn, chưa có nhãn chính thức nào.")
w("- Chưa có các mã đề khác của 2025 hay đề chính thức 2026. Kế hoạch OCR đề tỉnh (`docs/release/next/ocr-provincial/HANDOFF.md`) sẽ bổ sung; danh sách dạng kinh điển sẽ đổi khi có thêm đề.")
w("- Đề tham khảo 2025 (kết quả OCR-1) không dùng để lấy chủ đề vì quy tắc 'đề tham khảo chỉ làm khung'.\n")

w("## 7. Các quyết định của chủ app (29/10)\n")
w("1. Tỉ lệ mức độ cân bằng hơn: Biết 10, Hiểu 14, Vận dụng 10 (đã áp dụng).")
w("2. Giữ kiến thức lớp 10 và 11 (đã giữ, 8 trên 22 câu).")
w("3. Các bài ít gặp (8, 10, 16) không đưa vào; ma trận chỉ gồm nội dung thường ra (đã áp dụng).")
w("4. Phần II không gắn bài, chỉ gắn từng ý; mỗi câu thuộc một chương của phạm vi kiểm tra (đã áp dụng).")
w("5. Ghi năng lực bằng tên đầy đủ ở mỗi câu và mỗi ý (đã áp dụng).")
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text("\n".join(L), encoding="utf-8")
print("slots", len(S), "marks", dict(marks), "lines", len(L))

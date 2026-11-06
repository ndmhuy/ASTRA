"""Original teaching notes; chapter labels demonstrate filtering, not a verified book mapping."""
from dataclasses import asdict
import hashlib
import json
from .models import CONFIG, SourceDocument

# These notes are authored for this app; no textbook or exam text is reproduced.
NOTES = [
    ("vat-li", 11, 4, "Định luật Ohm và điện trở", "Định luật Ohm liên hệ cường độ dòng điện I, hiệu điện thế U và điện trở R: I = U/R. Với một điện trở thuần ở nhiệt độ không đổi, cường độ dòng điện tỉ lệ thuận với hiệu điện thế đặt vào hai đầu điện trở. Đơn vị: I đo bằng ampe (A), U bằng vôn (V), R bằng ôm (Ω). Ví dụ tự soạn: điện trở 6 Ω chịu hiệu điện thế 12 V thì dòng điện là 2 A. Không áp dụng dạng tuyến tính này cho mọi linh kiện hoặc khi nhiệt độ thay đổi đáng kể. Từ khóa: định luật Ôm, Ohm law, resistance, current, voltage."),
    ("vat-li", 11, 4, "Ghép điện trở nối tiếp và song song", "Mạch nối tiếp có cùng dòng điện qua các điện trở và điện trở tương đương R = R1 + R2. Mạch song song có cùng hiệu điện thế giữa các nhánh và 1/R = 1/R1 + 1/R2. Với hai điện trở 6 Ω mắc song song, điện trở tương đương là 3 Ω; mắc nối tiếp là 12 Ω. Sau khi xác định điện trở tương đương, dùng định luật Ohm để tìm dòng điện của toàn mạch. Phải xác định đúng hai nút của nhánh song song trước khi áp dụng công thức. Từ khóa: định luật Ohm, điện trở, circuits, series, parallel."),
    ("vat-li", 11, 1, "Chu kì và tần số dao động", "Dao động tuần hoàn lặp lại trạng thái sau những khoảng thời gian bằng nhau. Chu kì T là thời gian thực hiện một dao động, tần số f là số dao động trong một giây: f = 1/T. Tần số góc ω = 2πf. Nếu T = 0,5 s thì f = 2 Hz. Dao động điều hòa có li độ dạng x = A cos(ωt + φ). Biên độ A không âm; pha ban đầu phụ thuộc mốc thời gian. Từ khóa: dao động, chu kì, tần số, oscillation."),
    ("vat-li", 10, 2, "Vận tốc và gia tốc", "Vận tốc biểu thị sự thay đổi vị trí theo thời gian; gia tốc biểu thị sự thay đổi vận tốc theo thời gian. Trong chuyển động thẳng có gia tốc không đổi: v = v0 + at và độ dịch chuyển Δx = v0t + at²/2. Cần chọn chiều dương trước khi thay số và giữ dấu của vận tốc, gia tốc. Gia tốc âm không luôn có nghĩa vật chậm dần: cần so sánh chiều gia tốc với chiều vận tốc. Từ khóa: động học, vận tốc, gia tốc, velocity, acceleration."),
    ("toan", 11, 1, "Hàm số lượng giác", "Trên đường tròn lượng giác, sin và cos là các tọa độ tương ứng của điểm biểu diễn góc. Các đẳng thức cơ bản gồm sin²x + cos²x = 1 và tan x = sin x/cos x khi cos x khác 0. Hàm sin và cos có chu kì 2π; tan có chu kì π. Khi giải phương trình lượng giác, cần ghi đầy đủ họ nghiệm và thống nhất đơn vị góc. Ví dụ: sin x = 0 có nghiệm x = kπ, k nguyên. Từ khóa: lượng giác, trigonometry, sine, cosine."),
    ("toan", 11, 2, "Cấp số cộng", "Cấp số cộng là dãy số có hiệu giữa hai số hạng liên tiếp không đổi, gọi là công sai d. Số hạng tổng quát un = u1 + (n−1)d. Tổng n số hạng đầu Sn = n(u1 + un)/2. Ví dụ tự soạn: u1 = 3 và d = 2 thì u5 = 11, S5 = 35. Cần phân biệt công sai của cấp số cộng với công bội của cấp số nhân. Từ khóa: dãy số, cấp số cộng, arithmetic sequence."),
    ("toan", 12, 1, "Đạo hàm và tính đơn điệu", "Đạo hàm mô tả tốc độ biến thiên tức thời của hàm số. Trên một khoảng, nếu hàm khả vi và đạo hàm dương tại mọi điểm thì hàm đồng biến trên khoảng đó; nếu đạo hàm âm thì hàm nghịch biến. Khi lập bảng biến thiên, cần xác định miền xác định, điểm đạo hàm bằng 0 và điểm đạo hàm không tồn tại. Phải kiểm tra dấu hai bên thay vì kết luận cực trị chỉ từ điều kiện đạo hàm bằng 0. Từ khóa: đạo hàm, đơn điệu, derivative, monotonicity."),
    ("hoa-hoc", 10, 1, "Cấu tạo nguyên tử", "Nguyên tử gồm hạt nhân chứa proton, neutron và lớp vỏ electron. Số hiệu nguyên tử Z bằng số proton; với nguyên tử trung hòa, số electron bằng Z. Số khối A là tổng số proton và neutron. Các đồng vị có cùng Z nhưng khác số neutron. Khi tính số neutron dùng N = A − Z; không dùng nguyên tử khối trung bình làm số khối của một đồng vị cụ thể. Từ khóa: nguyên tử, proton, neutron, electron, atom."),
    ("hoa-hoc", 11, 1, "Cân bằng hóa học", "Cân bằng hóa học của phản ứng thuận nghịch là trạng thái động: tốc độ phản ứng thuận bằng tốc độ phản ứng nghịch. Nồng độ các chất ổn định theo thời gian nhưng không nhất thiết bằng nhau. Thay đổi nhiệt độ có thể làm thay đổi hằng số cân bằng; chất xúc tác giúp đạt cân bằng nhanh hơn nhưng không làm thay đổi vị trí cân bằng ở cùng nhiệt độ. Từ khóa: cân bằng hóa học, chemical equilibrium, catalyst."),
    ("sinh-hoc", 10, 2, "Màng sinh chất và vận chuyển", "Màng sinh chất có lớp kép phospholipid và protein, có tính thấm chọn lọc. Khuếch tán thụ động diễn ra theo gradient nồng độ; vận chuyển chủ động có thể ngược gradient và cần nguồn năng lượng. Thẩm thấu là sự vận chuyển nước qua màng thấm chọn lọc. Khi giải thích sự thay đổi thể tích tế bào, cần so sánh môi trường trong và ngoài tế bào và xét sự có mặt của thành tế bào. Từ khóa: tế bào, màng sinh chất, thẩm thấu, osmosis."),
    ("sinh-hoc", 11, 1, "Quang hợp ở thực vật", "Quang hợp chuyển năng lượng ánh sáng thành năng lượng hóa học. Ở thực vật, pha sáng tạo ATP và NADPH; quá trình cố định carbon sử dụng các sản phẩm này để tổng hợp chất hữu cơ. Oxy giải phóng trong quang hợp có nguồn gốc từ nước. Cường độ ánh sáng, nồng độ carbon dioxide và nhiệt độ có thể giới hạn tốc độ quang hợp. Từ khóa: quang hợp, chlorophyll, photosynthesis."),
    ("tieng-anh", 11, 1, "Present perfect and past simple", "Use the past simple for an action completed at a specified past time: I finished the exercise yesterday. Use the present perfect to connect a past event or experience with the present: I have finished the exercise, so I can help you now. A finished time expression such as yesterday normally goes with the past simple. Compare the intended time reference rather than translating each verb word for word. Từ khóa: hiện tại hoàn thành, quá khứ đơn, grammar, present perfect, past simple.")
]


def make_document(subject, grade, chapter, title, content, document_id, **extra):
    if not isinstance(content, str) or not content.strip():
        raise ValueError("Document content must be a nonempty string.")
    fields = dict(document_id=document_id, subject=subject, grade=grade, chapter=chapter,
                  lesson=None, semester=None, title=title, content=content,
                  series=CONFIG["series"], edition="local-demo-v1", source_id=document_id,
                  source_locator="Original note / full text", source_version="1",
                  content_sha256=hashlib.sha256(content.encode("utf-8")).hexdigest(),
                  approval_status="approved", approved_by="Local demonstration author",
                  approved_on="2026-11-06", rights_evidence="Original app demonstration notes",
                  evidence_class="synthetic", allow_local_retrieval=True, allow_quotation=True)
    fields.update(extra)
    return SourceDocument(**fields)


def demo_documents():
    return [make_document(*note, document_id=f"demo-{i:02d}") for i, note in enumerate(NOTES, 1)]


def fingerprint(documents):
    raw = json.dumps([asdict(d) for d in documents], sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

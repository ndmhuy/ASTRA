"""Local pre-generated exam content for offline/zero-cost runs."""

import asyncio
import json
from pathlib import Path

from exam_baseline.vact import template as vact_template

_THPT_P1 = [
    (
        "Cho hàm số $y = x^3 - 3x^2 + 2$. Điểm cực tiểu của đồ thị hàm số đã cho có tọa độ là:",
        {"A": "$(0; 2)$", "B": "$(2; -2)$", "C": "$(1; 0)$", "D": "$(-1; -2)$"},
        "B",
        "Ta có $y' = 3x^2 - 6x = 0 \\Leftrightarrow x = 0$ hoặc $x = 2$. "
        "Qua $x = 2$, $y'$ đổi dấu từ âm sang dương nên $x = 2$ là điểm cực tiểu, $y(2) = -2$.",
    ),
    (
        (
            "Tiệm cận đứng của đồ thị hàm số $y = \\frac{2x - 1}{x + 3}$ là đường thẳng có phương"
            " trình:"
        ),
        {"A": "$x = 2$", "B": "$x = -3$", "C": "$y = 2$", "D": "$x = 3$"},
        "B",
        "Mẫu thức $x + 3 = 0 \\Leftrightarrow x = -3$ và tử thức $2(-3) - 1 = -7 \\neq 0$ "
        "nên tiệm cận đứng là $x = -3$.",
    ),
    (
        "Nghiệm của phương trình $\\log_2(x - 1) = 3$ là:",
        {"A": "$x = 7$", "B": "$x = 9$", "C": "$x = 10$", "D": "$x = 5$"},
        "B",
        "Điều kiện $x > 1$. Phương trình tương đương $x - 1 = 2^3 = 8 \\Leftrightarrow x = 9$.",
    ),
    (
        "Tập nghiệm của bất phương trình $3^{x-1} > 9$ là:",
        {
            "A": "$(3; +\\infty)$",
            "B": "$(2; +\\infty)$",
            "C": "$(-\\infty; 3)$",
            "D": "$[3; +\\infty)$",
        },
        "A",
        "Ta có $3^{x-1} > 3^2 \\Leftrightarrow x - 1 > 2 \\Leftrightarrow x > 3$.",
    ),
    (
        "Họ tất cả các nguyên hàm của hàm số $f(x) = 3x^2 + 2\\cos x$ là:",
        {
            "A": "$x^3 - 2\\sin x + C$",
            "B": "$x^3 + 2\\sin x + C$",
            "C": "$6x - 2\\sin x + C$",
            "D": "$3x^3 + 2\\sin x + C$",
        },
        "B",
        "Áp dụng bảng nguyên hàm cơ bản: $\\int (3x^2 + 2\\cos x)\\,dx = x^3 + 2\\sin x + C$.",
    ),
    (
        "Nếu $\\int_0^2 f(x)\\,dx = 5$ thì $\\int_0^2 [2f(x) - 3]\\,dx$ bằng:",
        {"A": "$4$", "B": "$7$", "C": "$10$", "D": "$16$"},
        "A",
        (
            "Ta có $\\int_0^2 [2f(x) - 3]\\,dx = 2\\int_0^2 f(x)\\,dx - 3(2 - 0) = 2 \\cdot 5 - 6"
            " = 4$."
        ),
    ),
    (
        "Trong không gian $Oxyz$, mặt phẳng $(P): 2x - y + 3z - 4 = 0$ có một vectơ pháp tuyến là:",
        {
            "A": "$\\vec{n} = (2; 1; 3)$",
            "B": "$\\vec{n} = (2; -1; 3)$",
            "C": "$\\vec{n} = (-1; 3; -4)$",
            "D": "$\\vec{n} = (2; -1; -4)$",
        },
        "B",
        (
            "Hệ số của $x, y, z$ trong phương trình $(P)$ cho một vectơ pháp tuyến $\\vec{n} = "
            "(2; -1; 3)$."
        ),
    ),
    (
        "Trong không gian $Oxyz$, đường thẳng $d: \\frac{x-1}{2} = \\frac{y+2}{-1} = \\frac{z}{4}$ "
        "đi qua điểm nào sau đây?",
        {
            "A": "$M(1; -2; 0)$",
            "B": "$N(-1; 2; 0)$",
            "C": "$P(2; -1; 4)$",
            "D": "$Q(1; 2; 0)$",
        },
        "A",
        "Thay tọa độ $M(1; -2; 0)$ vào phương trình chính tắc của $d$ ta được $0 = 0 = 0$.",
    ),
    (
        "Trong không gian $Oxyz$, mặt cầu $(S): (x-2)^2 + (y+1)^2 + z^2 = 16$ có bán kính bằng:",
        {"A": "$16$", "B": "$4$", "C": "$8$", "D": "$2$"},
        "B",
        (
            "Mặt cầu có phương trình $(x-a)^2 + (y-b)^2 + (z-c)^2 = R^2$ với $R^2 = 16 "
            "\\Rightarrow R = 4$."
        ),
    ),
    (
        "Cho cấp số cộng $(u_n)$ có $u_1 = 3$ và công sai $d = 4$. Giá trị của $u_5$ bằng:",
        {"A": "$15$", "B": "$19$", "C": "$23$", "D": "$12$"},
        "B",
        "Áp dụng công thức $u_n = u_1 + (n - 1)d$: $u_5 = 3 + 4 \\cdot 4 = 19$.",
    ),
    (
        (
            "Gieo một con xúc xắc cân đối và đồng chất một lần. Xác suất để xuất hiện mặt có số "
            "chấm chẵn là:"
        ),
        {
            "A": "$\\frac{1}{6}$",
            "B": "$\\frac{1}{3}$",
            "C": "$\\frac{1}{2}$",
            "D": "$\\frac{2}{3}$",
        },
        "C",
        (
            "Không gian mẫu có $6$ phần tử; các mặt chẵn là $\\{2; 4; 6\\}$ gồm $3$ kết quả nên "
            "$P = \\frac{3}{6} = \\frac{1}{2}$."
        ),
    ),
    (
        "Cho mẫu số liệu ghép nhóm về thời gian tự học (phút) có các giá trị đại diện $25; 35; 45$ "
        "với tần số tương ứng là $4; 8; 8$. Số trung bình của mẫu số liệu này bằng:",
        {"A": "$35$", "B": "$37$", "C": "$38$", "D": "$40$"},
        "B",
        (
            "Số trung bình $\\bar{x} = \\frac{25 \\cdot 4 + 35 \\cdot 8 + 45 \\cdot 8}{4 + 8 + 8}"
            " = \\frac{740}{20} = 37$."
        ),
    ),
]

_THPT_P2 = [
    (
        (
            "Cho hàm số $f(x) = x^4 - 2x^2 + 3$ xác định trên $\\mathbb{R}$. Xét tính đúng sai "
            "của các mệnh đề sau:"
        ),
        [
            (
                "Đạo hàm của hàm số là $f'(x) = 4x^3 - 4x$.",
                True,
                "Tính đạo hàm trực tiếp cho $f'(x) = 4x^3 - 4x$.",
            ),
            (
                "Hàm số có đúng một điểm cực trị.",
                False,
                "$f'(x) = 0$ có ba nghiệm phân biệt $x = 0, \\pm 1$.",
            ),
            (
                "Giá trị cực tiểu của hàm số bằng $2$.",
                True,
                "Tại $x = \\pm 1$, hàm số đạt cực tiểu $f(\\pm 1) = 2$.",
            ),
            (
                "Hàm số đồng biến trên khoảng $(0; 1)$.",
                False,
                "Trên $(0; 1)$, $f'(x) = 4x(x^2 - 1) < 0$ nên nghịch biến.",
            ),
        ],
        "Dùng đạo hàm bậc nhất để xét khoảng đơn điệu và cực trị của hàm bậc bốn trùng phương.",
    ),
    (
        "Một vật chuyển động thẳng với vận tốc $v(t) = 3t^2 + 2$ (m/s), trong đó $t \\ge 0$ "
        "tính bằng giây. "
        "Xét tính đúng sai của các mệnh đề sau:",
        [
            (
                "Tại thời điểm $t = 0$, vận tốc của vật bằng $2\\text{ m/s}$.",
                True,
                "Thay $t = 0$ vào $v(t)$ được $v(0) = 2$.",
            ),
            (
                "Gia tốc tức thời của vật tại thời điểm $t = 2\\text{ s}$ là $12\\text{ m/s}^2$.",
                True,
                "Ta có $a(t) = v'(t) = 6t$, suy ra $a(2) = 12$.",
            ),
            (
                "Quãng đường vật đi được trong $2$ giây đầu tiên là $10\\text{ m}$.",
                False,
                "$s = \\int_0^2 (3t^2 + 2)\\,dt = (t^3 + 2t)\\big|_0^2 = 12\\text{ m}$.",
            ),
            (
                "Vận tốc của vật luôn tăng khi $t > 0$.",
                True,
                "Với $t > 0$, $a(t) = 6t > 0$ nên $v(t)$ đồng biến.",
            ),
        ],
        "Liên hệ đạo hàm và tích phân của hàm vận tốc $v(t)$ theo thời gian.",
    ),
    (
        "Trong không gian $Oxyz$, cho hai điểm $A(1; 0; 2)$, $B(3; -2; 4)$ và mặt phẳng $(P):"
        " x + y - z + 1 = 0$. "
        "Xét tính đúng sai của các mệnh đề sau:",
        [
            (
                "Tọa độ vectơ $\\overrightarrow{AB}$ là $(2; -2; 2)$.",
                True,
                "$\\overrightarrow{AB} = (3 - 1; -2 - 0; 4 - 2) = (2; -2; 2)$.",
            ),
            (
                "Trung điểm $I$ của đoạn thẳng $AB$ có tọa độ là $(2; -1; 3)$.",
                True,
                "Lấy trung bình cộng tọa độ $A$ và $B$ được $I(2; -1; 3)$.",
            ),
            (
                "Điểm $B(3; -2; 4)$ thuộc mặt phẳng $(P)$.",
                False,
                "Thay tọa độ $B(3; -2; 4)$ vào phương trình $(P)$ "
                "ta được $3 + (-2) - 4 + 1 = -2 \\neq 0$.",
            ),
            (
                "Độ dài đoạn thẳng $AB$ bằng $2\\sqrt{3}$.",
                True,
                "$AB = \\sqrt{2^2 + (-2)^2 + 2^2} = \\sqrt{12} = 2\\sqrt{3}$.",
            ),
        ],
        "Áp dụng các công thức tọa độ trong không gian $Oxyz$.",
    ),
    (
        "Một hộp chứa $6$ viên bi xanh và $4$ viên bi đỏ có cùng kích thước và khối lượng. "
        "Chọn ngẫu nhiên đồng thời $2$ viên bi từ hộp. Xét tính đúng sai của các mệnh đề sau:",
        [
            ("Số phần tử của không gian mẫu là $45$.", True, "$n(\\Omega) = C_{10}^2 = 45$."),
            (
                "Xác suất để lấy được $2$ viên bi cùng màu xanh bằng $\\frac{1}{3}$.",
                True,
                "$P = \\frac{C_6^2}{45} = \\frac{15}{45} = \\frac{1}{3}$.",
            ),
            (
                "Xác suất để lấy được $2$ viên bi cùng màu đỏ bằng $\\frac{2}{15}$.",
                True,
                "$P = \\frac{C_4^2}{45} = \\frac{6}{45} = \\frac{2}{15}$.",
            ),
            (
                "Xác suất để lấy được $2$ viên bi khác màu nhỏ hơn $\\frac{1}{2}$.",
                False,
                "$P = \\frac{6 \\cdot 4}{45} = \\frac{24}{45} = \\frac{8}{15} > \\frac{1}{2}$.",
            ),
        ],
        "Sử dụng tổ hợp để tính xác suất cổ điển.",
    ),
]

_THPT_P3 = [
    (
        "Tìm giá trị lớn nhất của hàm số $y = -x^2 + 4x + 5$ trên đoạn $[0; 3]$.",
        "9",
        "Đỉnh parabol là $x = 2 \\in [0; 3]$ cho giá trị lớn nhất $y(2) = -4 + 8 + 5 = 9$.",
    ),
    (
        "Cho hình lăng trụ đứng $ABC.A'B'C'$ có đáy là tam giác vuông cân tại $A$ với $AB = 3$ "
        "và chiều cao $AA' = 4$. Tính thể tích khối lăng trụ đã cho.",
        "18",
        (
            "Diện tích đáy $S = \\frac{1}{2} \\cdot 3 \\cdot 3 = 4{,}5$; thể tích $V = 4{,}5 "
            "\\cdot 4 = 18$."
        ),
    ),
    (
        "Gieo một đồng xu cân đối liên tiếp $3$ lần. Biết xác suất để cả $3$ lần đều ra mặt "
        "sấp là $\\frac{1}{a}$. "
        "Tìm giá trị của $a$.",
        "8",
        "Xác suất cần tìm là $\\left(\\frac{1}{2}\\right)^3 = \\frac{1}{8}$, suy ra $a = 8$.",
    ),
    (
        "Trong không gian $Oxyz$, khoảng cách từ điểm $M(1; 2; -2)$ đến mặt phẳng "
        "$(P): 2x - 2y + z + 7 = 0$ bằng bao nhiêu?",
        "1",
        (
            "Khoảng cách $d(M, (P)) = \\frac{|2(1) - 2(2) + (-2) + 7|}{\\sqrt{2^2 + (-2)^2 + "
            "1^2}} = \\frac{3}{3} = 1$."
        ),
    ),
    (
        "Một người gửi tiết kiệm $100$ triệu đồng với lãi suất $6\\%$/năm theo thể thức lãi đơn. "
        "Sau $2$ năm, tổng số tiền lãi người đó nhận được là bao nhiêu triệu đồng?",
        "12",
        "Tiền lãi sau $2$ năm theo lãi đơn là $100 \\cdot 6\\% \\cdot 2 = 12$ triệu đồng.",
    ),
    (
        "Cho cấp số nhân $(u_n)$ có $u_1 = 2$ và công bội $q = 3$. Tính tổng $u_1 + u_2 + u_3$.",
        "26",
        "Ta có $u_1 = 2, u_2 = 6, u_3 = 18$, suy ra tổng bằng $2 + 6 + 18 = 26$.",
    ),
]


def _thpt_demo_questions(slots) -> list[dict]:
    questions = []
    indices = {"P1": 0, "P2": 0, "P3": 0}
    for slot in slots:
        idx = indices[slot.part]
        indices[slot.part] += 1
        if slot.part == "P1":
            stem, choices, answer, solution = _THPT_P1[idx]
            questions.append(
                {
                    "id": slot.id,
                    "stem": stem,
                    "choices": choices,
                    "statements": [],
                    "answer": answer,
                    "solution": solution,
                    "illustration_request": None,
                }
            )
        elif slot.part == "P2":
            stem, stmts, solution = _THPT_P2[idx]
            questions.append(
                {
                    "id": slot.id,
                    "stem": stem,
                    "choices": {},
                    "statements": [
                        {"text": text, "answer": ans, "solution": sol} for text, ans, sol in stmts
                    ],
                    "answer": None,
                    "solution": solution,
                    "illustration_request": None,
                }
            )
        else:
            stem, answer, solution = _THPT_P3[idx]
            questions.append(
                {
                    "id": slot.id,
                    "stem": stem,
                    "choices": {},
                    "statements": [],
                    "answer": answer,
                    "solution": solution,
                    "illustration_request": None,
                }
            )
    return questions


_VACT_PASSAGES = {
    "g21_25": {
        "heading": "NHỊP ĐỜI TRÊN NHỮNG CON RẠCH PHƯƠNG NAM",
        "text": (
            "(1) Từ bao đời nay, mạng lưới kênh rạch chằng chịt ở đồng bằng sông Cửu Long "
            "không chỉ đóng vai trò "
            "dẫn nước tưới tiêu mà còn là mạch giao thông tự nhiên gắn kết các xóm làng.\n"
            "(2) Vào buổi sớm mai, những chiếc xuồng ba lá chở đầy rau củ, trái cây cập bến "
            "chợ nổi tạo nên "
            "một không gian trao đổi hàng hóa nhộn nhịp nhưng vẫn giữ được nét hiền hòa.\n"
            "(3) Khác với sự vội vã của các đại lộ bê tông, nhịp sống trên sông nước vận hành"
            " theo con nước lớn ròng; "
            "người lái ghe đọc được thời tiết qua hướng gió và sắc mây trên đường chân trời.\n"
            "(4) Tuy vậy, quá trình đô thị hóa và mở rộng đường bộ đã khiến nhiều bến sông "
            "xưa thu hẹp dần, "
            "để lại câu hỏi về cách bảo tồn không gian văn hóa sông nước song hành với phát "
            "triển kinh tế."
        ),
        "table": None,
    },
    "g26_30": {
        "heading": "ĐỌC CHẬM GIỮA THỜI ĐẠI THÔNG TIN TỨC THÌ",
        "text": (
            "(1) Thói quen lướt nhanh tiêu đề trong vài giây giúp con người tiếp nhận lượng "
            "tin tức lớn mỗi ngày, "
            "nhưng lại làm suy giảm khả năng kiên nhẫn trước những văn bản đòi hỏi suy ngẫm sâu.\n"
            "(2) Khi đọc một cuốn sách hay một tiểu luận dài, người đọc không chỉ thu nhận dữ"
            " kiện rời rạc "
            "mà còn tập luyện năng lực kết nối các lập luận, nhận diện mâu thuẫn và tự đối "
            "thoại với chính mình.\n"
            "(3) Các nhà nghiên cứu giáo dục chỉ ra rằng việc dành ra hai mươi phút mỗi ngày "
            "cho việc đọc sâu "
            "giúp cải thiện vốn từ vựng học thuật và khả năng tập trung bền bỉ ở người học trẻ.\n"
            "(4) Đọc chậm vì thế không phải là đi ngược lại nhịp sống hiện đại, mà là cách "
            "tạo một khoảng lặng "
            "cần thiết để tư duy không bị cuốn trôi bởi dòng thông tin ngắn hạn."
        ),
        "table": None,
    },
    "g46_52": {
        "heading": "GREEN ROOFS IN COMPACT CITIES",
        "text": (
            "(1) As metropolitan centers expand upward, rooftops account for nearly a quarter"
            " of exposed urban surfaces. "
            "Traditionally covered in dark asphalt that absorbs solar heat, these spaces are "
            "increasingly being "
            "converted into vegetated green roofs.\n"
            "(2) A layered green roof combines a waterproof membrane, a lightweight soil "
            "substrate, and drought-tolerant "
            "plants. During summer afternoons, evaporation from leaves and moist soil keeps "
            "roof surface temperatures "
            "significantly lower than those on conventional roofs.\n"
            "(3) Beyond cooling buildings, green roofs act as sponges during heavy rainfall. "
            "By temporarily retaining "
            "stormwater, they reduce peak runoff into aging municipal drainage pipes and help"
            " prevent street flooding.\n"
            "(4) Although installation requires structural assessment and higher upfront "
            "spending, long-term savings in "
            "air-conditioning electricity and extended roof membrane lifespan often offset "
            "the initial investment."
        ),
        "table": None,
    },
    "g53_60": {
        "heading": "RESTORING MANGROVES ALONG TROPICAL COASTLINES",
        "text": (
            "(1) Mangrove forests thrive along sheltered tropical estuaries where saltwater "
            "meets river sediment. "
            "Their dense, tangled root systems stabilize muddy shorelines and create "
            "sheltered nurseries for young fish, "
            "crabs, and shrimp.\n"
            "(2) Over recent decades, coastal development and aquaculture expansion cleared "
            "large stretches of mangrove "
            "cover. Without this natural barrier, nearby villages became far more vulnerable "
            "to storm surges and erosion.\n"
            "(3) Restoration projects have learned that simply planting single-species "
            "seedlings along open beaches often "
            "fails. Successful efforts first restore natural tidal flow and match local tree "
            "varieties to soil salinity.\n"
            "(4) Today, coastal communities increasingly combine mangrove conservation with "
            "sustainable eco-tourism and "
            "selective shellfish farming, proving that shoreline protection and local "
            "livelihoods can reinforce each other."
        ),
        "table": None,
    },
    "g73_74": {
        "heading": "",
        "text": (
            "Một xưởng thủ công sản xuất hai mẫu đèn trang trí loại A và loại B. Để hoàn "
            "thiện mỗi chiếc đèn loại A "
            "cần $2$ giờ gia công khung và $1$ giờ lắp mạch; mỗi chiếc đèn loại B cần $1$ giờ"
            " gia công khung và "
            "$2$ giờ lắp mạch. Mỗi tuần xưởng có tối đa $40$ giờ gia công khung và $35$ giờ "
            "lắp mạch."
        ),
        "table": None,
    },
    "g75_76": {
        "heading": "",
        "text": ("Cho cấp số cộng $(u_n)$ có $u_1 + u_4 = 14$ và $u_2 + u_5 = 20$."),
        "table": None,
    },
    "g77_78": {
        "heading": "",
        "text": (
            "Trong không gian $Oxyz$, cho điểm $A(1; -2; 3)$ và hai mặt phẳng "
            "$(P): 2x - y + 2z - 3 = 0$, $(Q): x + 2y - z + 1 = 0$."
        ),
        "table": None,
    },
    "g79_81": {
        "heading": "",
        "text": "Cho hàm số $y = x^3 - 3x + m$ với $m$ là tham số thực.",
        "table": None,
    },
    "g82_84": {
        "heading": "",
        "text": (
            "Một cửa hàng nhập linh kiện từ hai kho. Kho I có $12$ sản phẩm đạt chuẩn và $3$ "
            "sản phẩm lỗi. "
            "Kho II có $16$ sản phẩm đạt chuẩn và $4$ sản phẩm lỗi."
        ),
        "table": None,
    },
    "g85_87": {
        "heading": "",
        "text": (
            "Trong mặt phẳng tọa độ $Oxy$, cho tam giác $ABC$ có các đỉnh $A(1; 2)$, $B(4; "
            "6)$ và $C(7; 1)$."
        ),
        "table": None,
    },
    "g88_90": {
        "heading": "",
        "text": (
            "Cho hình chóp $S.ABCD$ có đáy $ABCD$ là hình vuông cạnh $a$, cạnh bên $SA$ vuông"
            " góc với mặt đáy "
            "và $SA = a$."
        ),
        "table": None,
    },
    "g91_93": {
        "heading": "",
        "text": (
            "Một hội nghị khoa học sắp xếp lịch trình $5$ báo cáo chuyên đề gồm: Trí tuệ nhân"
            " tạo ($A$), "
            "Sinh học ($B$), Hóa học ($C$), Vật lý ($D$) và Kinh tế ($E$) lần lượt từ vị trí "
            "$1$ đến $5$ thỏa mãn:\n"
            "- Báo cáo $A$ phải trình bày ngay trước báo cáo $C$.\n"
            "- Báo cáo $B$ trình bày sau báo cáo $D$.\n"
            "- Báo cáo $E$ không xếp ở vị trí đầu tiên và không xếp ở vị trí cuối cùng."
        ),
        "table": None,
    },
    "g94_96": {
        "heading": "",
        "text": (
            "Một đội tình nguyện chọn $4$ thành viên từ nhóm $6$ bạn gồm $3$ nam ($M, N, P$) "
            "và $3$ nữ ($H, K, L$) "
            "với các điều kiện:\n"
            "- Phải có ít nhất $2$ nữ trong đội được chọn.\n"
            "- Nếu chọn $M$ thì không chọn $P$.\n"
            "- $K$ và $N$ chỉ được chọn khi cả hai cùng có mặt hoặc cùng không được chọn."
        ),
        "table": None,
    },
    "g97_99": {
        "heading": "",
        "text": (
            "Bảng số liệu dưới đây thống kê doanh số bán xe máy điện của hai hãng X và Y "
            "(tính bằng nghìn chiếc) "
            "và tổng dung lượng thị trường toàn quốc trong hai năm $2020$ và $2025$:"
        ),
        "table": {
            "columns": ["Chỉ tiêu", "Năm 2020", "Năm 2025"],
            "rows": [
                ["Hãng X (nghìn chiếc)", "$30$", "$75$"],
                ["Hãng Y (nghìn chiếc)", "$45$", "$60$"],
                ["Tổng thị trường (nghìn chiếc)", "$150$", "$250$"],
            ],
        },
    },
    "g100_102": {
        "heading": "",
        "text": (
            "Bảng phân bố tần số ghép nhóm dưới đây ghi lại thời gian hoàn thành một bài kiểm"
            " tra trực tuyến "
            "(đơn vị: phút) của $100$ thí sinh:"
        ),
        "table": {
            "columns": ["Khoảng thời gian (phút)", "Số thí sinh (tần số)"],
            "rows": [
                ["$[10; 20)$", "$10$"],
                ["$[20; 30)$", "$25$"],
                ["$[30; 40)$", "$40$"],
                ["$[40; 50)$", "$20$"],
                ["$[50; 60]$", "$5$"],
            ],
        },
    },
    "g103_105": {
        "heading": "",
        "text": (
            "Khi hòa tan một chất tan không bay hơi vào nước nguyên chất, áp suất hơi bão hòa"
            " của dung dịch giảm "
            "tỉ lệ với phần mol của dung môi theo biểu thức $P = P_0 \\cdot "
            "\\frac{n_{\\text{dm}}}{n_{\\text{dm}} + n_{\\text{ct}}}$, "
            "trong đó $P_0$ là áp suất hơi bão hòa của nước nguyên chất ở cùng nhiệt độ ($P_0"
            " = 24\\text{ mmHg}$ ở $25^{\\circ}\\text{C}$). "
            "Cho khối lượng mol của nước là $18\\text{ g/mol}$, glucose "
            "($\\text{C}_6\\text{H}_{12}\\text{O}_6$) là $180\\text{ g/mol}$ "
            "và urea ($(\\text{NH}_2)_2\\text{CO}$) là $60\\text{ g/mol}$."
        ),
        "table": None,
    },
    "g106_108": {
        "heading": "",
        "text": (
            "Theo thuyết lượng tử ánh sáng, mỗi photon mang năng lượng $\\varepsilon = hf = "
            "\\frac{hc}{\\lambda}$, "
            "với hằng số Planck $h = 6{,}625 \\cdot 10^{-34}\\text{ J}\\cdot\\text{s}$, tốc "
            "độ ánh sáng trong chân không "
            "$c = 3 \\cdot 10^8\\text{ m/s}$ và $1\\text{ eV} = 1{,}6 \\cdot 10^{-19}\\text{ J}$. "
            "Ánh sáng khả kiến có bước sóng từ $0{,}38\\text{ }\\mu\\text{m}$ (tím) đến "
            "$0{,}76\\text{ }\\mu\\text{m}$ (đỏ)."
        ),
        "table": None,
    },
    "g109_111": {
        "heading": "",
        "text": (
            "Để khảo sát ảnh hưởng của nhiệt độ đến tốc độ phản ứng xúc tác bởi enzyme "
            "amylase, một nhóm học sinh "
            "đo lượng tinh bột bị thủy phân trong $5$ phút ở các mức nhiệt độ khác nhau với "
            "cùng nồng độ cơ chất và enzyme:"
        ),
        "table": {
            "columns": [
                "Ống nghiệm",
                "Nhiệt độ ($^{\\circ}\\text{C}$)",
                "Lượng tinh bột thủy phân (mg)",
            ],
            "rows": [
                ["1", "$10$", "$4{,}2$"],
                ["2", "$25$", "$11{,}5$"],
                ["3", "$37$", "$19{,}8$"],
                ["4", "$55$", "$8{,}4$"],
                ["5", "$80$", "$0{,}5$"],
            ],
        },
    },
    "g112_114": {
        "heading": "",
        "text": (
            "Theo báo cáo nhân khẩu học, một quốc gia có cơ cấu dân số bước vào giai đoạn già"
            " hóa khi tỉ lệ người từ "
            "$65$ tuổi trở lên đạt từ $7\\%$ tổng dân số, và được xem là dân số già khi tỉ lệ"
            " này đạt từ $14\\%$. "
            "Nguyên nhân chủ yếu làm tăng nhanh nhóm tuổi cao là mức sinh giảm liên tục kết "
            "hợp với tuổi thọ trung bình "
            "được cải thiện nhờ tiến bộ y tế và điều kiện sống."
        ),
        "table": None,
    },
    "g115_117": {
        "heading": "",
        "text": (
            "Cuộc Cách mạng công nghiệp lần thứ nhất khởi phát tại nước Anh vào nửa sau thế "
            "kỷ XVIII với sự ra đời "
            "của máy kéo sợi Jenny, máy hơi nước của James Watt và sự phát triển mạnh mẽ của "
            "ngành luyện kim, dệt may. "
            "Cuộc cách mạng này đã chuyển nền sản xuất từ lao động thủ công sang cơ khí hóa "
            "bằng máy móc."
        ),
        "table": None,
    },
    "g118_120": {
        "heading": "",
        "text": (
            "Doanh nghiệp thực phẩm sạch An Bình quyết định trích $5\\%$ lợi nhuận hằng năm "
            "để trồng cây xanh quanh khu "
            "công nghiệp và công bố minh bạch nguồn gốc nguyên liệu trên bao bì sản phẩm. Nhờ"
            " uy tín bền vững, doanh nghiệp "
            "thu hút thêm nhiều khách hàng trung thành và dễ dàng mở rộng hợp tác phân phối."
        ),
        "table": None,
    },
}


_VACT_STANDALONE = {
    1: (
        "Trong ca dao Nam Bộ, hình ảnh con cò thường được dùng để ẩn dụ cho điều gì?",
        {
            "A": "Cuộc đời lam lũ, nhẫn nại của người nông dân",
            "B": "Khát vọng chinh phục thiên nhiên kỳ vĩ",
            "C": "Vẻ đẹp kiêu sa của chốn cung đình",
            "D": "Không khí lễ hội rộn ràng ngày mùa",
        },
        "A",
        (
            "Con cò lặn lội bờ sông tượng trưng cho sự cần cù, chịu thương chịu khó của người lao"
            " động."
        ),
    ),
    2: (
        (
            "Biện pháp tu từ nào nổi bật trong hai câu: "
            '"Áo chàm đưa buổi phân ly / Cầm tay nhau biết nói gì hôm nay"?'
        ),
        {"A": "Hoán dụ", "B": "Nói quá", "C": "Nhân hóa", "D": "Điệp ngữ"},
        "A",
        '"Áo chàm" là dấu hiệu trang phục dùng để chỉ đồng bào Việt Bắc (hoán dụ).',
    ),
    3: (
        "Từ nào sau đây viết đúng chính tả tiếng Việt?",
        {"A": "Xán lạn", "B": "Sán lạn", "C": "Xáng lạn", "D": "Sáng lạn"},
        "A",
        'Từ Hán Việt chuẩn chính tả là "xán lạn" (rực rỡ, tươi sáng).',
    ),
    4: (
        'Từ "chạy" trong câu "Đồng hồ chạy rất chính xác" được dùng theo nghĩa nào?',
        {
            "A": "Nghĩa gốc",
            "B": "Nghĩa chuyển theo phương thức ẩn dụ",
            "C": "Nghĩa chuyển theo phương thức hoán dụ",
            "D": "Nghĩa đối lập",
        },
        "B",
        "Dựa trên sự tương đồng về hoạt động liên tục của bộ máy so với hành động di chuyển.",
    ),
    5: (
        'Câu "Mặc dù trời mưa to nhưng sân trường vẫn khô ráo lạ thường" thuộc kiểu câu ghép nào?',
        {
            "A": "Câu ghép chính phụ chỉ quan hệ tương phản",
            "B": "Câu ghép đẳng lập liệt kê",
            "C": "Câu ghép chỉ nguyên nhân - kết quả",
            "D": "Câu đơn mở rộng thành phần",
        },
        "A",
        'Cặp quan hệ từ "Mặc dù ... nhưng" biểu thị quan hệ nhượng bộ - tương phản.',
    ),
    6: (
        (
            "Phong cách ngôn ngữ nào thường sử dụng hệ thống thuật ngữ chuyên ngành và kết cấu "
            "lập luận chặt chẽ, khách quan?"
        ),
        {
            "A": "Phong cách ngôn ngữ sinh hoạt",
            "B": "Phong cách ngôn ngữ khoa học",
            "C": "Phong cách ngôn ngữ nghệ thuật",
            "D": "Phong cách ngôn ngữ báo chí",
        },
        "B",
        "Tính trừu tượng, khái quát, lý trí và chính xác là đặc trưng của ngôn ngữ khoa học.",
    ),
    7: (
        (
            "Chọn từ thích hợp nhất điền vào chỗ trống: "
            '"Bức tranh tái hiện ___ cảnh sinh hoạt ven sông lúc bình minh."'
        ),
        {"A": "sinh động", "B": "rung động", "C": "chấn động", "D": "biến động"},
        "A",
        '"Tái hiện sinh động" là kết hợp từ chuẩn nghĩa miêu tả sự sống động.',
    ),
    8: (
        "Câu nào sau đây mắc lỗi thiếu chủ ngữ?",
        {
            "A": "Qua tác phẩm này, tác giả đã phản ánh chân thực đời sống làng quê.",
            "B": "Với những nỗ lực không ngừng trong suốt học kỳ vừa qua đã giúp Lan tiến bộ.",
            "C": "Những cánh diều chao liệng trên bầu trời chiều đầy gió.",
            "D": "Trên triền đê, tiếng sáo diều vi vu ngân dài.",
        },
        "B",
        'Cụm từ bắt đầu bằng "Với..." làm trạng ngữ nên phần còn lại thiếu chủ ngữ.',
    ),
    9: (
        (
            "Thao tác lập luận nào chủ yếu dùng lý lẽ và dẫn chứng để làm sáng tỏ tính đúng đắn "
            "của một nhận định?"
        ),
        {"A": "Chứng minh", "B": "So sánh", "C": "Bình luận", "D": "Phân tích"},
        "A",
        "Chứng minh dùng dẫn chứng xác thực và lý lẽ hợp lý để khẳng định luận điểm.",
    ),
    10: (
        'Thành ngữ "Nước đổ lá khoai" thường dùng để nói về tình huống nào?',
        {
            "A": "Lời khuyên bảo không thấm vào đâu, không tạo chuyển biến",
            "B": "Sự đoàn kết gắn bó trong cộng đồng",
            "C": "Thành quả lao động đến rất nhanh chóng",
            "D": "Nỗi vất vả trong nghề trồng lúa nước",
        },
        "A",
        "Nước trượt khỏi bề mặt lá khoai không đọng lại, ví với việc tiếp thu không hiệu quả.",
    ),
    11: (
        (
            "Xác định lỗi sai trong câu: "
            '"Hội nghị đã tổng kết những kết quả đạt được '
            'và đề ra phương hướng giải quyết khắc phục."'
        ),
        {
            "A": "Lặp từ thừa nghĩa ở cuối câu",
            "B": "Sai chính tả",
            "C": "Thiếu vị ngữ",
            "D": "Sai quan hệ từ",
        },
        "A",
        '"Giải quyết" và "khắc phục" đồng nghĩa đặt cạnh nhau gây thừa từ.',
    ),
    12: (
        "Thể thơ lục bát truyền thống có đặc điểm gieo vần nào sau đây?",
        {
            "A": "Tiếng thứ $6$ câu lục vần với tiếng thứ $6$ câu bát",
            "B": "Chỉ gieo vần ở cuối các câu chẵn",
            "C": "Không quy định thanh điệu ở tiếng thứ $6$ và $8$",
            "D": "Mỗi khổ cố định $4$ dòng $7$ chữ",
        },
        "A",
        "Vần lưng giữa tiếng $6$ câu lục và tiếng $6$ câu bát là quy luật đặc trưng của lục bát.",
    ),
    13: (
        "Trong văn bản nghị luận, việc trích dẫn nhận định của chuyên gia có tác dụng chính là gì?",
        {
            "A": "Tăng sức thuyết phục và độ tin cậy cho luận điểm",
            "B": "Kéo dài dung lượng bài viết",
            "C": "Thay thế hoàn toàn ý kiến của người viết",
            "D": "Tạo yếu tố bất ngờ mang tính hư cấu",
        },
        "A",
        "Trích dẫn đáng tin cậy giúp củng cố cơ sở lập luận của tác giả.",
    ),
    14: (
        'Từ "xuân" trong câu "Tuổi xuân phơi phới ước mơ" mang nghĩa nào?',
        {
            "A": "Tuổi trẻ tràn đầy sức sống",
            "B": "Mùa đầu tiên trong năm dương lịch",
            "C": "Tiết khí giao mùa đầu hạ",
            "D": "Thời tiết ấm áp",
        },
        "A",
        'Từ "xuân" chuyển nghĩa ẩn dụ chỉ tuổi trẻ.',
    ),
    15: (
        "Dòng nào dưới đây chỉ gồm các từ láy?",
        {
            "A": "Lung linh, rì rào, man mác, bâng khuâng",
            "B": "Sách vở, bàn ghế, lung linh, rì rào",
            "C": "Xanh ngắt, đỏ thắm, tươi tốt, đẹp đẽ",
            "D": "Non nước, đất trời, sông núi, cây cỏ",
        },
        "A",
        "Cả bốn từ đều có quan hệ láy âm/vần giữa các tiếng.",
    ),
    16: (
        'Câu "Trời ơi, hôm nay gió mát quá!" thuộc kiểu câu phân loại theo mục đích nói nào?',
        {"A": "Câu cảm thán", "B": "Câu nghi vấn", "C": "Câu cầu khiến", "D": "Câu trần thuật"},
        "A",
        'Câu dùng từ cảm thán "Trời ơi" và dấu chấm than để bộc lộ cảm xúc.',
    ),
    17: (
        "Ý nghĩa của phép điệp cấu trúc trong văn bản chính luận thường là:",
        {
            "A": "Nhấn mạnh luận điểm và tạo nhịp điệu hùng hồn",
            "B": "Làm giảm tính liên kết giữa các đoạn",
            "C": "Thể hiện thái độ thờ ơ của người viết",
            "D": "Che giấu quan điểm cá nhân",
        },
        "A",
        "Điệp cấu trúc tạo nhấn mạnh và tăng sức truyền cảm cho lập luận.",
    ),
    18: (
        "Trật tự từ nào hợp lý nhất để nhấn mạnh chủ thể thực hiện hành động?",
        {
            "A": "Chính người nông dân đã lai tạo thành công giống lúa mới.",
            "B": "Giống lúa mới đã được lai tạo thành công vào năm ngoái.",
            "C": "Năm ngoái, một giống lúa mới đã xuất hiện.",
            "D": "Thành công ấy đến từ giống lúa mới.",
        },
        "A",
        'Cấu trúc "Chính ... đã ..." đặt chủ thể lên đầu câu để nhấn mạnh.',
    ),
    19: (
        'Trong tiếng Việt, cặp từ "bàn luận" và "thảo luận" có quan hệ ngữ nghĩa gì?',
        {
            "A": "Đồng nghĩa gần",
            "B": "Trái nghĩa",
            "C": "Đồng âm khác nghĩa",
            "D": "Bao hàm tuyệt đối",
        },
        "A",
        "Cả hai đều chỉ hoạt động trao đổi ý kiến về một vấn đề.",
    ),
    20: (
        "Yếu tố nào không thuộc cấu trúc cơ bản của một đoạn văn diễn dịch?",
        {
            "A": "Câu chủ đề đặt ở đầu đoạn",
            "B": "Các câu triển khai giải thích, minh họa cho câu đầu",
            "C": "Câu chủ đề khái quát chỉ xuất hiện ở cuối đoạn",
            "D": "Sự liên kết chặt chẽ về nội dung và hình thức",
        },
        "C",
        "Đoạn diễn dịch có câu chủ đề ở đầu đoạn; câu chủ đề ở cuối đoạn là đoạn quy nạp.",
    ),
    31: (
        "By the time the guests arrived, the host ___ already prepared dinner.",
        {"A": "has", "B": "had", "C": "was", "D": "will have"},
        "B",
        "Past perfect ('had prepared') describes an action completed before another past event.",
    ),
    32: (
        "The committee had to put ___ the annual festival due to heavy storms.",
        {"A": "off", "B": "on", "C": "up", "D": "out"},
        "A",
        "'Put off' means postpone.",
    ),
    33: (
        "She has made ___ progress in spoken English over the last six months.",
        {"A": "considerable", "B": "consider", "C": "considerably", "D": "considering"},
        "A",
        "An adjective ('considerable') is required to modify the noun 'progress'.",
    ),
    34: (
        "This electric bicycle is much ___ than the older model we tested yesterday.",
        {"A": "light", "B": "lighter", "C": "lightest", "D": "more light"},
        "B",
        "Comparative form of the one-syllable adjective 'light' is 'lighter'.",
    ),
    35: (
        "Students are encouraged to take part ___ community volunteering activities.",
        {"A": "at", "B": "on", "C": "in", "D": "with"},
        "C",
        "The fixed collocation is 'take part in'.",
    ),
    36: (
        "The team of researchers [A] are planning [B] to publish [C] its findings [D] next month.",
        {"A": "The team of researchers", "B": "are planning", "C": "to publish", "D": "next month"},
        "B",
        "Singular subject 'The team' takes singular verb 'is planning'.",
    ),
    37: (
        (
            "Each student [A] must submit [B] their assignment before [C] Friday afternoon [D] at"
            " the office."
        ),
        {"A": "must submit", "B": "their", "C": "Friday afternoon", "D": "at the office"},
        "B",
        "With singular 'Each student' in formal style, use 'his or her' rather than 'their'.",
    ),
    38: (
        (
            "My sister [A] enjoys reading historical novels, [B] listening to jazz, and [C] to "
            "paint [D] landscapes."
        ),
        {"A": "enjoys", "B": "listening to", "C": "to paint", "D": "landscapes"},
        "C",
        "Parallel structure after 'enjoys' requires gerund 'painting'.",
    ),
    39: (
        (
            "The new museum, [A] that opened [B] last spring, has already [C] attracted thousands"
            " of [D] visitors."
        ),
        {"A": "that", "B": "last spring", "C": "attracted", "D": "visitors"},
        "A",
        "Non-defining relative clauses after a comma use 'which', not 'that'.",
    ),
    40: (
        "Hardly [A] had the train [B] left the station [C] than it began to rain [D] heavily.",
        {"A": "Hardly", "B": "left the station", "C": "than", "D": "heavily"},
        "C",
        "'Hardly ... when' is the standard correlative pair, not 'than'.",
    ),
    41: (
        "Because the bridge was under repair, commuters had to take a longer route.",
        {
            "A": "The bridge repair forced commuters to take a longer route.",
            "B": "Commuters repaired the bridge before taking a shorter route.",
            "C": "Unless the bridge was repaired, commuters stopped traveling.",
            "D": "Taking a longer route helped workers repair the bridge faster.",
        },
        "A",
        "Option A preserves the exact cause-and-effect meaning.",
    ),
    42: (
        '"Remember to turn off the lab lights before locking the door," the teacher told Minh.',
        {
            "A": "The teacher reminded Minh to turn off the lab lights before locking the door.",
            "B": "The teacher accused Minh of leaving the lab lights on.",
            "C": "Minh asked the teacher to lock the lab door.",
            "D": "The teacher warned Minh not to enter the lab alone.",
        },
        "A",
        "'Remember to do something' transforms naturally to 'reminded someone to do something'.",
    ),
    43: (
        "No other library in the province holds as many rare manuscripts as this one.",
        {
            "A": "This library holds the largest collection of rare manuscripts in the province.",
            "B": "Several provincial libraries hold more rare manuscripts than this one.",
            "C": "This library used to keep fewer manuscripts than neighboring libraries.",
            "D": "Rare manuscripts are rarely stored in provincial libraries.",
        },
        "A",
        "Negative comparison with 'as many ... as' expresses the superlative.",
    ),
    44: (
        "If you water these indoor plants too frequently, their roots may rot.",
        {
            "A": "Overwatering these indoor plants can cause their roots to rot.",
            "B": "Indoor plants never survive without daily watering.",
            "C": "Root rot prevents anyone from watering indoor plants.",
            "D": "Watering plants less often will immediately dry out their leaves.",
        },
        "A",
        "Option A restates the warning clearly and accurately.",
    ),
    45: (
        "Although the software update looked simple, it took technicians three hours to verify.",
        {
            "A": (
                "Despite looking simple, the software update required "
                "three hours of technician verification."
            ),
            "B": "Technicians updated the software quickly because it looked simple.",
            "C": "The software update failed after three hours of testing.",
            "D": "Because it took three hours, the update looked complicated.",
        },
        "A",
        "'Despite + V-ing' accurately mirrors 'Although + clause'.",
    ),
    61: (
        "Tập nghiệm của phương trình $\\sqrt{2x + 1} = 3$ là:",
        {"A": "$\\{4\\}$", "B": "$\\{1\\}$", "C": "$\\{5\\}$", "D": "$\\{2\\}$"},
        "A",
        "Bình phương hai vế: $2x + 1 = 9 \\Leftrightarrow x = 4$ (thỏa điều kiện).",
    ),
    62: (
        "Số nghiệm nguyên của bất phương trình $x^2 - 5x + 4 \\le 0$ là:",
        {"A": "$3$", "B": "$4$", "C": "$5$", "D": "$2$"},
        "B",
        "Tập nghiệm là đoạn $[1; 4]$, chứa $4$ số nguyên: $1, 2, 3, 4$.",
    ),
    63: (
        "Một khoản tiền $50$ triệu đồng được gửi ngân hàng với lãi suất $0{,}5\\%$/tháng theo"
        " thể thức lãi kép. "
        "Sau $12$ tháng, tổng số tiền (triệu đồng) gần nhất với:",
        {"A": "$53{,}08$", "B": "$53{,}00$", "C": "$52{,}50$", "D": "$54{,}12$"},
        "A",
        "Ta có $50(1 + 0{,}005)^{12} \\approx 53{,}08$ triệu đồng.",
    ),
    64: (
        "Cho $\\log_2 3 = a$. Khi đó $\\log_4 27$ bằng:",
        {"A": "$\\frac{3a}{2}$", "B": "$3a$", "C": "$\\frac{2a}{3}$", "D": "$a^3$"},
        "A",
        "$\\log_4 27 = \\log_{2^2} 3^3 = \\frac{3}{2}\\log_2 3 = \\frac{3a}{2}$.",
    ),
    65: (
        "Một mạng lưới gồm $4$ trạm được nối vòng tròn bởi các tuyến cáp có độ dài $3, 5, 4, "
        "6$ km. "
        "Tổng độ dài tối thiểu của cây khung kết nối cả $4$ trạm là:",
        {"A": "$12$ km", "B": "$13$ km", "C": "$14$ km", "D": "$18$ km"},
        "A",
        "Loại bỏ cạnh dài nhất ($6$ km), còn lại $3 + 4 + 5 = 12$ km.",
    ),
    66: (
        (
            "Từ các chữ số $1, 2, 3, 4, 5$ có thể lập được bao nhiêu số tự nhiên có $3$ chữ số "
            "đôi một khác nhau?"
        ),
        {"A": "$60$", "B": "$125$", "C": "$10$", "D": "$24$"},
        "A",
        "Số cách chọn và sắp xếp $3$ chữ số từ $5$ chữ số là $A_5^3 = 60$.",
    ),
    67: (
        "Số nghiệm của phương trình $\\sin x = \\frac{1}{2}$ trên đoạn $[0; 2\\pi]$ là:",
        {"A": "$2$", "B": "$1$", "C": "$3$", "D": "$4$"},
        "A",
        "Có hai nghiệm trên $[0; 2\\pi]$ là $x = \\frac{\\pi}{6}$ và $x = \\frac{5\\pi}{6}$.",
    ),
    68: (
        (
            "Tam giác $ABC$ có $AB = 5$, $AC = 8$ và $\\widehat{A} = 60^{\\circ}$. Độ dài cạnh "
            "$BC$ bằng:"
        ),
        {"A": "$7$", "B": "$\\sqrt{89}$", "C": "$6$", "D": "$9$"},
        "A",
        (
            "Định lý côsin: $BC^2 = 25 + 64 - 2 \\cdot 5 \\cdot 8 \\cdot \\frac{1}{2} = 49 "
            "\\Rightarrow BC = 7$."
        ),
    ),
    69: (
        (
            "Giá trị của tham số $m$ để hàm số $f(x) = \\begin{cases} \\frac{x^2 - 9}{x - 3} & "
            "\\text{khi } x \\neq 3 \\\\ m + 2 & \\text{khi } x = 3 \\end{cases}$ liên tục tại $x"
            " = 3$ là:"
        ),
        {"A": "$4$", "B": "$6$", "C": "$3$", "D": "$2$"},
        "A",
        "$\\lim_{x \\to 3} (x + 3) = 6 = m + 2 \\Rightarrow m = 4$.",
    ),
    70: (
        "Đạo hàm của hàm số $y = x e^x$ là:",
        {"A": "$(x + 1)e^x$", "B": "$xe^x$", "C": "$e^x$", "D": "$(x - 1)e^x$"},
        "A",
        "Áp dụng quy tắc tích: $y' = e^x + xe^x = (x + 1)e^x$.",
    ),
    71: (
        "Cho $\\int_1^3 f(x)\\,dx = 6$. Giá trị của $\\int_1^3 [f(x) + 2]\\,dx$ bằng:",
        {"A": "$10$", "B": "$8$", "C": "$12$", "D": "$6$"},
        "A",
        "$\\int_1^3 [f(x) + 2]\\,dx = 6 + 2(3 - 1) = 10$.",
    ),
    72: (
        (
            "Diện tích hình phẳng giới hạn bởi đồ thị $y = x^2$, trục hoành và hai đường thẳng $x"
            " = 0, x = 3$ là:"
        ),
        {"A": "$9$", "B": "$3$", "C": "$27$", "D": "$4{,}5$"},
        "A",
        "$S = \\int_0^3 x^2\\,dx = \\frac{3^3}{3} = 9$.",
    ),
}

_VACT_GROUP_QUESTIONS = {
    21: (
        "Ý chính của đoạn (1) trong văn bản là gì?",
        {
            "A": "Vai trò tưới tiêu và giao thông truyền thống của kênh rạch Nam Bộ",
            "B": "Lịch sử hình thành các tuyến đường cao tốc hiện đại",
            "C": "Kỹ thuật đóng xuồng ba lá của người dân vùng sông nước",
            "D": "Biến đổi khí hậu toàn cầu ở khu vực Đông Nam Á",
        },
        "A",
        "Đoạn (1) giới thiệu hai chức năng cốt lõi của hệ thống kênh rạch.",
    ),
    22: (
        (
            'Chi tiết "nhịp sống trên sông nước vận hành theo con nước lớn ròng" '
            "ở đoạn (3) nhấn mạnh điều gì?"
        ),
        {
            "A": "Sự gắn bó hài hòa giữa sinh hoạt con người và quy luật tự nhiên",
            "B": "Tình trạng ùn tắc giao thông vào giờ cao điểm",
            "C": "Sự phụ thuộc hoàn toàn vào phương tiện cơ giới",
            "D": "Khó khăn trong việc mở rộng các đại lộ bê tông",
        },
        "A",
        "So sánh với đại lộ bê tông để làm nổi bật sự hòa nhịp với thủy triều và thời tiết.",
    ),
    23: (
        "Ở đoạn (4), tác giả bộc lộ mối quan tâm nào trước sự phát triển đường bộ?",
        {
            "A": "Làm sao giữ gìn văn hóa sông nước song song với phát triển kinh tế",
            "B": "Phản đối mọi công trình xây dựng cầu đường mới",
            "C": "Đề xuất đóng cửa tất cả các chợ nổi truyền thống",
            "D": "Khẳng định đường thủy đã hoàn toàn biến mất",
        },
        "A",
        "Đoạn (4) đặt câu hỏi về bài toán cân bằng bảo tồn và phát triển.",
    ),
    24: (
        "Phương thức biểu đạt chính kết hợp trong văn bản trên là:",
        {
            "A": "Thuyết minh kết hợp biểu cảm",
            "B": "Hành chính công vụ",
            "C": "Nghị luận bác bỏ thuần túy",
            "D": "Tự sự cổ tích",
        },
        "A",
        "Văn bản cung cấp thông tin về đời sống kênh rạch đồng thời bộc lộ tình cảm trân trọng.",
    ),
    25: (
        'Từ nào đồng nghĩa gần nhất với "nhộn nhịp" trong đoạn (2)?',
        {"A": "Sầm uất", "B": "Tĩnh lặng", "C": "Đơn điệu", "D": "Rời rạc"},
        "A",
        '"Sầm uất" gợi cảnh đông vui, tấp nập mua bán ở bến chợ.',
    ),
    26: (
        "Theo đoạn (1), hệ quả của thói quen chỉ lướt nhanh tiêu đề tin tức là gì?",
        {
            "A": "Giảm khả năng kiên nhẫn với các văn bản đòi hỏi suy nghĩ sâu",
            "B": "Giúp tăng ngay vốn từ vựng học thuật",
            "C": "Xóa bỏ hoàn toàn nhu cầu đọc tin hằng ngày",
            "D": "Làm tăng tốc độ ghi nhớ lập luận phức tạp",
        },
        "A",
        "Đoạn (1) nêu trực tiếp việc đọc lướt làm giảm sự kiên nhẫn đọc sâu.",
    ),
    27: (
        "Câu chủ đề thể hiện quan điểm cốt lõi ở đoạn (4) nhằm khẳng định điều gì?",
        {
            "A": "Đọc chậm giúp tạo khoảng lặng giữ tư duy trước tin tức ngắn hạn",
            "B": "Đọc chậm khiến con người lạc hậu với thời đại số",
            "C": "Mỗi người chỉ nên đọc sách in thay cho báo điện tử",
            "D": "Thông tin tức thì luôn sai lệch hoàn toàn",
        },
        "A",
        "Đoạn (4) khẳng định giá trị tích cực của đọc chậm trong bối cảnh hiện đại.",
    ),
    28: (
        'Ở đoạn (3), việc dẫn ý kiến "các nhà nghiên cứu giáo dục" có tác dụng gì?',
        {
            "A": "Tạo cơ sở khoa học đáng tin cậy cho lợi ích của việc đọc sâu",
            "B": "Phủ nhận vai trò của người học trẻ",
            "C": "Chứng minh hai mươi phút là thời lượng tối đa mỗi tuần",
            "D": "So sánh chương trình học giữa các bậc học",
        },
        "A",
        "Dẫn nguồn nghiên cứu giúp củng cố lập luận về lợi ích thực tế của đọc sâu.",
    ),
    29: (
        "Lợi ích nào sau đây của việc đọc sâu được nêu trong đoạn (2)?",
        {
            "A": "Rèn năng lực kết nối lập luận và tự đối thoại nội tâm",
            "B": "Thuộc lòng toàn bộ dữ kiện rời rạc",
            "C": "Giảm nhu cầu học ngoại ngữ",
            "D": "Tăng thời gian sử dụng mạng xã hội",
        },
        "A",
        "Đoạn (2) nêu rõ năng lực kết nối lập luận, nhận diện mâu thuẫn và tự đối thoại.",
    ),
    30: (
        'Nhan đề "Đọc chậm giữa thời đại thông tin tức thì" sử dụng cặp ý niệm nào?',
        {
            "A": "Tương phản giữa nhịp đọc sâu chậm rãi và tốc độ tin tức nhanh",
            "B": "Đồng nhất giữa sách dài và tiêu đề ngắn",
            "C": "Nhân quả giữa đọc chậm và mất thông tin",
            "D": "Liệt kê các thể loại văn học",
        },
        "A",
        'Sự đối lập giữa "đọc chậm" và "thông tin tức thì" làm nổi bật thông điệp bài viết.',
    ),
    46: (
        "What is the main topic of the passage?",
        {
            "A": "The environmental and economic roles of urban green roofs",
            "B": "How to mix lightweight concrete for skyscrapers",
            "C": "Ways to replace all city parks with parking garages",
            "D": "Reasons why dark asphalt roofs stay cooler in summer",
        },
        "A",
        (
            "The passage discusses cooling, stormwater retention, and long-term cost savings of "
            "green roofs."
        ),
    ),
    47: (
        (
            "According to paragraph (1), what fraction of exposed city surfaces is made up of "
            "rooftops?"
        ),
        {
            "A": "Nearly one-fourth",
            "B": "Over three-quarters",
            "C": "Less than one-tenth",
            "D": "Exactly half",
        },
        "A",
        "Paragraph (1) states 'nearly a quarter of exposed urban surfaces'.",
    ),
    48: (
        (
            "Which of the following is mentioned as part of a green roof's layered structure in "
            "paragraph (2)?"
        ),
        {
            "A": "A waterproof membrane and drought-tolerant plants",
            "B": "Heavy clay bricks and metal fences",
            "C": "Underground drainage pumps",
            "D": "Reflective glass panels",
        },
        "A",
        (
            "Paragraph (2) lists a waterproof membrane, lightweight soil substrate, and "
            "drought-tolerant plants."
        ),
    ),
    49: (
        'In paragraph (3), the phrase "act as sponges" highlights green roofs\' ability to:',
        {
            "A": "Absorb and temporarily hold rainwater",
            "B": "Wash street pavements automatically",
            "C": "Increase water pressure in city pipes",
            "D": "Change rain into drinking water",
        },
        "A",
        "Just like sponges, green roofs retain stormwater and reduce peak runoff.",
    ),
    50: (
        (
            "According to paragraph (4), why can green roofs still be financially worthwhile "
            "despite higher initial costs?"
        ),
        {
            "A": "They save cooling energy and help roof membranes last longer",
            "B": "They require no structural checks before installation",
            "C": "They eliminate the need for air conditioning in winter",
            "D": "They receive free water from nearby buildings",
        },
        "A",
        (
            "Paragraph (4) cites savings in air-conditioning electricity and extended membrane "
            "lifespan."
        ),
    ),
    51: (
        'Which word is closest in meaning to "offset" in paragraph (4)?',
        {"A": "Compensate for", "B": "Multiply", "C": "Delay", "D": "Double"},
        "A",
        "Here 'offset' means balance out or compensate for the initial investment.",
    ),
    52: (
        "What can be inferred about conventional dark asphalt roofs from the passage?",
        {
            "A": "They heat up faster under sunlight than vegetated roofs",
            "B": "They retain more stormwater than soil layers",
            "C": "They always last longer than green roofs",
            "D": "They require structural reinforcement every year",
        },
        "A",
        (
            "Paragraphs (1)-(2) note dark asphalt absorbs solar heat whereas green roofs keep "
            "temperatures lower."
        ),
    ),
    53: (
        "What is the best title for the passage?",
        {
            "A": "Protective Value and Revival of Coastal Mangroves",
            "B": "Deep-Sea Fishing Techniques in Tropical Waters",
            "C": "Building Concrete Seawalls on Sandy Beaches",
            "D": "Freshwater Farming in Mountain Valleys",
        },
        "A",
        "The passage centers on mangrove ecology, loss, restoration, and community benefits.",
    ),
    54: (
        "According to paragraph (1), mangrove roots benefit young marine animals by:",
        {
            "A": "Creating sheltered nursery habitats",
            "B": "Raising water salinity rapidly",
            "C": "Blocking river sediment from reaching estuaries",
            "D": "Chasing away all shoreline birds",
        },
        "A",
        "Paragraph (1) mentions 'sheltered nurseries for young fish, crabs, and shrimp'.",
    ),
    55: (
        "In paragraph (2), what happened after large stretches of mangroves were cleared?",
        {
            "A": "Coastal villages faced greater risk from storm surges and erosion",
            "B": "Shorelines stabilized naturally without root systems",
            "C": "Aquaculture ponds immediately produced twice as much",
            "D": "Storms stopped reaching tropical estuaries",
        },
        "A",
        "Loss of the natural barrier left nearby villages more vulnerable.",
    ),
    56: (
        (
            "Why do single-species planting efforts along open beaches often fail, according to "
            "paragraph (3)?"
        ),
        {
            "A": "They overlook natural tidal flow and soil salinity matching",
            "B": "Mangrove seedlings grow only in cold polar oceans",
            "C": "Estuaries lack enough sunlight for trees",
            "D": "Local varieties cannot survive in saltwater",
        },
        "A",
        (
            "Paragraph (3) explains successful projects restore tidal flow and match local "
            "species to salinity."
        ),
    ),
    57: (
        'The word "thrive" in paragraph (1) is closest in meaning to:',
        {"A": "Grow vigorously", "B": "Disappear", "C": "Freeze", "D": "Shrink"},
        "A",
        "'Thrive' means flourish or grow well in a habitat.",
    ),
    58: (
        "What does paragraph (4) suggest about conservation and coastal livelihoods?",
        {
            "A": "Sustainable practices allow ecology and local income to support each other",
            "B": "Eco-tourism requires cutting down older mangrove forests",
            "C": "Shellfish farming must be banned everywhere along estuaries",
            "D": "Communities must relocate inland to protect shorelines",
        },
        "A",
        (
            "Paragraph (4) states 'shoreline protection and local livelihoods can reinforce each "
            "other'."
        ),
    ),
    59: (
        'In paragraph (2), the phrase "this natural barrier" refers to:',
        {
            "A": "Mangrove forest cover",
            "B": "Aquaculture expansion",
            "C": "Coastal roads",
            "D": "River sediment",
        },
        "A",
        "It refers back to the mangrove cover mentioned in the first sentence.",
    ),
    60: (
        "Which statement is NOT supported by the passage?",
        {
            "A": "Every mangrove tree species grows equally well in any soil salinity.",
            "B": "Mangroves help anchor muddy shoreline sediment.",
            "C": "Tidal hydrology plays an important role in restoration.",
            "D": "Eco-tourism can coexist with mangrove conservation.",
        },
        "A",
        "Paragraph (3) specifically stresses matching tree varieties to soil salinity.",
    ),
    73: (
        (
            "Gọi $x, y$ lần lượt là số đèn loại A và loại B sản xuất trong tuần ($x, y \\ge 0$). "
            "Hệ bất phương trình ràng buộc thời gian là:"
        ),
        {
            "A": (
                "$\\begin{cases} 2x + y \\le 40 \\\\ x + 2y \\le 35 "
                "\\\\ x \\ge 0, y \\ge 0 \\end{cases}$"
            ),
            "B": (
                "$\\begin{cases} x + 2y \\le 40 \\\\ 2x + y \\le 35 "
                "\\\\ x \\ge 0, y \\ge 0 \\end{cases}$"
            ),
            "C": (
                "$\\begin{cases} 2x + y \\ge 40 \\\\ x + 2y \\ge 35 "
                "\\\\ x \\ge 0, y \\ge 0 \\end{cases}$"
            ),
            "D": (
                "$\\begin{cases} 2x + 2y \\le 40 \\\\ x + y \\le 35 "
                "\\\\ x \\ge 0, y \\ge 0 \\end{cases}$"
            ),
        },
        "A",
        "Tổng giờ gia công khung là $2x + y \\le 40$ và tổng giờ lắp mạch là $x + 2y \\le 35$.",
    ),
    74: (
        "Biết lãi mỗi đèn loại A là $120$ nghìn đồng và loại B là $150$ nghìn đồng. "
        "Lợi nhuận tối đa trong tuần (nghìn đồng) là:",
        {"A": "$3\\,300$", "B": "$2\\,400$", "C": "$2\\,625$", "D": "$3\\,000$"},
        "A",
        "Miền nghiệm có các đỉnh $(0;0), (20;0), (0;17{,}5), (15;10)$; "
        "tại $(15; 10)$ lợi nhuận đạt cực đại $15 \\cdot 120 + 10 \\cdot 150 = 3\\,300$ nghìn"
        " đồng.",
    ),
    75: (
        "Công sai $d$ của cấp số cộng $(u_n)$ là:",
        {"A": "$3$", "B": "$2$", "C": "$6$", "D": "$4$"},
        "A",
        "Trừ hai đẳng thức theo vế: $(u_2 - u_1) + (u_5 - u_4) = 2d = 6 \\Rightarrow d = 3$.",
    ),
    76: (
        "Số hạng đầu $u_1$ của cấp số cộng đã cho bằng:",
        {"A": "$2{,}5$", "B": "$3$", "C": "$4$", "D": "$1{,}5$"},
        "A",
        "Ta có $u_1 + (u_1 + 3d) = 14 \\Leftrightarrow 2u_1 + 9 = 14 \\Rightarrow u_1 = 2{,}5$.",
    ),
    77: (
        "Khoảng cách từ điểm $A(1; -2; 3)$ đến mặt phẳng $(P)$ bằng:",
        {"A": "$\\frac{7}{3}$", "B": "$\\frac{5}{3}$", "C": "$3$", "D": "$\\frac{8}{3}$"},
        "A",
        (
            "$d(A, (P)) = \\frac{|2(1) - (-2) + 2(3) - 3|}{\\sqrt{2^2 + (-1)^2 + 2^2}} = "
            "\\frac{7}{3}$."
        ),
    ),
    78: (
        "Mặt phẳng đi qua $A$ và vuông góc với cả $(P)$ lẫn $(Q)$ có vectơ pháp tuyến là:",
        {"A": "$(-3; 4; 5)$", "B": "$(3; 4; 5)$", "C": "$(-3; -4; 5)$", "D": "$(2; -1; 2)$"},
        "A",
        "Tích có hướng $\\vec{n}_P \\times \\vec{n}_Q = (2;-1;2) \\times (1;2;-1) = (-3; 4; 5)$.",
    ),
    79: (
        "Với $m = 2$, giá trị lớn nhất của hàm số trên đoạn $[0; 2]$ bằng:",
        {"A": "$4$", "B": "$2$", "C": "$0$", "D": "$6$"},
        "A",
        "Hàm đạt cực tiểu tại $x = 1$ bằng $0$; $y(0) = 2$, $y(2) = 8 - 6 + 2 = 4$.",
    ),
    80: (
        (
            "Tập tất cả giá trị $m$ để phương trình $x^3 - 3x + m = 0$ có $3$ nghiệm thực phân "
            "biệt là:"
        ),
        {"A": "$(-2; 2)$", "B": "$[-2; 2]$", "C": "$(-\\infty; -2)$", "D": "$(2; +\\infty)$"},
        "A",
        (
            "Giá trị cực đại là $2 + m$, cực tiểu là $-2 + m$; có $3$ nghiệm khi $(-2+m)(2+m) < 0"
            " \\Leftrightarrow -2 < m < 2$."
        ),
    ),
    81: (
        "Có bao nhiêu giá trị nguyên của $m$ để đồ thị hàm số cắt trục hoành tại đúng $1$ điểm?",
        {"A": "Vô số giá trị nguyên", "B": "$3$", "C": "$5$", "D": "$4$"},
        "A",
        "Khi $m > 2$ hoặc $m < -2$ đồ thị cắt trục hoành tại đúng $1$ điểm.",
    ),
    82: (
        "Chọn ngẫu nhiên $1$ sản phẩm từ Kho I. Xác suất để sản phẩm đó bị lỗi là:",
        {"A": "$0{,}2$", "B": "$0{,}25$", "C": "$0{,}8$", "D": "$0{,}15$"},
        "A",
        "Xác suất bằng $\\frac{3}{12 + 3} = \\frac{3}{15} = 0{,}2$.",
    ),
    83: (
        "Chọn ngẫu nhiên $2$ sản phẩm từ Kho I. Xác suất để cả $2$ sản phẩm đều đạt chuẩn là:",
        {
            "A": "$\\frac{22}{35}$",
            "B": "$\\frac{12}{35}$",
            "C": "$\\frac{4}{5}$",
            "D": "$\\frac{11}{35}$",
        },
        "A",
        "$P = \\frac{C_{12}^2}{C_{15}^2} = \\frac{66}{105} = \\frac{22}{35}$.",
    ),
    84: (
        (
            "Chọn ngẫu nhiên một kho với xác suất như nhau rồi lấy ra $1$ sản phẩm. Xác suất lấy "
            "được sản phẩm lỗi là:"
        ),
        {"A": "$0{,}2$", "B": "$0{,}25$", "C": "$0{,}3$", "D": "$0{,}1$"},
        "A",
        "$P = \\frac{1}{2}\\cdot\\frac{3}{15} + \\frac{1}{2}\\cdot\\frac{4}{20} = 0{,}2$.",
    ),
    85: (
        "Tọa độ trọng tâm $G$ của tam giác $ABC$ là:",
        {"A": "$(4; 3)$", "B": "$(3; 4)$", "C": "$(6; 4)$", "D": "$(4; 2)$"},
        "A",
        "$x_G = \\frac{1+4+7}{3} = 4$, $y_G = \\frac{2+6+1}{3} = 3$.",
    ),
    86: (
        "Độ dài đoạn thẳng $AB$ bằng:",
        {"A": "$5$", "B": "$\\sqrt{13}$", "C": "$7$", "D": "$\\sqrt{29}$"},
        "A",
        "$AB = \\sqrt{(4-1)^2 + (6-2)^2} = \\sqrt{9 + 16} = 5$.",
    ),
    87: (
        "Tọa độ điểm $D$ sao cho tứ giác $ABCD$ là hình bình hành là:",
        {"A": "$(4; -3)$", "B": "$(10; 5)$", "C": "$(-2; 7)$", "D": "$(4; 3)$"},
        "A",
        (
            "$\\overrightarrow{AB} = \\overrightarrow{DC} \\Rightarrow D = A + C - B = (1+7-4; "
            "2+1-6) = (4; -3)$."
        ),
    ),
    88: (
        "Thể tích khối chóp $S.ABCD$ bằng:",
        {"A": "$\\frac{a^3}{3}$", "B": "$a^3$", "C": "$\\frac{a^3}{2}$", "D": "$\\frac{a^3}{6}$"},
        "A",
        "$V = \\frac{1}{3} S_{ABCD} \\cdot SA = \\frac{1}{3}a^2 \\cdot a = \\frac{a^3}{3}$.",
    ),
    89: (
        "Góc giữa đường thẳng $SC$ và mặt đáy $(ABCD)$ có tang bằng:",
        {"A": "$\\frac{\\sqrt{2}}{2}$", "B": "$1$", "C": "$\\sqrt{2}$", "D": "$\\frac{1}{2}$"},
        "A",
        "$\\tan\\widehat{SCA} = \\frac{SA}{AC} = \\frac{a}{a\\sqrt{2}} = \\frac{\\sqrt{2}}{2}$.",
    ),
    90: (
        "Khoảng cách từ điểm $A$ đến mặt phẳng $(SBC)$ bằng:",
        {
            "A": "$\\frac{a\\sqrt{2}}{2}$",
            "B": "$a$",
            "C": "$\\frac{a\\sqrt{3}}{3}$",
            "D": "$\\frac{a}{2}$",
        },
        "A",
        (
            "Trong tam giác vuông $SAB$ vuông cân tại $A$, đường cao $AH = \\frac{a\\sqrt{2}}{2}$"
            " vuông góc với $(SBC)$."
        ),
    ),
    91: (
        "Có thể xếp được thứ tự hợp lệ nào sau đây từ vị trí $1$ đến $5$?",
        {
            "A": "$D, A, C, E, B$",
            "B": "$E, A, C, D, B$",
            "C": "$D, B, E, A, C$",
            "D": "$A, C, B, D, E$",
        },
        "A",
        "Thứ tự $D, A, C, E, B$ thỏa mãn $A$ ngay trước $C$, $B$ sau $D$, và $E$ ở vị trí $4$.",
    ),
    92: (
        (
            "Nếu báo cáo $E$ được xếp ở vị trí thứ $2$ thì cặp báo cáo $(A, C)$ phải đứng ở vị "
            "trí nào?"
        ),
        {"A": "$(3, 4)$", "B": "$(1, 2)$", "C": "$(2, 3)$", "D": "$(4, 5)$"},
        "A",
        (
            "$A$ ngay trước $C$ và $B$ phải sau $D$, nên $D$ ở vị trí $1$, $(A, C)$ ở $(3, 4)$ và"
            " $B$ ở vị trí $5$."
        ),
    ),
    93: (
        "Điều nào sau đây luôn đúng?",
        {
            "A": "Báo cáo $B$ không bao giờ đứng ở vị trí thứ $1$.",
            "B": "Báo cáo $A$ luôn đứng ở vị trí thứ $1$.",
            "C": "Báo cáo $D$ luôn đứng ở vị trí thứ $4$.",
            "D": "Báo cáo $C$ luôn đứng ở vị trí cuối cùng.",
        },
        "A",
        "Vì $B$ phải trình bày sau $D$ nên $B$ không thể đứng đầu tiên.",
    ),
    94: (
        "Tổ hợp $4$ thành viên nào sau đây hợp lệ?",
        {
            "A": "$\\{M, H, K, N\\}$",
            "B": "$\\{M, P, H, L\\}$",
            "C": "$\\{M, N, P, H\\}$",
            "D": "$\\{M, K, L, H\\}$",
        },
        "A",
        "$\\{M, H, K, N\\}$ có $2$ nữ ($H, K$), không có $P$ khi có $M$, và cả $K, N$ cùng có mặt.",
    ),
    95: (
        "Nếu $K$ được chọn vào đội và $P$ cũng được chọn thì điều nào phải đúng?",
        {
            "A": "$N$ cũng phải được chọn và $M$ không được chọn",
            "B": "$M$ phải được chọn",
            "C": "Đội có nhiều nhất $1$ bạn nữ",
            "D": "$H$ bắt buộc phải bị loại",
        },
        "A",
        "$K$ đi kèm $N$, và có $P$ thì không được chọn $M$.",
    ),
    96: (
        "Nếu $M$ và $P$ đều không được chọn thì khẳng định nào sau đây đúng?",
        {
            "A": "Cả $K$ và $N$ đều bắt buộc phải được chọn",
            "B": "Chỉ $K$ được chọn, $N$ bị loại",
            "C": "Chỉ chọn được tối đa $3$ thành viên",
            "D": "$L$ không thể có mặt trong đội",
        },
        "A",
        "Chỉ còn $4$ người khả dụng là $N, H, K, L$, nên tất cả đều phải được chọn.",
    ),
    97: (
        "Số lượng xe của hãng X bán ra năm $2025$ tăng bao nhiêu phần trăm so với năm $2020$?",
        {"A": "$150\\%$", "B": "$250\\%$", "C": "$120\\%$", "D": "$60\\%$"},
        "A",
        "Tỷ lệ tăng $= \\frac{75 - 30}{30} \\cdot 100\\% = 150\\%$.",
    ),
    98: (
        "Thị phần của hãng Y trên toàn thị trường vào năm $2025$ là bao nhiêu phần trăm?",
        {"A": "$24\\%$", "B": "$30\\%$", "C": "$20\\%$", "D": "$28\\%$"},
        "A",
        "Thị phần hãng Y năm $2025$ là $\\frac{60}{250} \\cdot 100\\% = 24\\%$.",
    ),
    99: (
        "So với năm $2020$, thị phần của hãng X vào năm $2025$ đã thay đổi như thế nào?",
        {
            "A": "Tăng $10$ điểm phần trăm",
            "B": "Giảm $10$ điểm phần trăm",
            "C": "Tăng $15$ điểm phần trăm",
            "D": "Không đổi",
        },
        "A",
        (
            "Năm $2020$ là $\\frac{30}{150} = 20\\%$; năm $2025$ là $\\frac{75}{250} = 30\\%$, "
            "tăng $10$ điểm phần trăm."
        ),
    ),
    100: (
        "Nhóm chứa trung vị của mẫu số liệu trên là:",
        {"A": "$[30; 40)$", "B": "$[20; 30)$", "C": "$[40; 50)$", "D": "$[10; 20)$"},
        "A",
        "Tần số tích lũy đến hết $[20; 30)$ là $35 < 50$, sang $[30; 40)$ đạt $75 \\ge 50$.",
    ),
    101: (
        "Giá trị trung vị (phút) của $100$ thí sinh xấp xỉ:",
        {"A": "$33{,}75$", "B": "$31{,}25$", "C": "$35{,}00$", "D": "$36{,}50$"},
        "A",
        "$M_e = 30 + \\frac{50 - 35}{40} \\cdot 10 = 33{,}75$ phút.",
    ),
    102: (
        "Số thí sinh hoàn thành bài thi trong thời gian dưới $30$ phút chiếm tỉ lệ bao nhiêu?",
        {"A": "$35\\%$", "B": "$25\\%$", "C": "$40\\%$", "D": "$65\\%$"},
        "A",
        "Có $10 + 25 = 35$ thí sinh trên tổng $100$ thí sinh, chiếm $35\\%$.",
    ),
    103: (
        (
            "Khi hòa tan thêm urea vào dung dịch ở $25^{\\circ}\\text{C}$, áp suất hơi bão hòa "
            "của dung dịch thay đổi như thế nào?"
        ),
        {
            "A": "Giảm đi vì phần mol của nước giảm",
            "B": "Tăng lên bằng áp suất hơi của urea",
            "C": "Không đổi ở mọi nồng độ",
            "D": "Luôn vượt quá $24\\text{ mmHg}$",
        },
        "A",
        (
            "Khi $n_{\\text{ct}}$ tăng thì $\\frac{n_{\\text{dm}}}{n_{\\text{dm}} + "
            "n_{\\text{ct}}}$ giảm nên $P$ giảm."
        ),
    ),
    104: (
        (
            "Hòa tan $18\\text{ g}$ glucose vào $180\\text{ g}$ nước ở $25^{\\circ}\\text{C}$. Áp"
            " suất hơi bão hòa của dung dịch xấp xỉ:"
        ),
        {
            "A": "$23{,}76\\text{ mmHg}$",
            "B": "$24{,}00\\text{ mmHg}$",
            "C": "$21{,}60\\text{ mmHg}$",
            "D": "$22{,}80\\text{ mmHg}$",
        },
        "A",
        (
            "$n_{\\text{dm}} = 10\\text{ mol}$, $n_{\\text{ct}} = 0{,}1\\text{ mol} \\Rightarrow "
            "P = 24 \\cdot \\frac{10}{10{,}1} \\approx 23{,}76\\text{ mmHg}$."
        ),
    ),
    105: (
        (
            "Nếu cùng hòa tan $0{,}1\\text{ mol}$ glucose hoặc $0{,}1\\text{ mol}$ urea vào "
            "$180\\text{ g}$ nước ở cùng nhiệt độ, độ giảm áp suất hơi bão hòa giữa hai dung "
            "dịch:"
        ),
        {
            "A": "Bằng nhau vì cùng số mol chất tan không điện ly",
            "B": "Dung dịch glucose giảm mạnh hơn $3$ lần",
            "C": "Dung dịch urea giảm ít hơn $3$ lần",
            "D": "Không thể so sánh",
        },
        "A",
        "Công thức phụ thuộc vào số mol chất tan không bay hơi và không điện ly.",
    ),
    106: (
        "Photon của ánh sáng nào sau đây mang năng lượng nhỏ nhất?",
        {
            "A": "Ánh sáng đỏ ($0{,}76\\text{ }\\mu\\text{m}$)",
            "B": "Ánh sáng tím ($0{,}38\\text{ }\\mu\\text{m}$)",
            "C": "Ánh sáng lục ($0{,}55\\text{ }\\mu\\text{m}$)",
            "D": "Ánh sáng lam ($0{,}45\\text{ }\\mu\\text{m}$)",
        },
        "A",
        (
            "Năng lượng $\\varepsilon = \\frac{hc}{\\lambda}$ tỉ lệ nghịch với bước sóng nên bước"
            " sóng dài nhất có năng lượng nhỏ nhất."
        ),
    ),
    107: (
        (
            "Năng lượng của một photon ánh sáng tím có bước sóng $0{,}38\\text{ }\\mu\\text{m}$ "
            "gần nhất với:"
        ),
        {
            "A": "$3{,}27\\text{ eV}$",
            "B": "$1{,}63\\text{ eV}$",
            "C": "$2{,}45\\text{ eV}$",
            "D": "$4{,}80\\text{ eV}$",
        },
        "A",
        (
            "$\\varepsilon = \\frac{6{,}625 \\cdot 10^{-34} \\cdot 3 \\cdot 10^8}{0{,}38 \\cdot "
            "10^{-6} \\cdot 1{,}6 \\cdot 10^{-19}} \\approx 3{,}27\\text{ eV}$."
        ),
    ),
    108: (
        "Tần số của bức xạ đỏ có bước sóng $0{,}75\\text{ }\\mu\\text{m}$ trong chân không bằng:",
        {
            "A": "$4{,}0 \\cdot 10^{14}\\text{ Hz}$",
            "B": "$2{,}5 \\cdot 10^{14}\\text{ Hz}$",
            "C": "$7{,}5 \\cdot 10^{14}\\text{ Hz}$",
            "D": "$4{,}0 \\cdot 10^{13}\\text{ Hz}$",
        },
        "A",
        (
            "$f = \\frac{c}{\\lambda} = \\frac{3 \\cdot 10^8}{0{,}75 \\cdot 10^{-6}} = 4{,}0 "
            "\\cdot 10^{14}\\text{ Hz}$."
        ),
    ),
    109: (
        (
            "Ở thí nghiệm trên, tốc độ thủy phân tinh bột bởi enzyme amylase đạt cực đại tại ống "
            "nghiệm nào?"
        ),
        {
            "A": "Ống nghiệm 3 ($37^{\\circ}\\text{C}$)",
            "B": "Ống nghiệm 1 ($10^{\\circ}\\text{C}$)",
            "C": "Ống nghiệm 4 ($55^{\\circ}\\text{C}$)",
            "D": "Ống nghiệm 5 ($80^{\\circ}\\text{C}$)",
        },
        "A",
        "Tại $37^{\\circ}\\text{C}$, lượng tinh bột thủy phân cao nhất ($19{,}8\\text{ mg}$).",
    ),
    110: (
        (
            "Vì sao ở $80^{\\circ}\\text{C}$ lượng tinh bột bị thủy phân giảm xuống chỉ còn "
            "$0{,}5\\text{ mg}$?"
        ),
        {
            "A": "Nhiệt độ cao làm biến tính cấu trúc không gian của enzyme",
            "B": "Nhiệt độ cao làm tinh bột chuyển hóa hoàn toàn trước khi đo",
            "C": "Enzyme hoạt động mạnh hơn ở $80^{\\circ}\\text{C}$ nhưng bị bay hơi",
            "D": "Cơ chất tinh bột bị đông đặc hoàn toàn ở $80^{\\circ}\\text{C}$",
        },
        "A",
        "Enzyme có bản chất protein nên bị biến tính mất hoạt tính ở nhiệt độ quá cao.",
    ),
    111: (
        (
            "Từ bảng kết quả, nhận xét nào đúng về mối quan hệ giữa nhiệt độ và hoạt tính enzyme "
            "amylase?"
        ),
        {
            "A": "Hoạt tính tăng dần đến ngưỡng tối ưu rồi giảm mạnh khi quá nóng",
            "B": "Nhiệt độ càng tăng thì hoạt tính enzyme càng tăng vô hạn",
            "C": "Hoạt tính enzyme không phụ thuộc vào nhiệt độ môi trường",
            "D": (
                "Ở $10^{\\circ}\\text{C}$ enzyme bị biến tính vĩnh viễn "
                "giống $80^{\\circ}\\text{C}$"
            ),
        },
        "A",
        (
            "Hoạt tính tăng từ $10^{\\circ}\\text{C}$ đến $37^{\\circ}\\text{C}$ rồi giảm nhanh ở"
            " $55^{\\circ}\\text{C}$ và $80^{\\circ}\\text{C}$."
        ),
    ),
    112: (
        (
            "Theo tiêu chuẩn trong đoạn thông tin, một quốc gia có tỉ lệ người từ $65$ tuổi trở "
            "lên đạt $10\\%$ thuộc giai đoạn nào?"
        ),
        {
            "A": "Giai đoạn già hóa dân số",
            "B": "Giai đoạn dân số trẻ",
            "C": "Giai đoạn dân số già",
            "D": "Giai đoạn cơ cấu dân số vàng tuyệt đối",
        },
        "A",
        "Tỉ lệ từ $7\\%$ đến dưới $14\\%$ thuộc giai đoạn già hóa dân số.",
    ),
    113: (
        "Nguyên nhân chính dẫn đến tỉ trọng người cao tuổi tăng nhanh trong cơ cấu dân số là gì?",
        {
            "A": "Mức sinh giảm kết hợp với tuổi thọ trung bình tăng",
            "B": "Tỉ lệ sinh tăng đột biến trong nhiều năm liền",
            "C": "Tuổi thọ trung bình giảm do y tế kém",
            "D": "Lao động nhập cư tăng gấp đôi hằng năm",
        },
        "A",
        (
            "Đoạn văn nêu rõ nguyên nhân là mức sinh giảm liên tục và tuổi thọ trung bình được "
            "cải thiện."
        ),
    ),
    114: (
        "Hệ quả kinh tế - xã hội dài hạn nào thường gắn liền với quá trình già hóa dân số nhanh?",
        {
            "A": "Áp lực tăng chi phí an sinh xã hội và thiếu hụt lao động trẻ",
            "B": "Dư thừa quá mức lực lượng lao động phổ thông trẻ tuổi",
            "C": "Chi phí chăm sóc y tế người cao tuổi giảm về $0$",
            "D": "Nhu cầu trường tiểu học tăng gấp nhiều lần",
        },
        "A",
        "Già hóa dân số kéo theo gánh nặng hưu trí, y tế và thu hẹp lực lượng lao động.",
    ),
    115: (
        "Cuộc Cách mạng công nghiệp lần thứ nhất khởi phát đầu tiên ở quốc gia nào?",
        {"A": "Nước Anh", "B": "Nước Pháp", "C": "Hoa Kỳ", "D": "Nước Đức"},
        "A",
        "Đoạn thông tin nêu rõ cuộc cách mạng khởi phát tại nước Anh vào nửa sau thế kỷ XVIII.",
    ),
    116: (
        (
            "Phát minh tiêu biểu nào đã tạo bước ngoặt thay thế sức người và sức nước bằng động "
            "cơ nhiệt trong công nghiệp?"
        ),
        {
            "A": "Máy hơi nước của James Watt",
            "B": "Động cơ phản lực",
            "C": "Mạng thông tin vệ tinh",
            "D": "Tế bào quang điện mặt trời",
        },
        "A",
        "Máy hơi nước của James Watt là phát minh trung tâm của cuộc cách mạng lần thứ nhất.",
    ),
    117: (
        (
            "Chuyển biến cơ bản nhất về phương thức sản xuất mà cuộc Cách mạng công nghiệp lần "
            "thứ nhất mang lại là gì?"
        ),
        {
            "A": "Chuyển từ lao động thủ công sang cơ khí hóa bằng máy móc",
            "B": "Chuyển từ tự động hóa số sang nông nghiệp du mục",
            "C": "Xóa bỏ hoàn toàn ngành dệt may và luyện kim",
            "D": "Tách rời hoàn toàn khoa học khỏi sản xuất",
        },
        "A",
        "Cơ khí hóa bằng máy móc thay thế lao động thủ công là bản chất của cuộc cách mạng này.",
    ),
    118: (
        (
            "Hành động trích $5\\%$ lợi nhuận trồng cây xanh quanh khu công nghiệp thể hiện loại "
            "trách nhiệm xã hội nào?"
        ),
        {
            "A": "Trách nhiệm bảo vệ môi trường và cộng đồng (nhân văn/đạo đức)",
            "B": "Trách nhiệm trốn tránh kiểm định chất lượng",
            "C": "Trách nhiệm độc quyền phân phối",
            "D": "Trách nhiệm cắt giảm phúc lợi người lao động",
        },
        "A",
        "Chủ động đóng góp cải thiện môi trường địa phương thể hiện trách nhiệm xã hội tích cực.",
    ),
    119: (
        (
            "Việc công bố minh bạch nguồn gốc nguyên liệu trên bao bì giúp doanh nghiệp đạt được "
            "lợi ích gì?"
        ),
        {
            "A": "Xây dựng niềm tin và thu hút khách hàng trung thành",
            "B": "Giảm chất lượng sản phẩm để hạ giá",
            "C": "Miễn mọi nghĩa vụ thuế nhà nước",
            "D": "Giảm độ nhận diện thương hiệu trên thị trường",
        },
        "A",
        "Minh bạch thông tin tạo dựng uy tín, củng cố niềm tin của người tiêu dùng.",
    ),
    120: (
        "Bài học kinh doanh rút ra từ trường hợp của doanh nghiệp An Bình là:",
        {
            "A": (
                "Thực hiện trách nhiệm xã hội bền vững có thể song hành với "
                "tăng trưởng uy tín và thị trường"
            ),
            "B": "Chi phí bảo vệ môi trường luôn làm doanh nghiệp phá sản",
            "C": "Doanh nghiệp nhỏ không cần quan tâm đến minh bạch nguồn gốc",
            "D": "Trách nhiệm xã hội chỉ dành cho tổ chức phi lợi nhuận",
        },
        "A",
        "Doanh nghiệp vừa đóng góp cộng đồng vừa mở rộng được hợp tác và giữ chân khách hàng.",
    ),
}


def _vact_demo_passage(group) -> dict:
    item = _VACT_PASSAGES[group.id]
    return {
        "id": group.id,
        "heading": item["heading"],
        "text": item["text"],
        "table": item["table"],
    }


def _vact_demo_question(group, num: int) -> dict:
    stem, choices, answer, solution = (
        _VACT_GROUP_QUESTIONS[num] if group.shared else _VACT_STANDALONE[num]
    )
    return {
        "id": f"q{num}",
        "stem": stem,
        "choices": choices,
        "answer": answer,
        "solution": solution,
        "passage_id": group.id if group.shared else None,
        "illustration_request": None,
    }


async def run_demo_job(request, output: Path, progress, *, is_vact: bool) -> dict:
    """Write valid local exam artifacts without calling any external AI provider."""
    output.mkdir(parents=True, exist_ok=True)
    internal = output / "_internal" / "revision_1"
    internal.mkdir(parents=True, exist_ok=True)

    if is_vact:
        batches = vact_template.batches()
        passages = []
        questions = []
        for batch in batches:
            progress("composer", batch.id, 1)
            await asyncio.sleep(0.02)
            for group in batch.groups:
                if group.shared:
                    passages.append(_vact_demo_passage(group))
                for num in range(group.start, group.end + 1):
                    questions.append(_vact_demo_question(group, num))
        progress("solver", batches[0].id, 1)
        await asyncio.sleep(0.02)
        progress("reviewer", None, 1)
        solver_entries = [
            {
                "question_id": q["id"],
                "answer": q["answer"],
                "reasoning": "Đã đối chiếu đáp án độc lập.",
                "status": "solved",
            }
            for q in questions
        ]
        answers_payload = {
            "status": "pending_human_review",
            "revision": 1,
            "composer": questions,
            "passages": passages,
            "independent_solver": {"entries": solver_entries},
        }
    else:
        for part in ("P1", "P2", "P3"):
            progress("composer", part, 1)
            await asyncio.sleep(0.02)
        questions = _thpt_demo_questions(request.slots)
        progress("solver", None, 1)
        await asyncio.sleep(0.02)
        progress("reviewer", None, 1)
        solver_entries = [
            {
                "question_id": q["id"],
                "answer": q["answer"] or "Đúng / Đúng / Sai / Đúng",
                "reasoning": "Đã đối chiếu đáp án độc lập.",
                "status": "solved",
            }
            for q in questions
        ]
        answers_payload = {
            "status": "pending_human_review",
            "revision": 1,
            "composer": questions,
            "independent_solver": {"entries": solver_entries},
        }

    (internal / "illustrations.json").write_text(
        json.dumps({"drawings": []}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output / "dap_an_va_loi_giai.json").write_text(
        json.dumps(answers_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return {
        "execution_status": "completed",
        "revision": 1,
        "demo_mode": True,
    }


def regenerate_demo_question(old: dict, instruction: str) -> dict:
    """Return a clean revised THPT question locally without API calls."""
    note = instruction.strip()[:120]
    if note:
        return {
            **old,
            "solution": f"{old['solution']} (Đã cập nhật theo yêu cầu: {note})",
        }
    return {**old}

# ASTRA — Kế Hoạch Thiết Kế & Đặc Tả UI/UX

**Dự án:** ASTRA — Hệ thống tạo đề thi tự động bằng AI, dành cho giáo viên phổ thông.  
**Nền tảng:** Desktop (màn hình ngang 16:9, từ 1366×768 đến 1920×1080).

---

## 1. Tổng Quan

### ASTRA làm gì?

ASTRA là một ứng dụng web giúp giáo viên soạn đề thi nhanh bằng cách chat với AI. Giáo viên mô tả yêu cầu (môn, chủ đề, số câu, độ khó...), hệ thống tự tạo ra đề thi hoàn chỉnh gồm câu hỏi + đáp án + barem, có thể xuất thẳng ra file Word hoặc PDF để in.

Phía sau là một hệ thống gồm nhiều AI agent phối hợp: một agent soạn câu hỏi, một agent giải độc lập để kiểm tra đáp án, một agent so sánh kết quả và đánh dấu câu cần xem lại. Toàn bộ quá trình này **giáo viên không cần biết** — họ chỉ thấy đề đang hiện ra từng câu trên màn hình.

### Giao diện giải quyết vấn đề gì?

Hệ thống AI chạy mất 2–5 phút cho một đề 40 câu. Nếu chỉ hiện "đang xử lý..." thì giáo viên không biết có chuyện gì đang xảy ra. Giải pháp: **hiển thị từng câu ngay khi nó xong**, thay vì đợi xong tất cả mới show. Giáo viên vừa xem đề hình thành, vừa có thể chat thêm để điều chỉnh.

Giao diện chia đôi màn hình:
- **Bên trái (~38%):** Khung chat để giáo viên ra lệnh, đính kèm tài liệu, theo dõi tiến độ.
- **Bên phải (~62%):** Tờ đề thi đang được điền vào theo thời gian thực.

### Luồng sử dụng (User Flow)

Mới vào → hỏi ngay một câu: **"Bạn muốn tạo đề nhanh?"**

- **Có** → Chọn loại đề (THPTQG / ĐGNL) + môn học → Bắt đầu.
- **Không** → Vào thẳng chế độ Chuyên nghiệp, tự do chat và tùy chỉnh.

---

## 2. Phân Tích: Abstraction (Trừu tượng hóa)

### Vấn đề cần giải quyết

Backend trả về dữ liệu thô: câu hỏi, đáp án, các ký hiệu toán học ở dạng plain text hay cú pháp LaTeX chưa render. Ví dụ:

```
Câu 3: Tính \frac{d}{dx}(x^2 + 3x). Đáp án: A. 2x+3  B. x^2  C. 3x  D. 2x
```

Nếu đổ thẳng ra màn hình, giáo viên thấy một mớ ký tự lộn xộn, không đọc được.

### Abstraction ở đây là gì?

**UI/UX đóng vai trò là tầng phiên dịch** giữa dữ liệu thô của backend và thứ giáo viên cần nhìn thấy.

| | Backend (AI agent) | UI/UX (Frontend) |
|---|---|---|
| **Quan tâm đến** | Câu hỏi đúng chưa? Đáp án có nhất quán không? | Câu hỏi hiển thị đẹp chưa? Font, layout, công thức render đúng chưa? |
| **Không cần biết** | Cách render LaTeX, CSS, font size | Cách agent tạo câu hỏi, cách kiểm tra đáp án |

Backend chỉ cần trả JSON đúng cấu trúc. Frontend nhận JSON đó và xử lý toàn bộ phần hiển thị.

**Input của UI:** JSON thô từ backend — mỗi câu gồm nội dung câu hỏi (có thể chứa LaTeX), 4 đáp án, đáp án đúng, và trạng thái kiểm tra (verified / flagged).

```json
{
  "id": 3,
  "question": "Tính $\\frac{d}{dx}(x^2 + 3x)$.",
  "options": ["$2x + 3$", "$x^2$", "$3x$", "$2x$"],
  "answer": "A",
  "status": "verified"
}
```

**Output của UI:** Câu hỏi được render đẹp — công thức toán hiển thị đúng qua KaTeX, layout chuẩn đề thi, đánh số thứ tự, 4 đáp án xếp thẳng hàng, câu bị "flagged" thì có ghi chú nhẹ bên dưới.

### Tại sao tách biệt này quan trọng?

- AI agent tập trung vào đúng việc của nó: **nội dung đúng**.
- Frontend tập trung vào đúng việc của nó: **hiển thị đẹp**.
- Nếu sau này muốn đổi cách render (ví dụ từ KaTeX sang MathJax, hoặc xuất PDF theo layout khác), chỉ cần sửa frontend — backend không cần đổi gì.

---

## 3. Thiết Kế Giao Diện

### 3.1 Ngôn ngữ thị giác

- **Màu nền:** `#f8fafc` (trắng ngà, không chói).
- **Màu nhấn:** `#10b981` / `#059669` (xanh lá nhạt — baby green).
- **Chữ:** 14–15px cho nội dung, 20–22px cho tiêu đề đề thi, 12px cho nhãn phụ.
- **Bo góc:** 4px–8px — không bo tròn như viên thuốc, không vuông cứng.
- **Không dùng:** màu đỏ/vàng/xanh lá chói như đèn giao thông, hiệu ứng nhấp nháy, chữ khẩu hiệu trên nút bấm.

### 3.2 Màn hình khởi đầu

```
+------------------------------------------------------------------------------------+
|                                                                                    |
|                                      ASTRA                                         |
|                                                                                    |
|                         Bạn muốn tạo đề nhanh?                                    |
|                                                                                    |
|            [ Có, tạo nhanh ]     [ Không, đưa tôi đến chế độ Chuyên nghiệp ]      |
|                                                                                    |
+------------------------------------------------------------------------------------+
```

Chọn **"Có"** → Mở bảng chọn nhanh: loại đề (THPTQG 40 câu / ĐGNL 30 câu) + môn học → Bắt đầu.  
Chọn **"Không"** → Vào thẳng workspace, tự nhập yêu cầu qua chat.

### 3.3 Màn hình làm việc chính

```
+------------------------------------------------------------------------------------------------------------------+
| ASTRA                                                                               [ Xuất Word ]   [ In PDF ]   |
+----------------------------------------------------+-------------------------------------------------------------+
| KHUNG CHAT (Trái ~38%)                             | ĐỀ THI ĐANG TẠO (Phải ~62%)                                 |
|                                                    |                                                             |
| [Lịch sử hội thoại]                                | Trường THPT ...        Mã đề: 001                           |
|                                                    | Môn: Vật lý            Thời gian: 50 phút                   |
| GV: "Soạn đề Vật lý 12, chương Dao động            | ─────────────────────────────────────────                   |
|       và Sóng, 40 câu trắc nghiệm."               | ĐANG TẠO: 12 / 40 CÂU                                       |
|                                                    | ─────────────────────────────────────────                   |
| AI:  "Đang soạn và kiểm tra đồng thời.             | Câu 1: Một vật dao động điều hòa...                         |
|       Câu 1-12 đã xong."                          |   A. Biên độ   B. Chu kỳ   C. Tần số góc   D. Pha           |
|                                                    |   Đáp án: C                                                 |
|                                                    |                                                             |
|                                                    | Câu 2: Một con lắc lò xo k = 100 N/m...                     |
|                                                    |   A. 0.1s   B. 0.2s   C. 0.4s   D. 0.5s                    |
|                                                    |   Đáp án: A                                                 |
|                                                    |                                                             |
|                                                    | Câu 3: [đang kiểm tra...]                                   |
|                                                    |                                                             |
| ─────────────────────────────────────────────────  |                                                             |
| +------------------------------------------------+ |                                                             |
| | Nhập yêu cầu hoặc điều chỉnh...               | |                                                             |
| | [📎 Đính kèm]  [🌐 Web search]            [↑] | |                                                             |
| +------------------------------------------------+ |                                                             |
+----------------------------------------------------+-------------------------------------------------------------+
```

### 3.4 Chi tiết khung Chat (bên trái)

- Tin nhắn hiển thị dạng flat — không dùng bong bóng chat bo tròn lố.
- Ô nhập tự giãn chiều cao theo nội dung (tối đa 5 dòng).
- `Enter` để gửi, `Shift+Enter` để xuống dòng.
- Nút **Đính kèm tài liệu**: upload file giáo án, ma trận (.pdf, .docx).
- Nút **Web search** (toggle): bật/tắt tra cứu thông tin từ mạng.

### 3.5 Chi tiết khung Canvas (bên phải)

- Câu hỏi xuất hiện ngay khi AI agent xong từng câu — không đợi đủ 40 câu.
- Công thức toán/lý/hóa render qua KaTeX (hiển thị đẹp, không lỗi font).
- Câu bị "flagged" (2 agent không đồng ý đáp án): hiện ghi chú xám nhẹ bên dưới + nút `[Sửa]` hoặc `[Đổi câu]`.
- Thanh trên cùng: `[ Xuất Word ]` và `[ In PDF ]`.

---

## 4. Cấu Trúc Component (cho lập trình viên)

```
src/
├── components/
│   ├── OnboardingFork.tsx       # Màn hình hỏi "Tạo nhanh?" — 2 lựa chọn
│   ├── QuickPresetModal.tsx     # Chọn loại đề + môn học nhanh
│   ├── Workspace/
│   │   ├── WorkspaceLayout.tsx  # Chia đôi màn hình 38/62
│   │   ├── ChatPane/
│   │   │   ├── ChatHistory.tsx  # Danh sách tin nhắn flat
│   │   │   └── ChatBar.tsx      # Ô nhập + nút đính kèm + web search + gửi
│   │   └── LiveCanvas/
│   │       ├── CanvasHeader.tsx # Tiêu đề đề, bộ đếm câu, nút xuất
│   │       ├── ExamPaperView.tsx# Tờ đề — nhận stream và render từng câu
│   │       └── QuestionCard.tsx # 1 câu hỏi: render LaTeX, 4 đáp án, flag
│   └── Shared/
│       └── MathRenderer.tsx     # Parse và render công thức bằng KaTeX
├── types/
│   └── exam.ts                  # QuestionItem, ExamPackage, StreamEvent
└── styles/
    └── workspace.css            # Baby green, bo góc nhẹ, không animation thừa
```

---

## 5. Tech Stack

| Mục | Lựa chọn | Lý do |
|---|---|---|
| Framework | React 19 + TypeScript | Kiểm soát kiểu dữ liệu chặt, component rõ ràng |
| Build tool | Vite | Build nhanh, HMR tức thì khi dev |
| Styling | Tailwind CSS | Viết nhanh, dễ nhất quán màu sắc và spacing |
| Toán học | KaTeX | Render LaTeX nhanh, chính xác, không cần server |
| Icons | Lucide React | Icon mảnh, hiện đại, SVG |
| Stream data | Server-Sent Events (SSE) | Nhận từng câu hỏi từ backend ngay khi xong |
| API | REST + `fetch` | Gửi prompt, upload file, yêu cầu sửa câu |
| Xuất file | `docx` lib + CSS Print | Xuất Word và in PDF trực tiếp từ trình duyệt |

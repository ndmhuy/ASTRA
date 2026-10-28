# ASTRA — Kế Hoạch Thiết Kế & Đặc Tả UI/UX (Master Plan)
**Mục tiêu tài liệu:** Bản đặc tả kỹ thuật và kiến trúc giao diện chuẩn xác dành cho kỹ sư / AI lập trình xây dựng lại từ đầu (build from scratch).  
**Dự án:** ASTRA — AI-Powered Exam Generation & Verification  
**Nền tảng:** Desktop-First (Tối ưu cho màn hình ngang giáo viên 16:9, độ phân giải 1366x768 đến 1920x1080).

---

## 1. Triết Lý Thiết Kế & Ngôn Ngữ Thị Giác (Design System)

### 1.1 Thẩm mỹ chủ đạo (Theme & Vibe)
- **Vibe:** Airy (thoáng khí), Open (rộng mở), Minimal (tối giản), Futuristic (hiện đại, tinh tế).
- **Tone màu:** Màu sáng (Light Mode), điểm nhấn **Baby Green** thanh lịch:
  - Màu nền chính (Base background): `#fafbfa` hoặc `#f8fafc` (trắng ngà dịu mắt, không lóa).
  - Màu nền thẻ (Surface): `#ffffff` với viền mảnh 1px (`#e2e8f0` hoặc `#e5e7eb`).
  - Màu Baby Green chủ đạo: `#10b981` (emerald-500) và `#059669` (emerald-600) cho điểm nhấn tương tác.
  - Màu nền phụ nhẹ: `#ecfdf5` (emerald-50) hoặc `#f0fdf4`.
  - Màu chữ: `#0f172a` (slate-900) cho tiêu đề; `#334155` (slate-700) cho nội dung bài đọc; `#64748b` (slate-500) cho chú thích.

### 1.2 Nguyên tắc bài trừ "LLM-ism" (Anti-LLM Patterns)
Tuyệt đối **NÉ TRÁNH** các lỗi giao diện AI thường gặp sau:
1. **Không bo góc quá đà (No Heavy Pill Shapes):** Bỏ các góc bo tròn xoe như viên thuốc hoạt họa. Chỉ dùng bo góc hình học thanh mảnh: `border-radius: 4px` đến tối đa `8px`.
2. **Không câu chốt sáo rỗng trên element:** Tuyệt đối không gắn các khẩu hiệu như *"AI siêu thông minh"*, *"Được hỗ trợ bởi Multi-Agent"*, *"Đột phá công nghệ"* lên các nút bấm hoặc thẻ giao diện.
3. **Không dùng palette Đỏ - Vàng - Xanh lòe loẹt:** Không chia màu trạng thái xanh đỏ như đèn giao thông. Cảnh báo dùng viền xám đậm hoặc một sắc độ nâu ấm nhẹ (`#78350f` viền `#fde68a`), không chói gắt.
4. **Không dùng font chữ khổng lồ:** Chữ có kích thước vừa vặn, thanh lịch như một trang báo cáo khoa học (Body: 14px–15px, Tiêu đề bài thi: 20px–22px, Nhãn nhỏ: 12px).
5. **Hạn chế Animation tối đa (Zero-Distraction Policy):**
   - Không dùng chấm nhấp nháy (pulsing dots), không dùng hiệu ứng nảy (bounce), không dùng vòng quay loader hoa mắt.
   - Trạng thái thay đổi dứt khoát hoặc dùng thanh tiến trình tĩnh lặng để mắt người dùng không phải liên tục đảo qua đảo lại.

---

## 2. Luồng Trải Nghiệm Người Dùng (User Flow)

### Bước 1: Màn hình khởi đầu (The Fork in the Road)
Khi giáo viên mới truy cập vào trang web, không hiển thị một bảng điều khiển phức tạp. Hệ thống hiển thị một khung câu hỏi trực diện ngay chính giữa màn hình:

```
+------------------------------------------------------------------------------------+
|                                                                                    |
|                                       ASTRA                                        |
|                                                                                    |
|                          Bạn muốn tạo đề nhanh?                                    |
|                                                                                    |
|             [ Có, tạo nhanh ]       [ Không, đưa tôi đến chế độ Chuyên nghiệp ]     |
|                                                                                    |
+------------------------------------------------------------------------------------+
```

- **Lựa chọn 1: `[ Có, tạo nhanh ]`**  
  Mở ngay một bảng tùy chọn nhanh (Preset Drawer):
  - Chọn 1 trong các chuẩn có sẵn: `THPT Quốc Gia (40 câu - 50p)` hoặc `Đánh Giá Năng Lực (30 câu)`.
  - Chọn Môn học.
  - Bấm `Bắt đầu` $\rightarrow$ Tự động chuyển thẳng sang Không gian làm việc và kích hoạt sinh đề.
- **Lựa chọn 2: `[ Không, đưa tôi đến chế độ Chuyên nghiệp ]`**  
  Chuyển thẳng vào Không gian làm việc song song (Parallel Workspace), nơi giáo viên toàn quyền kiểm soát qua thanh chat và tài liệu đính kèm.

---

## 3. Kiến Trúc Không Gian Làm Việc Song Song (Parallel Workspace)

Toàn bộ màn hình Desktop được chia làm **2 khung song song cố định (Split View)**:

```
+------------------------------------------------------------------------------------------------------------------+
| ASTRA                                                                               [ Xuất Word ]   [ In PDF ]   |
+----------------------------------------------------+-------------------------------------------------------------+
| KHUNG TƯƠNG TÁC & CHAT (Trái ~38%)                 | CANVAS TẠO ĐỀ TRỰC TIẾP (Phải ~62%)                         |
|                                                    |                                                             |
| [Lịch sử hội thoại tinh chỉnh]                     | [Tiêu đề đề thi & Thời gian làm bài]                        |
|                                                    | ----------------------------------------------------------- |
| User: "Soạn đề kiểm tra 1 tiết Vật lý 12,          | ĐANG TẠO: 12 / 40 CÂU HOÀN THÀNH                            |
|        tập trung phần Dao động và Sóng..."         | ----------------------------------------------------------- |
|                                                    | Câu 1: Một vật dao động điều hòa theo phương trình...       |
| Assistant: "Đang phân tích cấu trúc ma trận        |   A. Biên độ       B. Chu kỳ       C. Tần số góc    D. Pha  |
|            và tiến hành giải đối chiếu độc lập."   |   (Đáp án: C)                                               |
|                                                    |                                                             |
|                                                    | Câu 2: Một con lắc lò xo có độ cứng k = 100 N/m...          |
|                                                    |   A. 0.1s          B. 0.2s         C. 0.4s          D. 0.5s |
|                                                    |   (Đáp án: A)                                               |
|                                                    |                                                             |
|                                                    | Câu 3: [Đang kiểm tra lời giải độc lập...]                  |
|                                                    |                                                             |
| -------------------------------------------------- |                                                             |
| [THANH CHAT HIỆN ĐẠI]                              |                                                             |
| +------------------------------------------------+ |                                                             |
| | Nhập yêu cầu tạo đề hoặc điều chỉnh...         | |                                                             |
| |                                                | |                                                             |
| | [📎 Đính kèm tệp]   [🌐 Tìm trên mạng]    [↑]  | |                                                             |
| +------------------------------------------------+ |                                                             |
+----------------------------------------------------+-------------------------------------------------------------+
```

---

## 4. Đặc Tả Chi Tiết 2 Khung Màn Hình

### 4.1 Khung bên Trái: Chatbot Terminal & Input Bar
- **Bố cục:** Chiếm khoảng 35% - 40% bề ngang màn hình bên trái.
- **Khu vực hiển thị tin nhắn (Chat Message Feed):**
  - Hiển thị ngắn gọn lời nhắc của giáo viên và thông báo tiến độ ngắn của hệ thống.
  - Phông chữ sạch sẽ, không bong bóng chat hoạt họa bo tròn lố bịch. Dạng dòng tin nhắn phẳng (flat lines), ngăn cách bằng khoảng trắng (whitespace).
- **Thanh Chat Hiện Đại (Modern Floating/Docked Input Bar):**
  - Mô phỏng chuẩn mực của các AI chatbot hiện đại (như Claude / ChatGPT / Perplexity).
  - Ô textarea tự động giãn chiều cao theo số dòng (Auto-expand từ 1 đến 5 dòng).
  - Thanh công cụ tích hợp ngay mép dưới ô nhập:
    - **Nút `[📎 Đính kèm tài liệu]`:** Mở cửa sổ chọn file giáo án, ma trận hoặc tệp PDF/Docx của giáo viên.
    - **Nút `[🌐 Tìm trên mạng]` (Toggle switch):** Bật/tắt chế độ tra cứu dữ liệu web thời gian thực.
    - **Nút `[Gửi / Mũi tên]`:** Nằm gọn ở góc phải thanh chat. Phím tắt: `Enter` để gửi, `Shift + Enter` để xuống dòng.

---

### 4.2 Khung bên Phải: Live Creation Canvas (Cơ Chế Dopamine)
- **Mục tiêu UX:** Tạo cảm giác thỏa mãn và tin cậy cho giáo viên khi tận mắt chứng kiến đề thi đang được "dệt" thành hình từng câu một cách chuyên nghiệp.
- **Cách thức hoạt động:**
  - Nhận luồng dữ liệu thời gian thực (Server-Sent Events) từ Backend.
  - **Câu hỏi xuất hiện tức thì:** Cứ mỗi khi tác tử giải xong 1 câu và kiểm định đạt, câu hỏi đó lập tức xuất hiện trên mặt giấy bên phải.
  - **Trình bày dạng bài thi chuẩn mực:**
    - Có tiêu đề trường/sở, mã đề, tên môn học, thời gian làm bài.
    - Câu hỏi đánh số thứ tự rõ ràng (`Câu 1:`, `Câu 2:`...).
    - Công thức Toán - Lý - Hóa hiển thị chuẩn LaTeX qua KaTeX (không bị lỗi font).
    - 4 phương án A, B, C, D xếp ngay ngắn.
  - **Cơ chế phát hiện lỗi nhẹ nhàng (Non-intrusive Flag):**
    - Nếu câu nào hai tác tử độc lập bị lệch đáp án hoặc câu hỏi có bẫy đa nghĩa: Hiện một dòng ghi chú xám viền mảnh bên dưới câu đó kèm nút `[Sửa]` hoặc `[Đổi câu này]`.
  - **Thanh tác vụ trên đỉnh Canvas:**
    - `[ Xuất file Word (.docx) ]`: Xuất tệp chuẩn để giáo viên in trực tiếp.
    - `[ Xuất Đáp án & Barem (.docx) ]`: Bản có lời giải chi tiết cho người chấm.

---

## 5. Cấu Trúc Thành Phần Giao Diện Đề Xuất (Component Architecture)

Dành cho AI hoặc Kỹ sư viết code Frontend:

```
src/
├── components/
│   ├── OnboardingFork.tsx         # Màn hình hỏi: "Bạn muốn tạo đề nhanh?" (Có / Chuyên nghiệp)
│   ├── QuickPresetModal.tsx       # Bảng chọn nhanh mẫu đề chuẩn (THPTQG, DGNL)
│   ├── Workspace/
│   │   ├── WorkspaceLayout.tsx    # Bố cục chia 2 khung ngang (Desktop Split 40 - 60)
│   │   ├── ChatPane/
│   │   │   ├── ChatHistory.tsx    # Luồng tin nhắn phẳng giữa Thầy cô và Hệ thống
│   │   │   └── ModernChatBar.tsx  # Thanh nhập prompt chuẩn chatbot (kèm upload file, web search)
│   │   └── LiveCanvas/
│   │       ├── CanvasHeader.tsx   # Tiêu đề đề thi, bộ đếm số câu hoàn thành, nút xuất Word/PDF
│   │       ├── ExamPaperView.tsx  # Mặt giấy bài thi hiển thị câu hỏi trực tiếp thời gian thực
│   │       └── QuestionCard.tsx   # Từng câu hỏi chuẩn LaTeX KaTeX kèm đáp án & xử lý cờ
│   └── Shared/
│       └── MathRenderer.tsx       # Bộ parse và render công thức Toán/Lý/Hóa bằng KaTeX
├── types/
│   └── exam.ts                    # Type definitions (QuestionItem, ExamPackage, ProgressEvent)
└── styles/
    └── workspace.css              # CSS tinh tế, bo góc nhẹ (4px-8px), màu baby green, không animation thừa
```

---

## 6. Tiêu Chuẩn Nghiệm Thu Kỹ Thuật (Acceptance Checklist)

1. **Hiển thị Desktop:** Màn hình ngang hiển thị đầy đủ cả Khung Chat và Khung Giấy thi cùng lúc mà không bị vỡ bố cục hay phải cuộn ngang.
2. **Khởi đầu 1 câu hỏi:** Khi vừa tải trang, chỉ có đúng một câu hỏi chào và 2 nút lựa chọn rõ ràng.
3. **Thanh chat đa năng:** Thanh nhập liệu gõ mượt, có icon đính kèm tài liệu và nút gửi rõ ràng.
4. **Cơ chế song song (Dopamine):** Khi người dùng gõ lệnh bên trái, câu hỏi sinh ra lập tức xuất hiện bên phải theo thứ tự từ 1 đến hết.
5. **Thẩm mỹ:** Không có hiệu ứng nhấp nháy làm mỏi mắt; màu xanh nhạt (baby green) làm điểm nhấn tinh tế; không có các khối viền đỏ vàng gay gắt.

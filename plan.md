# ASTRA — Kế Hoạch Thiết Kế & Đặc Tả UI/UX (Master Plan)

**Mục tiêu tài liệu:** Bản đặc tả kỹ thuật, kiến trúc giao diện và phân tích Tư Duy Tính Toán (Computational Thinking) chuẩn xác dành cho kỹ sư / AI lập trình xây dựng lại từ đầu và phục vụ viết báo cáo học thuật.  
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

### Màn hình khởi đầu (The Fork in the Road)
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

## 5. Phân Tích Dưới Lăng Kính Tư Duy Tính Toán (Computational Thinking Analysis)

*Phần này phân tích nền tảng tư duy tính toán cốt lõi định hình nên toàn bộ thiết kế giao diện ASTRA, bám sát khung chương trình CSC10014 và tiêu chí đánh giá độ phức tạp tư duy (Complexity).*

### 5.1 Decomposition (Phân rã)
- **Phân rã không gian làm việc (Workspace Decomposition):** Phân rã tiến trình soạn đề thành hai không gian độc lập về mặt nhận thức nhưng đồng bộ về dữ liệu:
  1. *Không gian Chỉ huy & Tương tác (Control Plane - Khung Trái):* Nơi giáo viên ra lệnh, đính kèm tài liệu và giao tiếp.
  2. *Không gian Sản phẩm & Thẩm định (Artifact Plane - Khung Phải):* Nơi kết quả đề thi được hiện thực hóa và kiểm duyệt trực tiếp.
- **Phân rã hành vi sửa chữa (Item-Level Repair Decomposition):**  
  Thay vì cơ chế "All-or-Nothing" (muốn đổi 1 câu phải chạy lại toàn bộ 40 câu gây tốn token và mất các câu đã ưng ý), hệ thống phân rã đề thi thành từng thực thể `QuestionItem`, cho phép gửi yêu cầu sửa riêng lẻ cho đúng câu đó mà không ảnh hưởng 39 câu còn lại.

### 5.2 Pattern Recognition (Nhận diện mẫu)
- **Mẫu thẩm định hội đồng thi (Exam Committee Proofreading Pattern):**  
  Trong thực tế, giáo viên không đọc 40 câu với sự chú ý ngang nhau. Họ chỉ quan tâm sâu ở **các câu bị tranh cãi hoặc có nguy cơ lệch đáp án**. Giao diện nhận diện mẫu hành vi này để tạo cơ chế **Triage**: Phân cụm câu hỏi thành 2 tập hợp $\{ \text{Verified} \}$ (hiển thị sạch sẽ, không nút thừa) và $\{ \text{Flagged} \}$ (đóng khung lưu ý kèm 2 lựa chọn xử lý nhanh).
- **Mẫu tương tác quen thuộc (Conversational Mental Model):**  
  Giáo viên ngày nay đã quen thuộc với giao diện chatbot (ChatGPT/Claude). Việc tái sử dụng mẫu thanh chat hiện đại giúp loại bỏ hoàn toàn chi phí học cách sử dụng (Zero-learning curve).

### 5.3 Abstraction (Trừu tượng hóa & Giấu thông tin)
- **Layered Abstraction (Trừu tượng hóa phân tầng):**  
  UI đóng vai trò là tầng trừu tượng cao nhất, che giấu hoàn toàn các chi tiết kỹ thuật phức tạp bên dưới (như cấu trúc mạng tác tử, vector embedding, RAG retrieval, token limits, multi-turn prompts). Giáo viên chỉ tương tác với các thực thể sư phạm thuần túy: *Đề bài, Đáp án, SGK, Barem điểm*.
- **Information Hiding qua Onboarding Fork:**  
  Câu hỏi khởi đầu *"Bạn muốn tạo đề nhanh?"* là một lớp trừu tượng hóa: nó đóng gói toàn bộ ma trận kiến thức phức tạp thành một câu hỏi nhị phân đơn giản, bảo vệ giáo viên khỏi sự choáng ngợp thông tin (cognitive overload).

### 5.4 Algorithm Design (Thiết kế luồng thuật toán UI)
- **Máy trạng thái hữu hạn (Finite State Machine - FSM):**  
  Giao diện hoạt động như một FSM với các chuyển trạng thái xác định:  
  $$\text{ONBOARDING} \xrightarrow{\text{chọn}} \text{WORKSPACE\_IDLE} \xrightarrow{\text{prompt}} \text{STREAMING\_GENERATION} \xrightarrow{\text{hoàn tất}} \text{READY\_TO\_EXPORT}$$
- **Thuật toán tiếp nhận luồng sự kiện (Dopamine Streaming Algorithm):**  
  Tiếp nhận luồng Server-Sent Events (SSE) bất đồng bộ từ backend, giải mã JSON từng câu và chèn trực tiếp vào Document Object Model (DOM) theo đúng thứ tự mà không gây hiện tượng giật trang (layout shift).

### 5.5 Spatial & Temporal Reasoning (Tư duy Không gian & Thời gian)
- **Spatial Reasoning (Tư duy cấu trúc thị giác):**  
  Áp dụng mô hình bố cục ngang 40–60. Khung chat bên trái giữ vai trò neo thông tin điều khiển, khung canvas bên phải đóng vai trò mặt giấy in mở rộng. Mắt người dùng di chuyển tự nhiên từ trái (mô tả ý định) sang phải (chứng kiến sản phẩm thành hình) theo quy luật dòng chảy thị giác tự nhiên.
- **Temporal Reasoning (Tư duy tiến trình thời gian):**  
  Thời gian chạy của hệ thống Multi-Agent kéo dài từ 2–5 phút. Nếu để màn hình chờ thông thường, người dùng sẽ nghĩ hệ thống bị treo. Bằng cách kích hoạt cơ chế sinh câu hỏi song song (cứ xong câu nào hiện câu đó), thời gian chờ tâm lý (perceived latency) được triệt tiêu, kích hoạt sự hứng thú và tin tưởng vào tiến độ công việc.

---

## 6. Cấu Trúc Thành Phần Giao Diện Đề Xuất (Component Architecture)

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

## 7. Công Nghệ & Tech Stack (Implementation Stack)

*Mục này đóng vai trò tham chiếu kỹ thuật cho việc hiện thực hóa:*

- **Giao diện & Ứng dụng Client:**
  - **Framework:** React 19 + TypeScript (Đảm bảo an toàn kiểu dữ liệu cho các hợp đồng interface).
  - **Build Tool:** Vite (Tốc độ biên dịch siêu tốc < 2.5 giây, HMR tức thì).
  - **Styling:** CSS Modules / Tailwind CSS cấu hình nhẹ (Tập trung typography, khoảng đệm, bo góc 4px–8px).
- **Xử lý Công thức & Ký hiệu Khoa học:**
  - **KaTeX (`katex`):** Bộ thư viện toán học nhanh nhất hiện nay, hiển thị công thức Toán, Lý, Hóa chuẩn LaTeX cho thi THPTQG.
- **Hệ thống Biểu tượng (Icons):**
  - **Lucide-React:** Bộ icon hình học thanh mảnh, hiện đại, kích thước chuẩn 16px–20px.
- **Giao thức Giao tiếp với Multi-Agent Backend:**
  - **Server-Sent Events (SSE):** Duy trì kết nối một chiều thời gian thực để stream từng câu hỏi và trạng thái kiểm duyệt từ backend lên Live Canvas.
  - **REST API (`fetch` / JSON):** Xử lý gửi prompt, đính kèm tệp và yêu cầu sửa câu hỏi đơn lẻ.
- **Xuất bản Tài liệu:**
  - **Tệp Word (.docx):** Sinh tệp DOCX trực tiếp từ cấu trúc dữ liệu `ExamPackage` để giáo viên mở bằng Microsoft Word.
  - **Tệp PDF:** Tận dụng CSS Print Stylesheet để in trực tiếp từ trình duyệt mà không làm lệch font.

---

## 8. Tiêu Chuẩn Nghiệm Thu Kỹ Thuật (Acceptance Checklist)

1. **Hiển thị Desktop:** Màn hình ngang hiển thị đầy đủ cả Khung Chat và Khung Giấy thi cùng lúc mà không bị vỡ bố cục hay phải cuộn ngang.
2. **Khởi đầu 1 câu hỏi:** Khi vừa tải trang, chỉ có đúng một câu hỏi chào và 2 nút lựa chọn rõ ràng.
3. **Thanh chat đa năng:** Thanh nhập liệu gõ mượt, có icon đính kèm tài liệu và nút gửi rõ ràng.
4. **Cơ chế song song (Dopamine):** Khi người dùng gõ lệnh bên trái, câu hỏi sinh ra lập tức xuất hiện bên phải theo thứ tự từ 1 đến hết.
5. **Thẩm mỹ:** Không có hiệu ứng nhấp nháy làm mỏi mắt; màu xanh nhạt (baby green) làm điểm nhấn tinh tế; không có các khối viền đỏ vàng gay gắt.

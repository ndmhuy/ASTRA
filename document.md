# ASTRA — Tài Liệu Chuyển Giao Kiến Trúc & Hướng Dẫn Kỹ Thuật (Handover Doc)

> **Mục đích tài liệu:** Bản tóm tắt kiến trúc, luồng nghiệp vụ, giao ước dữ liệu (API Contracts) và trạng thái mã nguồn của hệ thống ASTRA để kỹ sư hoặc AI (ChatGPT / Claude) tiếp nhận và triển khai tiếp mà không làm gãy vỡ hệ thống hiện tại.

---

## 1. Tổng Quan Dự Án

- **Tên dự án:** ASTRA — AI-Powered Exam Generation & Verification System.
- **Bối cảnh:** Đồ án môn *Tư Duy Tính Toán (Computational Thinking - CSC10014)* — Chương trình APCS, Trường ĐH Khoa Học Tự Nhiên (HCMUS).
- **Core Concept:** Hệ thống đa tác tử (Multi-Agent: Writer - Blind Solver - Critic/Appraiser) tự động sinh đề thi, giải đối chiếu độc lập và phát hiện bẫy câu hỏi trước khi trả về cho giáo viên.
- **Frontend Stack:** React 19, TypeScript, Vite, KaTeX (render công thức Toán/Lý/Hóa), Lucide React.
- **Git Repo:** `https://github.com/ndmhuy/ASTRA.git`, nhánh làm việc hiện tại: **`uiux`**.

---

## 2. Kiến Trúc Giao Diện (UI/UX Architecture)

Giao diện đã được refactor hoàn toàn từ luồng 3 bước tuần tự cũ (`Config -> Stepper -> Review`) sang mô hình **Không gian làm việc song song (Parallel Workspace)** theo chuẩn *ASTRA Master Plan*.

```
                              [ Khởi Động ]
                                    │
                                    ▼
                          ┌──────────────────┐
                          │  OnboardingFork  │
                          └─────────┬────────┘
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
          [ Nút: Tạo nhanh ]             [ Nút: Chuyên nghiệp ]
                    │                               │
                    ▼                               │
         ┌──────────────────────┐                   │
         │  QuickPresetModal    │                   │
         └──────────┬───────────┘                   │
                    │ (Submit)                      │
                    └───────────────┬───────────────┘
                                    │
                                    ▼
       ┌─────────────────────────────────────────────────────────┐
       │                   WorkspaceLayout                       │
       │                                                         │
       │  ┌───────────────────────┐   ┌───────────────────────┐  │
       │  │ ChatPane (38%)        │   │ LiveCanvas (62%)      │  │
       │  │ - Header + ChatHistory│   │ - CanvasHeader        │  │
       │  │ - ModernChatBar       │   │ - ExamPaperView       │  │
       │  │   (Attach/Web/Send)   │   │ - QuestionCard (KaTeX)│  │
       │  └───────────────────────┘   └───────────────────────┘  │
       └─────────────────────────────────────────────────────────┘
```

### 2.1 Luồng người dùng (User Flow)
1. **Màn hình chào đón (`OnboardingFork.tsx`):**
   - Đơn giản, trực diện với câu hỏi: *"Bạn muốn tạo đề như thế nào?"*.
   - Nút to, rõ ràng, tối ưu cho giáo viên không rành công nghệ:
     - **Tạo nhanh** (xanh Emerald): Mở drawer chọn chuẩn nhanh.
     - **Chế độ Chuyên nghiệp**: Vào thẳng workspace để prompt tự do.
   - **Cơ chế lưu phiên (Active Session Resume):** Nếu người dùng đang tạo dở đề hoặc đã có lịch sử chat mà quay lại màn hình chính, hệ thống sẽ hiện **Banner xanh nhắc nhở: "Bạn có phiên làm việc đang mở"** kèm nút `[ Quay lại → ]` để bảo toàn dữ liệu, không bị reset mất việc.
2. **Hộp thoại cấu hình nhanh (`QuickPresetModal.tsx`):**
   - Chọn định dạng: `THPT Quốc Gia (40 câu · 50 phút)` hoặc `Đánh Giá Năng Lực (30 câu · 40 phút)`.
   - Chọn môn học (`Toán, Lý, Hóa, Sinh, Anh, Sử, Địa, GDCD, Tổng hợp`).
   - Bấm `Bắt đầu tạo đề →` sẽ kích hoạt pipeline và chuyển vào Workspace.
3. **Không gian làm việc song song (`WorkspaceLayout.tsx`):**
   - **Cột Trái (38% - `ChatPane`):**
     - Dòng hội thoại phẳng (*Flat line messages*), không dùng bong bóng hoạt họa trẻ con ("LLM-ism").
     - `ModernChatBar`: Textarea tự giãn chiều cao (1-5 dòng), đính kèm tệp 📎, bật/tắt tìm kiếm web 🌐, gửi tin bằng phím `Enter`.
   - **Cột Phải (62% - `LiveCanvas`):**
     - `CanvasHeader`: Đếm số câu hoàn thành theo thời gian thực (`ĐANG TẠO: X / Y CÂU`), nút xuất file Word (.docx) đề thi & đáp án/barem.
     - `ExamPaperView`: Hiển thị dạng mặt giấy in chuẩn mực. Câu hỏi mới sinh ra xuất hiện tức thì với hiệu ứng fade-in mượt (CSS transition 200ms).
     - `QuestionCard`: Render công thức Toán/Lý/Hóa bằng KaTeX chuẩn xác, highlight đáp án đúng, gắn nhãn cảnh báo nếu có bẫy hoặc bất đồng đáp án giữa Writer và Solver kèm nút sửa.

---

## 3. Triết Lý Thiết Kế (Design System & Anti-LLMism)

Hệ thống tuân thủ nghiêm ngặt các nguyên tắc sau:
- **Tone màu:** Nền sáng dịu (`#fafbfa`, `#f8fafc`), bề mặt thẻ trắng viền mảnh 1px (`#e2e8f0`), điểm nhấn **Baby Green / Emerald** (`#059669`, `#10b981`, `#ecfdf5`).
- **Bo góc chuẩn:** Chỉ dùng bo góc hình học thanh lịch `4px` đến `8px`. **Tuyệt đối không dùng pill-shape bo tròn xoe**.
- **Không Animation hoa mắt:** Không dùng chấm nhấp nháy, không dùng loader xoay tít, không dùng hiệu ứng nảy (bounce).
- **Typography:** Body 14–15px, Tiêu đề bài thi 20–22px, Label 12px.
- **Trực quan cho giáo viên:** Các nút hành động chính có diện tích bấm lớn, nhãn chữ tiếng Việt tường minh.

---

## 4. Cấu Trúc Thư Mục Frontend (`astra-frontend/src`)

```
src/
├── App.tsx                     # Bộ điều phối trung tâm: quản lý state screen, active session, generation
├── App.css / index.css         # CSS reset & biến giao diện gốc
├── main.tsx                    # Entry point React
├── types/
│   └── exam.ts                 # Contracts & Types: QuestionItem, ExamPackage, GenerationProgress, ChatMessage
├── services/
│   └── examService.ts          # Service Layer: Tách biệt MockExamService và ApiExamService qua .env
├── styles/
│   └── workspace.css           # Toàn bộ CSS layout chia cột 38/62, fade-in card, flat chat
└── components/
    ├── OnboardingFork.tsx      # Màn hình Fork (Tạo nhanh / Chuyên nghiệp / Khôi phục phiên)
    ├── QuickPresetModal.tsx    # Modal preset nhanh (THPTQG, DGNL + Môn học)
    ├── MathRenderer.tsx        # Parser KaTeX inline ($...$) & block ($$...$$)
    ├── Navbar.tsx              # Navbar cũ (giữ làm tham chiếu)
    ├── ConfigView.tsx          # View cấu hình cũ (giữ làm tham chiếu)
    ├── StepperView.tsx         # View tiến trình cũ (giữ làm tham chiếu)
    ├── ReviewView.tsx          # View review cũ (giữ làm tham chiếu)
    ├── EditQuestionModal.tsx   # Modal chỉnh sửa chi tiết câu hỏi
    ├── ExportModal.tsx         # Modal tuỳ chọn xuất tài liệu
    └── Workspace/
        ├── WorkspaceLayout.tsx # Bố cục chia 2 khung Desktop cố định
        ├── ChatPane/
        │   ├── ChatHistory.tsx # Danh sách tin nhắn dạng flat dòng
        │   └── ModernChatBar.tsx # Input bar tự giãn + công cụ đính kèm/web
        └── LiveCanvas/
            ├── CanvasHeader.tsx # Header bộ đếm X/Y câu + nút xuất DOCX
            ├── ExamPaperView.tsx# Khung giấy thi trực quan cuộn độc lập
            └── QuestionCard.tsx # Thẻ câu hỏi KaTeX + xử lý cờ kiểm định
```

---

## 5. Kiến Trúc Backend Đa Tác Tử & Cơ Chế Kết Nối (Backend Integration)

Frontend và Backend được **tách rời hoàn toàn (Decoupled)** theo nguyên lý:
> **Backend (Multi-Agent)** phụ trách sinh và giải đối chiếu, chỉ cần stream dữ liệu JSON từng câu hỏi hoàn chỉnh qua Server-Sent Events (SSE).  
> **Frontend** tự bắt sự kiện SSE, trích xuất dữ liệu và render câu hỏi lên mặt giấy với hiệu ứng fade-in độc lập.

```
[ Backend Multi-Agent Pipeline ]
 1. Blueprint Builder  ──► Tạo ma trận đề
 2. RAG SGK Retriver   ──► Lấy kiến thức chuẩn
 3. Writer + Solver    ──► Soạn đề & Giải độc lập
 4. Critic/Appraiser   ──► Thẩm định, phát hiện bẫy
           │
           ▼ (Đẻ ra từng câu QuestionItem)
    SSE Stream Event:
    data: {
      "stage": 3,
      "completedItems": 5,
      "totalItems": 40,
      "latestItemPreview": {
        "id": 5,
        "stem": "Cho mạch điện $RLC$... Tổng trở $Z$ là:",
        "choices": { "A": "...", "B": "...", ... },
        "key": "B",
        "status": "VERIFIED"
      }
    }
           │
           ▼
[ Frontend ASTRA ] ──► Append vào liveQuestions[] ──► Canvas tự render & KaTeX render tức thì!
```

### 5.1 Cấu hình Switch MOCK / API Thật
Trong file `astra-frontend/.env` (đã có sẵn file mẫu `.env.example`):
```bash
# Đang chạy chế độ giả lập offline để demo & test UI:
VITE_SERVICE_MODE=mock

# Khi backend thật (FastAPI / Flask) sẵn sàng, chỉ cần đổi thành:
VITE_SERVICE_MODE=api
VITE_API_BASE_URL=http://localhost:8000/api
```

### 5.2 Các Endpoints Backend Cần Cung Cấp
Nếu ChatGPT/Backend Developer viết backend, cần hỗ trợ 5 endpoints REST/SSE sau:

| Phương thức | Đường dẫn | Chức năng | Body / Query | Output mong đợi |
|---|---|---|---|---|
| `POST` | `/api/exams/generate` | Khởi tạo job sinh đề | `ExamRequestParams` | `{ "jobId": "string" }` |
| `GET` | `/api/exams/{jobId}/events` | SSE Stream tiến trình | Không | Luồng `GenerationProgress` SSE |
| `GET` | `/api/exams/{jobId}` | Lấy toàn bộ đề thi hoàn chỉnh | Không | `ExamPackage` |
| `POST` | `/api/exams/{jobId}/questions/{id}/regenerate` | Tái tạo/sửa 1 câu theo prompt | `{ "instruction": "string" }` | `QuestionItem` |
| `PUT` | `/api/exams/{jobId}/questions/{id}` | Cập nhật thủ công nội dung câu | `QuestionItem` | `{ "success": true }` |
| `GET` | `/api/exams/{jobId}/export` | Xuất file in | `?type=STUDENT_EXAM&format=docx` | Binary stream / download |

### 5.3 Cấu trúc Dữ Liệu Cốt Lõi (`src/types/exam.ts`)

#### QuestionItem (Câu hỏi)
```typescript
export interface QuestionItem {
  id: number;
  stem: string;                  // Đề bài (chứa công thức LaTeX $...$)
  choices: {
    A: string;
    B: string;
    C: string;
    D: string;
  };
  key: 'A' | 'B' | 'C' | 'D';    // Đáp án chính thức
  explanation: string;           // Lời giải chi tiết
  level: 'NHAN_BIET' | 'THONG_HIEU' | 'VAN_DUNG' | 'VAN_DUNG_CAO';
  topic: string;
  status: 'PENDING' | 'VERIFIED' | 'FLAGGED';
  writerKey?: 'A' | 'B' | 'C' | 'D'; // Đáp án do Writer đưa ra
  solverKey?: 'A' | 'B' | 'C' | 'D'; // Đáp án do Blind Solver giải ra
  auditNotes?: string;           // Ghi chú bất đồng / cảnh báo bẫy đa nghĩa
}
```

#### GenerationProgress (Event SSE mỗi nhịp)
```typescript
export interface GenerationProgress {
  stage: number;               // 1 -> 5
  stageName: string;           // Tên bước đang chạy
  percent: number;             // 0 -> 100
  estimatedSecondsLeft: number;
  completedItems: number;      // Số câu đã sinh xong
  totalItems: number;          // Tổng số câu (ví dụ: 40)
  statusMessage: string;       // Log ngắn
  latestItemPreview?: QuestionItem; // [QUAN TRỌNG]: Câu hỏi vừa hoàn thành để Canvas bên phải vẽ ngay
}
```

---

## 6. Hướng Dẫn Chạy & Thao Tác Git

### 6.1 Khởi động Frontend
```bash
# 1. Di chuyển vào thư mục frontend
cd astra-frontend

# 2. Cài đặt dependencies (nếu chưa cài)
npm install

# 3. Khởi chạy dev server (port 5173)
npm run dev
# hoặc chạy trực tiếp bằng Vite:
npx vite --port 5173

# 4. Kiểm tra TypeScript / Build
npx tsc -b --noEmit
npm run build
```

### 6.2 Tình trạng Git
- **Remote Repo:** `https://github.com/ndmhuy/ASTRA.git`
- **Branch đang dùng:** `uiux`
- **Các file tài liệu nhạy cảm / file thô đã được đổi tên và thêm vào `.gitignore` (chỉ lưu cục bộ trên máy):**
  - `plan.md` (bản master plan gốc)
  - `report.pdf` (báo cáo nhóm)
  - `plan1.jfif`, `plan2.jfif`, `plan3.jfif`, `plan4.jfif` (ảnh thiết kế mẫu)
  - Thư mục `Resource/`

---

## 7. Gợi Ý Các Bước Tiếp Theo Dành Cho ChatGPT / Developer Kế Tiếp

1. **Xây dựng Backend Multi-Agent:**
   - Dùng **FastAPI** hoặc **LangGraph / CrewAI / Autogen**.
   - Thiết lập luồng 3 agent:
     1. Agent 1 (`Writer`): Nhận ma trận đề, sinh câu hỏi + đáp án nháp.
     2. Agent 2 (`Solver`): Nhận câu hỏi đã giấu đáp án, tự giải độc lập ra `solverKey`.
     3. Agent 3 (`Critic`): So sánh `writerKey` vs `solverKey`. Nếu khớp $\rightarrow$ `status = VERIFIED`; nếu lệch hoặc phát hiện bẫy $\rightarrow$ `status = FLAGGED` và viết `auditNotes`.
   - Kết nối endpoint SSE `/api/exams/{jobId}/events` để push từng câu ra Frontend.
2. **Nâng cấp tính năng Chat sửa câu:**
   - Khi giáo viên gõ: *"Sửa câu 3 thành mức độ vận dụng cao hơn"* bên khung trái, kết nối backend để gọi endpoint regenerate targeted item và cập nhật câu số 3 trên Canvas ngay lập tức.
3. **Hoàn thiện Export DOCX:**
   - Sử dụng thư viện `python-docx` trên backend để render file Word chuẩn thể thức đề thi Bộ GD&ĐT (Font Times New Roman, chia bảng điểm, tiêu đề trường sở).

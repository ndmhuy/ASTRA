# Luồng lập kế hoạch MAS trong ASTRA

Đặc tả hành vi của runtime `astra_mas` 0.1.1, từ `prepare_plan` đến
`MasResult`. Các trường dữ liệu, mã lỗi và cấu hình nằm trong
[hợp đồng I/O](ASTRA_MAS_IO_CONTRACT.md).

## A. Kiểm tra đầu vào và đọc tệp

```mermaid
flowchart TD
  A0(["ASTRA gọi prepare_plan với MasInput, callback và MasLimits"])
  A0 --> A1{"Đạt giới hạn<br/>đầu vào?"}
  A1 -->|Không| AE["MasError theo giới hạn"]
  A1 -->|Có| A2["Kiểm tra bundle và CPython<br/>Mở tiến trình tạm, chặn mạng Python"]
  A2 --> A3["Kiểm tra mã định dạng<br/>Kiểm kê PDF, ảnh và dung lượng giải nén Office"]
  A3 --> A4{"Có ma trận riêng?"}
  A4 -->|Không| A6["Dựng khung theo định dạng và môn"]
  A4 -->|Có| A5["Đọc bảng CSV, XLSX hoặc DOCX<br/>Giữ hàng rõ, ghi mâu thuẫn theo địa chỉ"]
  A5 --> A6
  A6 --> A7["Chuyển đổi cục bộ theo loại tệp<br/>Kiểm giới hạn ảnh và ký tự trích xuất"]
  A7 --> A8{"Ma trận cần<br/>phục hồi?"}
  A8 -->|Có| A9["Đọc PDF, ảnh hoặc văn bản<br/>Dùng INTAKE_VISUAL_READ khi cần, rồi kiểm lại bảng"]
  A8 -->|Không| A10{"Có tài liệu tham khảo?"}
  A9 --> A10
  A10 -->|Có| A11["Gộp bản trùng theo dấu vân tay nội dung<br/>Đọc văn bản gốc, ảnh và trang quét"]
  A11 --> A12["INTAKE_VISUAL_BATCH khi cần<br/>Lọc bài khi xác lập được, rồi PLAN_REFERENCE_SUMMARY"]
  A12 --> A13["Ghi nguồn và phần đọc thiếu<br/>Chuyển sang B"]
  A10 -->|Không| A13
  classDef terminal fill:#e8f5f0,stroke:#176b5a,color:#172838
  classDef error fill:#fcecea,stroke:#9d3c33,color:#5e2823
  class A0,A13 terminal
  class AE error
```

ASTRA kiểm tra kiểu dữ liệu khi tạo `MasInput` và `MasLimits`, rồi chọn vai
tệp qua `matrix` và `materials`. Đề mẫu gửi trong `materials`
đi qua bộ đọc tài liệu tham khảo. Một bảng có hàng đã đọc được hoặc có mâu
thuẫn theo địa chỉ được giữ để xử lý bằng chứng. Nhánh phục hồi áp dụng khi
bảng còn thiếu cấu trúc và chưa có mâu thuẫn đã ghi.

Poppler kiểm kê và đọc PDF. Pandoc đọc công thức DOCX khi có sẵn. Bộ đọc giữ
dấu vết mất công thức, ảnh hay đoạn đọc thiếu. Trình đọc ảnh gửi ảnh PNG qua
callback ở C. Các lỗi kiểm kê, định dạng hoặc giới hạn dừng lần gọi bằng mã
lỗi. Tài liệu đọc thiếu có thể được ghi cảnh báo để tiếp tục với nguồn còn lại.

## B. Xác định phạm vi và lập kế hoạch

```mermaid
flowchart TD
  B0(["Bằng chứng và khung đã đọc từ A"])
  B0 --> B1{"Có thời lượng rõ<br/>và số câu còn linh hoạt?"}
  B1 -->|Có| B2["INTAKE_BLUEPRINT đề xuất số câu<br/>Kiểm theo dạng câu của định dạng"]
  B1 -->|Không| B3["Giữ khung mặc định hoặc số câu đã xác lập"]
  B2 --> B4["Chốt khung có thể dùng<br/>Dự phòng bằng quy tắc khi cần"]
  B3 --> B4
  B4 --> B5{"Cần diễn giải yêu cầu<br/>hoặc bằng chứng đầu vào?"}
  B5 -->|Có| B6["PLAN_INPUT_RESOLUTION<br/>Kiểm phạm vi, nguồn, nhóm và địa chỉ"]
  B5 -->|Không| B7["Xác định phạm vi theo quy tắc<br/>và dữ liệu đi kèm"]
  B6 -->|Phản hồi dùng được| B8["Ràng buộc phạm vi và nguồn đã kiểm"]
  B6 -->|Phản hồi không dùng được| B7
  B7 --> B8
  B8 --> B9["Dựng kế hoạch tạm theo địa chỉ phần, câu, ý<br/>Giữ nội dung ma trận đã xác lập"]
  B9 --> BM["Gắn tài liệu đã kiểm vào đúng phần hoặc ô"]
  BM --> B10["PLAN_SYNTHESIS đề xuất chủ đề và yêu cầu<br/>cho các ô được phép bổ sung"]
  B10 --> B11["PLAN_PART_CONTENT cho phần cần xử lý<br/>Kiểm trả lời theo đúng ô và phạm vi phần"]
  B11 --> B12["Kiểm tra khung, nhóm, nội dung và nguồn<br/>Giữ bằng chứng, ghi cảnh báo và tính revision"]
  B12 --> B13(["Chuyển envelope MAS sang C"])
  classDef terminal fill:#e8f5f0,stroke:#176b5a,color:#172838
  class B0,B13 terminal
```

Nếu ma trận đã được gửi hoặc số câu đã xác lập, bước blueprint giữ số câu.
Bộ phân giải dùng yêu cầu, ma trận, phần tài liệu đọc được và dữ liệu đi kèm
để chọn phạm vi. Khi nguồn chưa đủ để xác lập nội dung, kế hoạch giữ các
ô có bằng chứng và ghi phần thiếu. Một phản hồi model sai cấu trúc hoặc sai
địa chỉ có thể bị loại. Luồng dùng phần hợp lệ và quy tắc dự phòng trong
phạm vi còn được xác lập.

Các tên viết hoa là `recipe`. Mỗi lần cần model, bước đang chạy dùng callback
ở C rồi tiếp tục với kết quả đã kiểm. Phần đã đủ nội dung và mô tả nhóm trong
các chế độ cho phép có thể bỏ lượt gọi riêng cho phần đó.

## C. Trao đổi với LLM và trả về ASTRA

```mermaid
flowchart LR
  subgraph CLLM["Khi một bước ở A hoặc B cần model"]
    direction TB
    C0["Tiến trình MAS gửi recipe, system, user và images<br/>qua stdin/stdout"]
    C0 --> C1{"Prompt đạt giới hạn?"}
    C1 -->|Không| C8["MasError có mã lỗi"]
    C1 -->|Có| C2["ASTRA gọi await complete với MasPrompt"]
    C2 --> C3{"Chuỗi trả lời hợp lệ<br/>và đúng giới hạn?"}
    C3 -->|Lỗi callback, phản hồi rỗng hoặc quá lớn| C8
    C3 -->|Có| C4["MAS kiểm JSON và lược đồ của recipe"]
    C4 -->|Đạt| C5["Tiếp tục với dữ liệu đã kiểm"]
    C4 -->|Sai cấu trúc hoặc địa chỉ| C6["Áp dụng dự phòng hoặc ghi cảnh báo của bước"]
  end
  subgraph COUT["Khi B trả envelope MAS"]
    direction TB
    C9["Nhận plan, state và gaps"]
    C9 --> C10{"Ô nào thiếu chủ đề<br/>hoặc yêu cầu cần đạt?"}
    C10 -->|Có| C11["Đặt state thành blocked<br/>Ghi mas_unfilled_cells và địa chỉ ô"]
    C10 -->|Không| C12["Giữ state và gaps từ planner"]
    C11 --> C13{"JSON kết quả đạt giới hạn byte?"}
    C12 --> C13
    C13 -->|Không| C14["MasError mas_plan_bytes_limit"]
    C13 -->|Có| C15(["ASTRA nhận schema_version, state, plan và gaps"])
  end
  CLLM ~~~ COUT
  classDef terminal fill:#e8f5f0,stroke:#176b5a,color:#172838
  classDef error fill:#fcecea,stroke:#9d3c33,color:#5e2823
  class C15 terminal
  class C8,C14 error
```

ASTRA sở hữu model và thông tin xác thực. Tiến trình lập kế hoạch trao đổi
với ASTRA qua luồng nội bộ. Lỗi cài đặt, lỗi giao thức hoặc quá thời gian
trao đổi cũng trả `MasError`. Khi nhận `ready`, ASTRA vẫn đọc `gaps` để hiển
thị cảnh báo. Khi nhận `blocked`, ASTRA vẫn nhận bản kế hoạch ứng viên cùng
các địa chỉ cần bổ sung. Bước cuối của runtime là trả `MasResult`.

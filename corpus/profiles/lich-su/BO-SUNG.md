> **Lịch sử đánh giá:** các số/hold và yêu cầu giáo viên ở dưới thuộc đợt trước. Quyết định dùng hiện hành 06/11/2026 tại [USABILITY-REVIEW](USABILITY-REVIEW.md): 73 mẫu nội dung dùng được, bằng chứng mức được tách riêng; không có gate giáo viên mới.

# Bổ sung

**Nguồn bổ sung:** góp ý của một giáo viên trên bản `LichSu_v4_De (GÓP Ý).docx`, gồm **5 góp ý ghi trong thân tài liệu** và **2 bình luận Word** gắn trực tiếp vào câu hỏi. [Bản gốc lưu trong gói](evidence/teacher-feedback/LichSu_v4_De_GOP-Y.docx). Dữ liệu trích xuất/mapping: [data/teacher-feedback.json](data/teacher-feedback.json).

**Vị trí của nguồn:** đây là *phản hồi chuyên môn về prototype v4*, không phải đề thi chính thức/tỉnh, không tăng mẫu số corpus, không chứng minh độ phân hóa thực nghiệm, và **không phải phê duyệt toàn bộ prototype/hồ sơ**. Các yêu cầu triển khai phía dưới là **đề xuất chuyển hóa** góp ý thành kiểm tra; phân biệt với nội dung giáo viên đã nói.

## Bổ sung từ nhận xét tổng quát

| ID | Nhận xét của giáo viên (tóm đúng ý) | Cách đưa vào kiểm tra | Câu/địa chỉ ưu tiên |
|---|---|---|---|
| `LS-FB-01` | Đề cần phối hợp lớp 10, 11, 12; ở lớp 12 phân bố đủ các chủ đề; bản v4 thiếu chủ đề Hồ Chí Minh. | Lập bảng phủ lớp/chủ đề theo chương trình đích trước khi phát hành. Đánh dấu **chưa phủ** thay vì coi một thuật ngữ xuất hiện là đã phủ chủ đề. Chỉ đề xuất đổi quota khi được xác nhận, không ghi đè baseline. | Mức toàn đề; các nhóm `LS-T05`, `LS-T09`, `LS-T22`, `LS-T23`, `LS-T24` trong catalog cần xét đúng phạm vi, không tự cộng trùng. |
| `LS-FB-02` | Câu vận dụng cần phương án trả lời có khả năng phân hóa hơn. | Yêu cầu chuỗi suy luận thực sự; kiểm từng nhiễu về tính hợp lí, song song và khả năng phân biệt nhầm lẫn. Giữ `hold` nếu chỉ loại được nhiễu do từ ngữ cực đoan/phi lí, kể cả khi khóa khớp. | `P1/21`, `P1/22`, `P1/23`, `P1/24` (đã có cờ trong audit trước); áp dụng cho tất cả VD. |
| `LS-FB-03` | Với câu đúng/sai, hạn chế dùng nguồn Internet; nếu dùng phải trích đầy đủ; ưu tiên sách chuyên khảo. | Lưu xuất xứ đầy đủ, đoạn nguyên văn, trang/ấn bản (nếu có), quyền sử dụng, tình trạng kiểm chứng; tự biên soạn ghi rõ. Ưu tiên nguồn chuyên khảo phù hợp, **không suy ra mọi nguồn trực tuyến đều sai**. | Ngữ liệu `P2/1`–`P2/4` cần rà nguồn, chữ trích, bối cảnh, cắt lược. |
| `LS-FB-04` | Câu trắc nghiệm khách quan nên gọn, tránh rườm rà; dẫn câu 19, 22, 23. | Biên tập phần dẫn thành **một nhiệm vụ hỏi rõ**, bỏ mệnh đề lặp và tiền đề không cần thiết, nhưng giữ đủ dữ kiện/mốc. Cụm “nên để 1 câu” có thể hiểu là một câu dẫn ngắn; **cần giáo viên xác nhận** trước khi áp thành quy tắc cứng. | `P1/19`, `P1/22`, `P1/23`. |
| `LS-FB-05` | Nhận định đúng/sai nên được thiết kế theo ba mức NB, TH, VD. | Phân loại **từng ý a–d** theo yêu cầu tối thiểu và lý do; kiểm nhóm có kết hợp mức theo ma trận mục tiêu. Không mặc định `a=NB,b=TH,c=d=VD` là đã đạt. Mức tổng câu theo quy tắc ghi tại `LEVELS.md`; unknown vẫn unknown. | `P2/1/a` đến `P2/4/d`; đặc biệt `P2/1/a` còn cờ đa nghĩa từ audit trước. |

## Bổ sung từ bình luận Word trực tiếp

| ID | Địa chỉ chuẩn | Nội dung giáo viên comment | Hành động kiểm tra |
|---|---|---|---|
| `LS-FB-06` | `P1/3` | “Hạn chế những câu hỏi về ngày tháng” | Cân nhắc đổi yêu cầu ghi nhớ ngày cụ thể thành kiểm tra bối cảnh, ý nghĩa, tiến trình, tương quan sự kiện; nếu vẫn giữ mốc, cần chứng minh mục tiêu nhận thức và mức độ phù hợp. |
| `LS-FB-07` | `P1/8` | “Hạn chế hỏi thời gian” | Cùng nguyên tắc: tránh câu chỉ chọn năm mà không có yêu cầu tư duy lịch sử khác. |

**Sàng lọc mở rộng do người lập hồ sơ đề xuất, không phải bình luận của giáo viên:** `P1/10` cũng hỏi trực tiếp ngày; cần đưa vào lượt rà soát cùng hai câu trên. Không mặc định cấm mọi câu có mốc thời gian (niên đại vẫn có thể cần thiết để hiểu quan hệ trước–sau).

## Bổ sung vào điều kiện nghiệm thu

- [ ] Có đối chiếu **phân bố theo khối lớp/chủ đề** với chương trình và yêu cầu đề đích; chủ đề Hồ Chí Minh được kiểm tra bằng nội dung thực, không phải chỉ trùng từ khóa trong tên chiến dịch.
- [ ] Tất cả câu nhãn VD có **bằng chứng chuỗi suy luận tối thiểu** và ba nhiễu có cơ chế sai hợp lí; không dùng từ tuyệt đối để tạo nhiễu dễ loại.
- [ ] Mỗi nhóm TF: nguồn/ngữ liệu truy xuất được hoặc ghi tự biên soạn; a–d gắn mức NB/TH/VD/unknown độc lập, giải và kiểm từng ý; kiểm phân bố mức trong nhóm.
- [ ] Câu trắc nghiệm có một mục tiêu hỏi chính, câu dẫn ngắn nhất có thể nhưng **không mất dữ kiện cần thiết**; chú ý câu 19, 22, 23.
- [ ] Thống kê câu chỉ yêu cầu nhớ ngày/năm; kiểm sự cần thiết và thay bằng nhiệm vụ đánh giá hiểu/vận dụng khi phù hợp; chú ý câu 3, 8, rà thêm 10.
- [ ] Mọi thay đổi sau góp ý phải có bản câu đã sửa, khóa, giải thích nhiễu, phân loại lại mức và tự giải lại; **chưa sửa = chưa nghiệm thu**.

## Quyết định cập nhật và phạm vi chưa thực hiện

Đợt bổ sung này **đã ghi nhận, chuẩn hóa thành tiêu chí và map địa chỉ**, chưa viết lại 28 câu prototype, chưa thay ma trận nghiên cứu tại SHA đã pin, chưa kiểm chứng các trích dẫn gốc ngoài tài liệu góp ý, và chưa có số liệu bài làm để đo độ phân hóa. Giữ nguyên các nhãn `hold`, `missing`, `pass_model_selfcheck` và số liệu coverage trước bổ sung. Người duyệt chuyên môn cần chốt điều chỉnh quota lớp/chủ đề và cách hiểu câu góp ý “nên để 1 câu” trước khi đổi quy tắc tự động.


## Trạng thái theo dõi sau chỉnh lý — 2026-11-04

Prototype revised đã được biên tập thành 28 câu synthetic, không chèn trích dẫn giả và tránh câu hỏi chỉ yêu cầu chọn ngày. Các thay đổi này chưa đóng phản hồi giáo viên: ba mẫu VD đang được giữ riêng (`LS-V-002`, `LS-V-004`, `LS-V-007`), và phân hóa nhiễu/độ khó vẫn cần giáo viên xem xét. Bản render prototype 6 trang đang có chưa được xem là bản xác nhận cuối; cần parent tái tạo và kiểm lại.

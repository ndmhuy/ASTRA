# Hồ sơ Lịch sử — bản dùng để soạn đề

**73 mẫu dùng được về nội dung**, trên 25 chủ đề. Không có bước chờ giáo viên: quyết định hiện hành do agent chịu trách nhiệm và có hồ sơ kiểm. Không ghi thành giáo viên phê duyệt hoặc độ khó đã đo bằng bài làm.

- 70 mẫu cũ giữ kết quả giải tách đã có; LS-V-004/007 được phục hồi ở mức TH theo kết quả reviewer cũ.
- LS-V-002 được sửa yêu cầu hỏi không có đáp án trọn vẹn; bản mới có khóa B, mức TH, được agent tự giải và bác từng nhiễu. Không gọi lần sửa này là một lượt blind mới.
- 5 mẫu có nội dung đúng nhưng nhãn VD còn có điều kiện: LS-V-001/003/005/006/008. Giữ mẫu, không dùng riêng chúng chứng minh quota VD nghiêm.
- Coverage theo nhãn cũ **64/67**; theo bằng chứng mức không điều kiện **59/67**, thêm 5 ô có điều kiện và 3 ô VD chỉ đề xuất chưa có mẫu. Các ô đề xuất không phải nội dung sai hoặc quota bắt buộc của đề.

Dùng [SAMPLES](SAMPLES.md), [25 chủ đề](TOPICS.md), [bảng coverage hai trục](COVERAGE.csv) và [quyết định sử dụng](USABILITY-REVIEW.md). Khi cần đúng một quota VD, chọn ô có `strict_level_status=supported`; mẫu có điều kiện vẫn dùng được cho minh họa, học tập hoặc đề không ép quota ấy.

Nguồn corpus giữ nguyên: 1 official + 5 provincial, 240 câu/ý. Một hàng chưa đủ bằng chứng về mức và một nguồn chưa ghép chắc mã/khóa vẫn được giữ; thiếu bằng chứng không biến chúng thành sai. Mẫu synthetic không cộng vào tần suất nguồn.

Tool đã dựng pack trước lượt chỉnh nội dung; lần dựng lại của nhánh này được ghi trong USABILITY-REVIEW.json. Chưa có thử chạy pipeline sinh đề hoặc đo chất lượng trên học sinh; việc đó tách khỏi khả năng dùng tài liệu để soạn đề.

# LaTeX input → mini Composer → LaTeX output

> Đây là exporter draft-only của `mini_cli`. Pipeline có Solver/Reviewer dùng
> `pipeline_cli`, có bốn agent, xuất TikZ/PGFPlots native và chuyển người dùng duyệt
> sau tối đa một phản hồi Reviewer về Composer. Dùng XeLaTeX/LuaLaTeX. Xem
> [pipeline hiện tại](PIPELINE_PLAN_AND_BENCHMARK.md).

CLI nhận request JSON gồm ma trận đề và `exam_family` (`hcm_dgnl` hoặc `thpt`), một file LaTeX mẫu, tùy chọn một kho `QuestionBank` JSON đã chuẩn hóa, nhiều file raw material UTF-8 và prompt điều chỉnh. `--material` được đưa vào Composer dưới dạng `content_support` evidence; file LaTeX mẫu là tham chiếu hình thức. Nội dung file đầu vào không được xem là lệnh hệ thống.

File LaTeX mẫu phải chứa đúng một dòng `%% ASTRA_BODY %%` trong `document`. Giữ preamble, font, margin và lệnh định dạng của nhóm bạn trong mẫu; ASTRA thay marker bằng nội dung đề, đáp án hoặc phiếu tô. Xem `examples/latex_template.tex`. Mẫu không có marker sẽ bị từ chối.

Ví dụ:

```powershell
python -m exam_baseline.mini_cli `
  --request examples/hcm_de11/input.json `
  --template path/to/de_mau.tex `
  --bank path/to/question_bank.json `
  --material path/to/rag_excerpt.txt `
  --prompt "Ưu tiên bối cảnh đời sống, giữ nguyên ma trận" `
  --output runs/hcm_de11/new1
```

`--bank` cần JSON theo schema `QuestionBank` của `models.py`. Có thể bỏ `--bank` nếu chỉ có raw material. Nếu dùng nhiều file material, lặp lại `--material`. Trước khi dùng model thật, đặt provider/key/model trong `.env` theo README. `--fixture` chỉ replay kết quả mẫu.

Đầu ra gồm `de_thi.tex`, `dap_an.tex`, `phieu_tra_loi.tex`, `exam_draft.json`, `student_view.json`, hình trong `figures/` và đáp án private ở thư mục `teacher_private` cạnh thư mục run. Hình dùng đường dẫn tương đối. `dap_an.tex` chỉ được xuất khi mọi câu có đáp án. Không đưa thư mục private hoặc `dap_an.tex` vào gói học sinh.

Profile `hcm_dgnl_de11` kiểm cấu trúc 120 câu của đề tham chiếu. Với đề tốt nghiệp THPT Toán/Lý/Hóa/Anh/Sử/Địa, hãy cung cấp ma trận riêng theo môn và năm thi trong request; chưa có profile cố định cho các môn này vì repo không có đặc tả chính thức tương ứng. Validator kiểm cấu trúc và provenance, chưa chứng minh đáp án đúng, bám chương trình hay đề tương đương về độ khó. Cần Solver/Reviewer và kiểm bản PDF render trước khi phát hành.

Biên dịch bằng XeLaTeX từ **chính thư mục run** để `figures/*.png` được tìm bằng đường dẫn tương đối:

```powershell
xelatex -interaction=nonstopmode -halt-on-error -no-shell-escape de_thi.tex
xelatex -interaction=nonstopmode -halt-on-error -no-shell-escape dap_an.tex
xelatex -interaction=nonstopmode -halt-on-error -no-shell-escape phieu_tra_loi.tex
```

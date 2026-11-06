# PROTOTYPE-AUDIT — một nội dung TeX có hai origin (bổ sung phản hồi giáo viên)

## Đầu vào và phép kiểm
- Nội dung duy nhất: `28eb748d17fc`, hai origin `product` và `corpus` có cùng SHA-256; không đếm thành hai prototype. [TeX](evidence/prototypes/28eb748d17fc/PROTO_thptqg_hoa-hoc_v2.tex), [khóa JSON](evidence/prototypes/28eb748d17fc/keys/PROTO_thptqg_hoa-hoc_v2_Answers.json).
- Đã biên dịch TeX bằng pdflatex và xem PDF 6 trang [PDF render kiểm tra](evidence/prototypes/28eb748d17fc/COMPILED-FOR-AUDIT.pdf), gồm hình vòng đường, sơ đồ ghép kim loại, điện phân và bảng. PDF này **không phải tài liệu gốc được cung cấp**. Không kiểm print/đối sánh runtime.
- Lập phiếu suy luận từ phản ứng và tính toán sau khi đọc TeX, rồi so với khóa kèm; **cùng model, cùng chat đã có thể thấy khóa**, không blind hay teacher-approved.
- Có 18 MCQ + 4 TF×4 ý + 6 đáp số số = **40 slot kiểm**; đối chiếu cùng khóa **40/40**, bất đồng khóa 0. **40/40 chỉ đo khớp phép giải với khóa, không phải 40/40 câu đủ điều kiện phát hành**. Phản hồi giáo viên đã xác định các vấn đề về tính nhất quán, hình, trình bày và độ phân hóa; prototype vẫn ở trạng thái **hold phát hành** tới khi sửa và render kiểm tra. Xem [phản hồi giáo viên](TEACHER-FEEDBACK.md).

## Audit từng câu/ý
| Địa chỉ | Nhóm | Mức suy xét | Khóa suy/khóa file | Đủ? | Nhận xét nội dung, dữ kiện, nhiễu |
|---|---|---|---|---|---|
| `P1.1` | T09 | NB | C/C | khớp | Na tác dụng với nước thường; Ag/Cu không, Fe không phản ứng mạnh như kim loại kiềm. Các kim loại không cùng lớp hoạt tính; nhiễu Ag, Cu, Fe bỏ tiêu chí phản ứng nhanh với nước. |
| `P1.2` | T03 | NB | B/B | khớp | Nhóm N nối trực tiếp với hai gốc methyl là amine bậc hai. Ba lựa chọn còn lại lần lượt là amine bậc 1, bậc 3 hoặc bậc 1 thơm. |
| `P1.3` | T02 | TH | A/A | khớp khóa; **sửa hình** | Hình vòng 5 cạnh với hai nhánh CH₂OH phù hợp fructose dạng furanose. Bộ nhiễu trộn monosaccharide với disaccharide; cần xem hình, không chỉ tên. |
| `P1.4` | T05 | TH | C/C | khớp | E° = 0,80−(−0,76)=1,56 V. Các phương án khác biểu thị đổi dấu/cộng thế sai. |
| `P1.5` | T01 | NB | A/A | khớp | CH₃COOC₂H₅ + NaOH → CH₃COONa + C₂H₅OH. Các phương án nhiễu hoán đổi gốc ester hoặc cho acid tự do trong kiềm. |
| `P1.6` | T01 | TH | B/B | khớp | Hydrogen hóa các liên kết C=C trong triolein tạo tristearin. Trilinolein không phải chất bão hòa; tripalmitin sai số carbon; glycerol không còn là triester. |
| `P1.7` | T04 | NB | C/C | khớp | Nylon-6,6 được tạo qua trùng ngưng diamine/diacid; ba polymer còn lại trùng hợp. Nhiễu là polymer trùng hợp thông dụng. |
| `P1.8` | T03 | NB | A/A | khớp | Lysine mang nhóm amino bên thêm nên dung dịch có tính base. Glu acid còn glycine/alanine gần trung tính trong tình huống quen thuộc. |
| `P1.9` | T10 | TH | A/A | khớp | Nhỏ NH₃ tạo Cu(OH)₂, NH₃ dư tạo phức xanh đậm hòa tan. Nhiễu phủ nhận tạo phức hoặc nhầm màu kết tủa. |
| `P1.10` | T11 | TH | D/D | khớp | Z=17 là chlorine, phân bố 2–8–7, chu kì 3 nhóm VIIA. Nhiễu nhầm chu kì/nhóm dựa trên số lớp và electron hóa trị. |
| `P1.11` | T06 | TH | A/A | khớp | Anode trơ điện phân CuSO₄: H₂O bị oxi hóa, không phải SO₄²⁻. Đảo vị trí oxi hóa/khử và nhầm tác nhân oxi hóa. |
| `P1.12` | T09 | TH | B/B | khớp | CO₃²⁻ làm kết tủa CaCO₃, MgCO₃ thích hợp để loại ion gây cứng. Chất khác không đồng thời loại Ca²⁺ và Mg²⁺ theo điều kiện nêu. |
| `P1.13` | T07 | TH | A/A | khớp | Cu quý hơn Fe; ghép Cu làm Fe ở vị trí anode ăn mòn mạnh hơn. Mg/Zn/Al thường đóng vai trò anode hi sinh nếu điều kiện phù hợp. |
| `P1.14` | T01 | TH | C/C | khớp | 8,8/88=0,10 mol ethyl acetate; tạo 0,10 mol CH₃COONa, m=8,2g. Nhiễu m khác do dùng khối lượng mol alcohol hoặc ester. |
| `P1.15` | T02 | TH | C/C | khớp | 36/180=0,20 mol glucose; CO₂ lý thuyết 0,40 mol; thực tế 0,32 mol; V=7,9328L. Nhiễu bỏ hệ số 2, hiệu suất hoặc hệ số thể tích khí. |
| `P1.16` | T03 | TH | B/B | khớp | M(ethylamine)=45; n=4,5/45=0,10; M(muối)=81,5; m=8,15g. Nhiễu nhầm muối ammonium hoặc khối lượng HCl tham gia. |
| `P1.17` | T03 | NB | A/A | khớp | Protein đơn giản thủy phân hoàn toàn tạo các α-amino acid. Nhiễu khẳng định protein không đông tụ, mọi protein tan hoặc nhận sai liên kết peptide. |
| `P1.18` | T08 | TH | D/D | khớp | nH₂=9,916/24,79=0,40; đặt x=mol Mg, y=mol Al: x+1,5y=0,4; 24x+27y=7,8 ⇒ y=0,2mol, mAl=5,4g. Nhiễu do hệ số khí của Al hoặc giải hệ tỉ lượng sai. |
| `P2.1.a` | T06 | NB | D/D | khớp | a: cathode nhận Cu; b: anode thoát O₂, không phải H₂; c: Q/F≈0,04 mol e ⇒ mCu≈1,28g; d: tạo H⁺ nên pH giảm. Tính Faraday hai electron trên một ion Cu²⁺; điều kiện Cu²⁺ còn dư quan trọng. |
| `P2.1.b` | T06 | TH | S/S | khớp | a: cathode nhận Cu; b: anode thoát O₂, không phải H₂; c: Q/F≈0,04 mol e ⇒ mCu≈1,28g; d: tạo H⁺ nên pH giảm. Tính Faraday hai electron trên một ion Cu²⁺; điều kiện Cu²⁺ còn dư quan trọng. |
| `P2.1.c` | T06 | TH | D/D | khớp | a: cathode nhận Cu; b: anode thoát O₂, không phải H₂; c: Q/F≈0,04 mol e ⇒ mCu≈1,28g; d: tạo H⁺ nên pH giảm. Tính Faraday hai electron trên một ion Cu²⁺; điều kiện Cu²⁺ còn dư quan trọng. |
| `P2.1.d` | T06 | TH | S/S | khớp | a: cathode nhận Cu; b: anode thoát O₂, không phải H₂; c: Q/F≈0,04 mol e ⇒ mCu≈1,28g; d: tạo H⁺ nên pH giảm. Tính Faraday hai electron trên một ion Cu²⁺; điều kiện Cu²⁺ còn dư quan trọng. |
| `P2.2.a` | T02 | NB | D/D | khớp | a: Tollens tạo bạc; b: glucose là chất khử; c: saccharose chưa thủy phân không tráng bạc; d: 0,9/180×2×108=1,08g Ag. Kết hợp chức aldehyde dạng mở vòng với thay đổi số oxi hóa; không suy mọi disaccharide là đường khử. |
| `P2.2.b` | T02 | TH | S/S | khớp | a: Tollens tạo bạc; b: glucose là chất khử; c: saccharose chưa thủy phân không tráng bạc; d: 0,9/180×2×108=1,08g Ag. Kết hợp chức aldehyde dạng mở vòng với thay đổi số oxi hóa; không suy mọi disaccharide là đường khử. |
| `P2.2.c` | T02 | TH | S/S | khớp | a: Tollens tạo bạc; b: glucose là chất khử; c: saccharose chưa thủy phân không tráng bạc; d: 0,9/180×2×108=1,08g Ag. Kết hợp chức aldehyde dạng mở vòng với thay đổi số oxi hóa; không suy mọi disaccharide là đường khử. |
| `P2.2.d` | T02 | TH | D/D | khớp phép tính; **sửa dữ kiện/ngữ cảnh** | a: Tollens tạo bạc; b: glucose là chất khử; c: saccharose chưa thủy phân không tráng bạc; d: 0,9/180×2×108=1,08g Ag. Kết hợp chức aldehyde dạng mở vòng với thay đổi số oxi hóa; không suy mọi disaccharide là đường khử. |
| `P2.3.a` | T01 | NB | D/D | khớp | a: muối acid béo nổi khi tách muối; b: NaCl làm giảm độ tan sản phẩm, không thúc đẩy tốc độ chính; c: thêm nước tránh cạn; d: 8,9/890=0,01mol tristearin → 0,92g glycerol, không phải 2,76g. Nhiễu d nhầm ba mol glycerol trên một mol triglyceride. |
| `P2.3.b` | T01 | TH | S/S | khớp | a: muối acid béo nổi khi tách muối; b: NaCl làm giảm độ tan sản phẩm, không thúc đẩy tốc độ chính; c: thêm nước tránh cạn; d: 8,9/890=0,01mol tristearin → 0,92g glycerol, không phải 2,76g. Nhiễu d nhầm ba mol glycerol trên một mol triglyceride. |
| `P2.3.c` | T01 | TH | D/D | khớp | a: muối acid béo nổi khi tách muối; b: NaCl làm giảm độ tan sản phẩm, không thúc đẩy tốc độ chính; c: thêm nước tránh cạn; d: 8,9/890=0,01mol tristearin → 0,92g glycerol, không phải 2,76g. Nhiễu d nhầm ba mol glycerol trên một mol triglyceride. |
| `P2.3.d` | T01 | TH | S/S | khớp | a: muối acid béo nổi khi tách muối; b: NaCl làm giảm độ tan sản phẩm, không thúc đẩy tốc độ chính; c: thêm nước tránh cạn; d: 8,9/890=0,01mol tristearin → 0,92g glycerol, không phải 2,76g. Nhiễu d nhầm ba mol glycerol trên một mol triglyceride. |
| `P2.4.a` | T13 | NB | D/D | khớp | a: endpoint phenolphthalein từ hồng sang không màu; b: Vtb=10,0mL; c: CNaOH=0,100M, không phải 0,010M; d: HCl chuẩn ở burette, không phải pipette. Nhiễu nhầm vị trí dụng cụ hoặc hệ số mL khi quy đổi nồng độ. |
| `P2.4.b` | T13 | TH | D/D | khớp | a: endpoint phenolphthalein từ hồng sang không màu; b: Vtb=10,0mL; c: CNaOH=0,100M, không phải 0,010M; d: HCl chuẩn ở burette, không phải pipette. Nhiễu nhầm vị trí dụng cụ hoặc hệ số mL khi quy đổi nồng độ. |
| `P2.4.c` | T13 | TH | S/S | khớp | a: endpoint phenolphthalein từ hồng sang không màu; b: Vtb=10,0mL; c: CNaOH=0,100M, không phải 0,010M; d: HCl chuẩn ở burette, không phải pipette. Nhiễu nhầm vị trí dụng cụ hoặc hệ số mL khi quy đổi nồng độ. |
| `P2.4.d` | T13 | TH | S/S | khớp | a: endpoint phenolphthalein từ hồng sang không màu; b: Vtb=10,0mL; c: CNaOH=0,100M, không phải 0,010M; d: HCl chuẩn ở burette, không phải pipette. Nhiễu nhầm vị trí dụng cụ hoặc hệ số mL khi quy đổi nồng độ. |
| `P3.1` | T04 | TH | 145/145 | khớp | 1, 4, 5 là các polymer điều chế bằng trùng hợp; nylon-6,6 trùng ngưng, cellulose tự nhiên. Nhập 145 là mã các vị trí, không phải giá trị lượng vật lí. Dạng mã số của câu trả lời ngắn: lưu ý khác nhiệm vụ tính số. |
| `P3.2` | T01 | TH | 4/4 | khớp khóa; **sửa lời dẫn** | Có 4 ester C₄H₈O₂ no mạch hở: methyl propanoate, ethyl acetate, propyl formate và isopropyl formate. Hướng dẫn “làm tròn” không cần thiết khi đếm số đồng phân nguyên. |
| `P3.3` | T08 | TH | 2,43/2,43 | khớp | 10×0,51×(54/102)×0,90=2,43 tấn Al. Chủ yếu tỉ lượng + hiệu suất theo công thức có sẵn, không đủ chứng minh VD. |
| `P3.4` | T03 | TH | 20,8/20,8 | khớp | Gly-Ala M=146; n=0,1 mol. Muối glycine Na M=97 và alanine Na M=111, tổng 20,8 g. Thủy phân hai đầu amide/acid trong kiềm; các bước thường quy. |
| `P3.5` | T20 | TH | 158/158 | khớp | Phần khối lượng nitrogen trong phân 95% urea =0,95×28/60; m cần=70/(0,95×28/60)=157,895kg ⇒158kg. Đổi thành phần phân bón và làm tròn theo phần trăm khối lượng. |
| `P3.6` | T15 | TH | 223/223 | khớp | ΔHcháy=−393,5+2(−285,8)−(−74,9)=−890,2 kJ/mol; nCH₄=4/16=0,25 ⇒222,55kJ, làm tròn 223. Lập Hess và nhân mol, vẫn là vận hành quy trình quen thuộc. |

## Nhận định và hướng sửa cụ thể
- **P1.3 (giáo viên yêu cầu sửa):** hình chemfig đã render nhưng cần **thay bằng Haworth thể hiện rõ hướng nhóm OH/CH₂OH** và kiểm hóa học sau render. Đây là lỗi/thiếu rõ ràng của biểu diễn, **không phải thiếu file ảnh**. Chưa được coi là đáp ứng yêu cầu giáo viên.
- **P1.13:** hình TikZ nối Fe/M trong đất ẩm đã render được. Bổ sung câu dẫn nêu tiếp xúc điện thật và môi trường điện li để loại bỏ ngộ nhận về ăn mòn khi mạch hở.
- **P2.1.c:** định luật Faraday với Cu²⁺ là phép tính thường quy, không tự gọi VD. **P2.3.d:** cần kiểm ba gốc acid béo và chỉ một glycerol trên triglyceride, nhiễu 2,76 g là nhân sai 3 lần.
- **P3.1:** mã “145” là phép mã hóa danh sách polymer (không phải lượng vật lí); trình bày cho chấm tự động cần ràng buộc nhập đúng ba chữ số, không được hoán vị. **P3.2:** giáo viên xác nhận **cần bỏ** “làm tròn đến chữ số hàng đơn vị” vì kết quả đếm đồng phân phải là số nguyên.
- **P3.3–P3.6:** chủ yếu thực hiện công thức/tỉ lượng quen thuộc; tạm xếp TH dù nhiều phép tính hoặc tình huống sản xuất. Không đạt định nghĩa VD chỉ bằng độ dài; cần thay nhiệm vụ bằng xây dựng mô hình hoặc dữ liệu độc lập, không chỉ tăng số.
- **Nhiễu MCQ:** đã rà theo từng câu P1 ở bảng, nhưng không có bài làm học sinh nên đây là giả thuyết lỗi, không thể kết luận phân hóa thực nghiệm. TF sai kiểm từng ý.
- **Danh pháp/đủ dữ kiện:** giữ tên hóa chất tiếng Anh như methane, glucose, glycerol, nylon. Kiểm tra dấu ΔH, thể tích mol 24,79 L, F; không sửa TeX gốc. Các giả thiết hiệu suất và ion Cu²⁺ dư đã có cho phép giải duy nhất.
- **Giới hạn:** không thử engine render của sản phẩm, không so khớp pipeline, không đo học sinh; xem [data/prototype-audit.json](data/prototype-audit.json) và [phiếu tự giải](data/prototype-solve-first.json).

## Bổ sung: nhận xét giáo viên và các gate nghiệm thu (04/11/2026)

- **P2.2.d — tính đúng không đủ:** phương trình tạo bạc cho 0,9 g glucose dư thuốc thử dẫn đến **1,08 g Ag** là đúng về số học, nhưng không thể gắn trực tiếp giả thiết đó vào **thí nghiệm phía trên** vốn định lượng thuốc thử ít hơn. Sửa ngữ cảnh: “**Trong một thí nghiệm khác, cho 0,9 gam glucose phản ứng hoàn toàn với dung dịch AgNO₃/NH₃ dư thì thu được 1,08 gam Ag.**” Không đổi đáp án sang sai vì nhận xét đang yêu cầu tách thí nghiệm, không phủ nhận kết quả.
- **Hình fructose P1.3:** có bản render cũ nhưng chưa đạt chuẩn rõ hướng nhóm thế; phải vẽ Haworth và kiểm sau render bằng người có chuyên môn.
- **P3.2:** bỏ chỉ dẫn làm tròn trong câu đếm số nguyên.
- **Dàn trang:** câu hỏi và tất cả phương án không được ngắt trang; rà cả chùm/TF; giảm khoảng trắng trang cuối; chưa có PDF bản sửa được duyệt.
- **Toàn đề:** kết luận giáo viên: khá nhẹ, một số kiến thức lặp, **chỉ phù hợp ôn tập cơ bản sau sửa**; muốn luyện thi phân hóa cần rà cơ cấu và thêm nhiệm vụ VD thực chất. Không suy từ feedback này ra tỉ lệ NB/TH/VD định lượng hoặc phân hóa thực nghiệm.

**Phạm vi kiểm định:** các cờ trên là phản hồi chuyên môn được **người dùng chuyển tiếp**; không kiểm chứng danh tính/nghiệm thu độc lập. `status=pass_same_model` của các dòng dữ liệu gốc **chỉ** có nghĩa khớp giải/khóa; `editorial_gate` trong [data/prototype-audit.json](data/prototype-audit.json) và [data/teacher-feedback.json](data/teacher-feedback.json) theo dõi điều kiện phát hành riêng. Không chỉnh sửa bằng chứng LaTeX gốc.


## Addendum — revised prototype compile/layout review (04/11/2026)

This addendum records the current revised artifact; the audit above remains historical and unchanged. The revised TeX/PDF and verification receipt are [prototype-revised/prototype.tex](prototype-revised/prototype.tex), [prototype-revised/prototype.pdf](prototype-revised/prototype.pdf), and [verification.json](prototype-revised/verification.json).

- Implemented the separate experiment context for P2.2.d, changed P3.1 to a scalar answer of 3, and removed the rounding instruction from P3.2 because the isomer count is an integer.
- The revised selection contains 8 reviewed replacements: 4 MCQ and 4 VD short-answer questions. The other 20 legacy questions remain in the paper; their content has not been independently verified.
- Compiled with pdflatex in two passes; all 7 rendered pages were reviewed for layout. The Haworth diagram lower-right substituent labels were moved to below-right placement; final pages 1 and 7 were visually reviewed. Only page 1 pixels changed from the pre-fix frame set; the earlier frame hashes are retained at [hoa-frames-before-figure-fix.json](../../audit/outputs/scoped-three/hoa-frames-before-figure-fix.json).
- Scope is compile and rendered layout only. This does not certify answer/content correctness, teacher acceptance, runtime integration, or release readiness. Teacher and runtime acceptance remain false.

"""M0 sample matrix: GDKT&PL (THPTQG, 24 MCQ + 4 TF = 28 cau, 40 units of 0.25 = 10 marks).
ORIGINAL and abstract: topics from the Ket noi tri thuc lesson list, requirements written for this sample, cau numbering
chosen here. Nothing is copied from an official paper. Run with the app venv:  build.py  (writes next to itself)."""
import json, os, sys, io
from pathlib import Path
HERE = Path(__file__).resolve().parent
GT = Path("/Users/huynguyen/Lecturing_Lab/lab-r1/work-r0/Grading_Tools")

LEVELS = ["NB", "TH", "VD"]
LV_VI = {"NB": "Biết", "TH": "Hiểu", "VD": "Vận dụng"}
UNIT_MARK = 0.25

# bài id -> (chủ đề, tên bài)  [Kết nối tri thức, lớp 12]
BAI = {
 1: ("Chủ đề 1: Tăng trưởng, phát triển và hội nhập kinh tế", "Bài 1: Tăng trưởng và phát triển kinh tế"),
 2: ("Chủ đề 1: Tăng trưởng, phát triển và hội nhập kinh tế", "Bài 2: Hội nhập kinh tế quốc tế"),
 3: ("Chủ đề 2: Bảo hiểm và an sinh xã hội", "Bài 3: Bảo hiểm"),
 4: ("Chủ đề 2: Bảo hiểm và an sinh xã hội", "Bài 4: An sinh xã hội"),
 5: ("Chủ đề 3: Kinh doanh và trách nhiệm xã hội của doanh nghiệp", "Bài 5: Lập kế hoạch kinh doanh"),
 6: ("Chủ đề 3: Kinh doanh và trách nhiệm xã hội của doanh nghiệp", "Bài 6: Trách nhiệm xã hội của doanh nghiệp"),
 7: ("Chủ đề 4: Quản lí thu, chi trong gia đình", "Bài 7: Quản lí thu, chi trong gia đình"),
 8: ("Chủ đề 5: Quyền và nghĩa vụ của công dân", "Bài 8: Quyền và nghĩa vụ của công dân về kinh doanh và nộp thuế"),
 9: ("Chủ đề 5: Quyền và nghĩa vụ của công dân", "Bài 9: Quyền và nghĩa vụ của công dân về sở hữu tài sản và tôn trọng tài sản của người khác"),
 10: ("Chủ đề 5: Quyền và nghĩa vụ của công dân", "Bài 10: Quyền và nghĩa vụ của công dân trong hôn nhân và gia đình"),
 11: ("Chủ đề 5: Quyền và nghĩa vụ của công dân", "Bài 11: Quyền và nghĩa vụ của công dân trong học tập"),
 12: ("Chủ đề 5: Quyền và nghĩa vụ của công dân", "Bài 12: Quyền và nghĩa vụ của công dân trong bảo vệ, chăm sóc sức khoẻ; bảo đảm an sinh xã hội"),
 13: ("Chủ đề 5: Quyền và nghĩa vụ của công dân", "Bài 13: Quyền và nghĩa vụ của công dân trong bảo vệ di sản văn hoá, môi trường và tài nguyên thiên nhiên"),
 14: ("Chủ đề 6: Pháp luật quốc tế", "Bài 14: Một số vấn đề chung về pháp luật quốc tế"),
 15: ("Chủ đề 6: Pháp luật quốc tế", "Bài 15: Công pháp quốc tế về dân cư, lãnh thổ và chủ quyền quốc gia"),
 16: ("Chủ đề 6: Pháp luật quốc tế", "Bài 16: Nguyên tắc cơ bản của Tổ chức Thương mại thế giới và hợp đồng thương mại quốc tế"),
}

NL = {"NL.1": "Nhận thức kinh tế – pháp luật", "NL.2": "Tìm hiểu hoạt động kinh tế – xã hội", "NL.3": "Vận dụng kiến thức, kĩ năng"}

# (index, bai, level, requirement, style, competency)
P1 = [
 (1, 1, "NB", "Nêu được khái niệm tăng trưởng kinh tế và một chỉ tiêu thường dùng để đo tăng trưởng", "khái niệm trực tiếp, 4 phương án ngắn", "NL.1"),
 (2, 2, "NB", "Nhận biết được mục tiêu hoặc một hình thức cơ bản của hội nhập kinh tế quốc tế", "khái niệm trực tiếp", "NL.1"),
 (3, 3, "NB", "Nêu được khái niệm bảo hiểm và vai trò của bảo hiểm đối với cá nhân, gia đình", "khái niệm trực tiếp", "NL.1"),
 (4, 4, "NB", "Kể được một chính sách an sinh xã hội cơ bản của Nhà nước", "khái niệm trực tiếp", "NL.1"),
 (5, 5, "NB", "Nêu được tên các bước của quy trình lập kế hoạch kinh doanh theo đúng trình tự", "khái niệm trực tiếp", "NL.1"),
 (6, 6, "NB", "Nhận biết được một biểu hiện thực hiện trách nhiệm xã hội của doanh nghiệp", "khái niệm trực tiếp", "NL.1"),
 (7, 7, "NB", "Nêu được khái niệm khoản thu, khoản chi và nguyên tắc cơ bản của quản lí thu, chi trong gia đình", "khái niệm trực tiếp", "NL.1"),
 (8, 8, "NB", "Nêu được quyền tự do kinh doanh và nghĩa vụ nộp thuế của công dân", "khái niệm trực tiếp", "NL.1"),
 (9, 9, "NB", "Nhận biết được quyền sở hữu tài sản hợp pháp của công dân", "khái niệm trực tiếp", "NL.1"),
 (10, 10, "NB", "Nêu được một nguyên tắc cơ bản của chế độ hôn nhân và gia đình", "khái niệm trực tiếp", "NL.1"),
 (11, 13, "NB", "Nhận biết được hành vi bảo vệ di sản văn hoá hoặc môi trường theo quy định của pháp luật", "tình huống một câu", "NL.1"),
 (12, 14, "NB", "Nêu được khái niệm pháp luật quốc tế và một nguồn cơ bản của pháp luật quốc tế", "khái niệm trực tiếp", "NL.1"),
 (13, 1, "TH", "Phân biệt tăng trưởng kinh tế với phát triển kinh tế dựa vào một dữ kiện cho trước", "dữ kiện ngắn kèm yêu cầu phân biệt", "NL.1"),
 (14, 3, "TH", "Phân biệt bảo hiểm xã hội, bảo hiểm y tế và bảo hiểm thương mại trong một tình huống ngắn", "tình huống 2–3 dòng", "NL.1"),
 (15, 5, "TH", "Giải thích được vai trò của một bước trong quy trình lập kế hoạch kinh doanh", "tình huống 2–3 dòng", "NL.1"),
 (16, 7, "TH", "Giải thích được vì sao cần cân đối thu, chi; phân loại khoản chi cần thiết và khoản chi điều chỉnh được", "tình huống kèm số liệu đơn giản", "NL.1"),
 (17, 9, "TH", "Giải thích được giới hạn của quyền sở hữu: phải tôn trọng tài sản của người khác", "tình huống 2–3 dòng", "NL.1"),
 (18, 11, "TH", "Giải thích được quyền và nghĩa vụ học tập của công dân qua một tình huống học đường", "tình huống 2–3 dòng", "NL.1"),
 (19, 12, "TH", "Phân biệt quyền được bảo vệ, chăm sóc sức khoẻ với trách nhiệm tham gia bảo hiểm y tế", "tình huống 2–3 dòng", "NL.1"),
 (20, 15, "TH", "Giải thích được các bộ phận cấu thành lãnh thổ quốc gia theo công pháp quốc tế", "khái niệm kèm ví dụ", "NL.1"),
 (21, 2, "VD", "Xác định lợi ích hoặc thách thức mà một doanh nghiệp gặp phải trong một tình huống hội nhập cụ thể", "tình huống 4–5 dòng có nhân vật", "NL.3"),
 (22, 6, "VD", "Đánh giá việc một doanh nghiệp thực hiện trách nhiệm xã hội trong tình huống có cả mặt tích cực và mặt hạn chế", "tình huống 4–5 dòng có nhân vật", "NL.3"),
 (23, 8, "VD", "Xác định nghĩa vụ thuế của chủ thể kinh doanh trong một tình huống có số liệu đơn giản", "tình huống kèm số liệu", "NL.3"),
 (24, 16, "VD", "Vận dụng một nguyên tắc của Tổ chức Thương mại thế giới để nhận xét một tình huống thương mại giả định", "tình huống 4–5 dòng", "NL.3"),
]

# P2: one câu = one situation = one bài; ý a NB, b TH, c VD, d VD (4 ý x 0.25 average = 1.0 per câu)
P2_CAU = {
 1: (1, "bảng số liệu hai năm của một nền kinh tế (tổng sản phẩm, thu nhập bình quân, một chỉ tiêu xã hội) kèm 3–4 dòng mô tả",
     [("a", "NB", "Nhận biết chỉ tiêu tăng trưởng kinh tế xuất hiện trong số liệu", "NL.1"),
      ("b", "TH", "Giải thích mối quan hệ giữa tăng trưởng kinh tế và một chỉ tiêu phát triển xã hội nêu trong số liệu", "NL.1"),
      ("c", "VD", "Đánh giá mức tăng trưởng giữa hai năm bằng phép so sánh hoặc tính tỉ lệ đơn giản từ số liệu", "NL.3"),
      ("d", "VD", "Đánh giá một giải pháp để tăng trưởng đi cùng phát triển bền vững", "NL.3")]),
 2: (6, "tình huống 6–8 dòng về một doanh nghiệp (A) với hoạt động sản xuất và hoạt động cộng đồng",
     [("a", "NB", "Nhận biết hoạt động của doanh nghiệp thể hiện trách nhiệm kinh tế hoặc pháp lí", "NL.1"),
      ("b", "TH", "Phân biệt hoạt động thể hiện trách nhiệm đạo đức với hoạt động từ thiện", "NL.1"),
      ("c", "VD", "Đánh giá hành vi của doanh nghiệp là phù hợp hay chưa phù hợp với trách nhiệm xã hội", "NL.3"),
      ("d", "VD", "Đánh giá cách ứng xử của một nhân vật trong tình huống đối với doanh nghiệp", "NL.3")]),
 3: (9, "tình huống 6–8 dòng về một gia đình có tài sản chung, việc tặng cho hoặc để lại tài sản và một tranh chấp nhỏ",
     [("a", "NB", "Nhận biết chủ thể có quyền sở hữu tài sản nêu trong tình huống", "NL.1"),
      ("b", "TH", "Giải thích quyền của chủ sở hữu hoặc giới hạn của quyền đó trong tình huống", "NL.1"),
      ("c", "VD", "Xác định hành vi của một nhân vật là đúng hay sai quy định về tôn trọng tài sản của người khác", "NL.3"),
      ("d", "VD", "Đánh giá cách giải quyết tranh chấp mà các nhân vật lựa chọn", "NL.3")]),
 4: (15, "tình huống 6–8 dòng giả định về một quốc gia ven biển, lãnh thổ và hoạt động của công dân nước khác",
     [("a", "NB", "Nhận biết bộ phận lãnh thổ quốc gia được nhắc tới trong tình huống", "NL.1"),
      ("b", "TH", "Giải thích quyền của quốc gia đối với bộ phận lãnh thổ đó theo công pháp quốc tế", "NL.1"),
      ("c", "VD", "Xác định hành vi của công dân nước khác trong tình huống là phù hợp hay vi phạm", "NL.3"),
      ("d", "VD", "Đánh giá cách ứng xử của cơ quan hoặc cá nhân trong tình huống theo nguyên tắc tôn trọng chủ quyền", "NL.3")]),
}

LEVEL_CUES = {
 "NB": "nêu, kể tên, nhận biết, chỉ ra; một khái niệm hoặc một sự kiện trực tiếp, không cần suy luận",
 "TH": "phân biệt, giải thích, so sánh, sắp xếp; hiểu bản chất trong một dữ kiện hoặc tình huống ngắn",
 "VD": "xác định, đánh giá, vận dụng; tình huống mới có nhân vật hoặc số liệu, người học phải kết luận và nêu lí do",
}


def tt_cell(index): return f"C{index}"
def tf_cell(cau, st): return f"{cau}{st.upper()}"


def build_rows():
    rows = []
    # P1: one row per (bài, level), in bài order then level order
    for bid in sorted(BAI):
        chude, ten = BAI[bid]
        for lv in LEVELS:
            items = [p for p in P1 if p[1] == bid and p[2] == lv]
            if not items:
                continue
            rows.append({
                "part_id": "P1", "topic": ten, "chu_de": chude, "level": lv, "count": len(items),
                "references": [{"index": i[0]} for i in items],
                "marks": round(len(items) * UNIT_MARK, 2),
                "note": "; ".join(f"Câu {i[0]}: {i[3]}" for i in items),
                "items": [{"ref": f"C{i[0]}", "requirement": i[3], "style": i[4], "competency": i[5], "marks": UNIT_MARK} for i in items],
            })
    # P2: one row per (câu's bài, level)
    for cau, (bid, stem, sts) in P2_CAU.items():
        chude, ten = BAI[bid]
        for lv in LEVELS:
            items = [s for s in sts if s[1] == lv]
            if not items:
                continue
            rows.append({
                "part_id": "P2", "topic": ten, "chu_de": chude, "level": lv, "count": None, "count_unit": "statement",
                "references": [{"index": cau, "statement": s[0]} for s in items],
                "marks": round(len(items) * UNIT_MARK, 2),
                "note": "; ".join(f"Ý {cau}{s[0]}: {s[2]}" for s in items),
                "items": [{"ref": f"{cau}{s[0]}", "requirement": s[2], "style": f"ý {s[0]} của câu {cau}: {stem}", "competency": s[3], "marks": UNIT_MARK} for s in items],
            })
    return rows


def totals(rows):
    t = {"by_part_cau": {"P1": 24, "P2": 4}, "units": {"P1": 24, "P2": 16}, "by_level_units": {lv: 0 for lv in LEVELS},
         "by_part_level_units": {"P1": {lv: 0 for lv in LEVELS}, "P2": {lv: 0 for lv in LEVELS}}, "marks": 0.0, "by_bai_units": {}}
    for r in rows:
        n = len(r["references"])
        t["by_level_units"][r["level"]] += n
        t["by_part_level_units"][r["part_id"]][r["level"]] += n
        t["marks"] += r["marks"]
        t["by_bai_units"][r["topic"]] = t["by_bai_units"].get(r["topic"], 0) + n
    t["marks"] = round(t["marks"], 2)
    t["by_level_percent"] = {lv: round(100 * t["by_level_units"][lv] / 40, 1) for lv in LEVELS}
    return t


def document():
    rows = build_rows()
    return {
        "version": 1, "levels": LEVELS,
        "subject": "GDKTPL", "exam_type": "THPTQG",
        "source": "mẫu M0 (2026-10-26), tự soạn, trừu tượng; không phải ma trận chính thức của đề nào",
        "built_from": "m0_sample",
        "level_cues": LEVEL_CUES,
        "competencies": NL,
        "scoring": {"P1": "mỗi câu 0,25 điểm", "P2": "mỗi câu 1,0 điểm (4 ý, điểm theo số ý đúng); trung bình 0,25 điểm mỗi ý",
                    "total": 10.0, "duration_minutes": 50},
        "totals": totals(rows),
        "rows": rows,
    }


# -------- tables for the Word file (the importer reads these with no assistant call) --------
def table_I():
    head = ["TT", "Chủ đề", "Nội dung/đơn vị kiến thức",
            "Nhiều lựa chọn - Biết", "Nhiều lựa chọn - Hiểu", "Nhiều lựa chọn - Vận dụng",
            "Đúng sai - Biết", "Đúng sai - Hiểu", "Đúng sai - Vận dụng",
            "Tổng - Biết", "Tổng - Hiểu", "Tổng - Vận dụng", "Tỷ lệ % điểm"]
    out = [head]
    sums = {"mc": {lv: 0 for lv in LEVELS}, "tf": {lv: 0 for lv in LEVELS}}
    tt = 0
    for bid in sorted(BAI):
        chude, ten = BAI[bid]
        tt += 1
        mc = {lv: [f"C{p[0]}" for p in P1 if p[1] == bid and p[2] == lv] for lv in LEVELS}
        tf = {lv: [tf_cell(c, s[0]) for c, (b, _st, sts) in P2_CAU.items() if b == bid for s in sts if s[1] == lv] for lv in LEVELS}
        units = sum(len(v) for v in mc.values()) + sum(len(v) for v in tf.values())
        tot = {lv: len(mc[lv]) + len(tf[lv]) for lv in LEVELS}
        for lv in LEVELS:
            sums["mc"][lv] += len(mc[lv]); sums["tf"][lv] += len(tf[lv])
        pct = f"{100 * units * UNIT_MARK / 10:g}".replace(".", ",")
        out.append([str(tt), chude, ten] + [" ".join(mc[lv]) for lv in LEVELS] + [" ".join(tf[lv]) for lv in LEVELS]
                   + [str(tot[lv]) if tot[lv] else "" for lv in LEVELS] + [pct])
    mcn = [sums["mc"][lv] for lv in LEVELS]; tfn = [sums["tf"][lv] for lv in LEVELS]
    totn = [mcn[i] + tfn[i] for i in range(3)]
    f = lambda x: f"{x:g}".replace(".", ",")
    out.append(["", "Tổng số câu", ""] + [str(x) for x in mcn] + [str(x) for x in tfn] + [str(x) for x in totn] + ["100"])
    out.append(["", "Tổng số điểm", ""] + [f(x * UNIT_MARK) for x in mcn] + [f(x * UNIT_MARK) for x in tfn] + [f(x * UNIT_MARK) for x in totn] + ["10"])
    out.append(["", "Tỷ lệ %", ""] + ["", "", ""] + ["", "", ""] + [f(100 * x / 40) for x in totn] + ["100"])
    return out


def table_II():
    out = [["TT", "Chủ đề", "Nội dung/đơn vị kiến thức", "Mức độ", "Yêu cầu cần đạt", "Câu", "Dạng", "Năng lực"]]
    n = 0
    for bid in sorted(BAI):
        chude, ten = BAI[bid]
        for lv in LEVELS:
            for p in [p for p in P1 if p[1] == bid and p[2] == lv]:
                n += 1
                out.append([str(n), chude, ten, LV_VI[lv], p[3], f"C{p[0]}", "Nhiều lựa chọn", p[5]])
        for cau, (b, _stem, sts) in P2_CAU.items():
            if b != bid: continue
            for lv in LEVELS:
                for s in [s for s in sts if s[1] == lv]:
                    n += 1
                    out.append([str(n), chude, ten, LV_VI[lv], s[2], tf_cell(cau, s[0]), "Đúng sai", s[3]])
    return out


def _landscape(data: bytes) -> bytes:
    """A4 landscape, narrow margins, 8 pt table text, full-width tables: the grid is 13 columns wide. Layout only."""
    import re, zipfile
    zin = zipfile.ZipFile(io.BytesIO(data)); out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            raw = zin.read(item.filename)
            if item.filename == "word/document.xml":
                x = raw.decode("utf-8")
                x = x.replace("<w:sectPr/>", '<w:sectPr><w:pgSz w:w="16838" w:h="11906" w:orient="landscape"/>'
                              '<w:pgMar w:top="720" w:right="720" w:bottom="720" w:left="720" w:header="360" w:footer="360" w:gutter="0"/></w:sectPr>')
                x = x.replace("<w:tblPr>", '<w:tblPr><w:tblW w:w="5000" w:type="pct"/>')
                def cell(m):
                    s = m.group(0)
                    s = s.replace("<w:r><w:t", '<w:r><w:rPr><w:sz w:val="16"/></w:rPr><w:t')
                    return s.replace("<w:rPr><w:b/></w:rPr>", '<w:rPr><w:b/><w:sz w:val="16"/></w:rPr>')
                x = re.sub(r"<w:tc>.*?</w:tc>", cell, x, flags=re.S)
                raw = x.encode("utf-8")
            zout.writestr(item, raw)
    return out.getvalue()


def build_docx():
    sys.path.insert(0, str(GT))
    from exchange.ooxml import DocxBuilder
    b = DocxBuilder()
    b.heading("MÔN HỌC: GDKT&PL, LỚP 12 — MA TRẬN ĐỀ MẪU (M0)")
    b.paragraph("Đề thi tốt nghiệp THPT: 24 câu nhiều lựa chọn (0,25 điểm/câu) và 4 câu đúng/sai (4 ý/câu), tổng 10 điểm, 50 phút. "
                "Mẫu tự soạn để làm ví dụ về mức độ chi tiết; không phải ma trận chính thức của một đề cụ thể.")
    b.heading("Phụ lục I — Ma trận đề")
    b.table(table_I(), header=True)
    b.paragraph("")
    b.heading("Phụ lục II — Bảng đặc tả (yêu cầu cần đạt theo từng câu / ý)")
    b.table(table_II(), header=True)
    return _landscape(b.to_bytes())


def build_md(doc):
    L = ["# GDKT&PL lớp 12 — ma trận đề mẫu (M0)", "",
         "Mẫu tự soạn, trừu tượng; không sao chép từ đề hay ma trận chính thức. Dùng làm ví dụ về mức độ chi tiết cho vòng ma trận.", "",
         "Cấu trúc: Phần I 24 câu nhiều lựa chọn (0,25 điểm/câu); Phần II 4 câu đúng/sai, mỗi câu 4 ý (a Biết, b Hiểu, c–d Vận dụng); tổng 10 điểm; 50 phút.", "",
         "## Tổng hợp", ""]
    t = doc["totals"]
    L += [f"- Câu: Phần I 24, Phần II 4 (16 ý). Đơn vị chấm (câu MCQ + ý): 40, mỗi đơn vị 0,25 điểm.",
          f"- Theo mức độ: Biết {t['by_level_units']['NB']} ({t['by_level_percent']['NB']}%), Hiểu {t['by_level_units']['TH']} ({t['by_level_percent']['TH']}%), Vận dụng {t['by_level_units']['VD']} ({t['by_level_percent']['VD']}%).",
          f"- Phần I: Biết {t['by_part_level_units']['P1']['NB']}, Hiểu {t['by_part_level_units']['P1']['TH']}, Vận dụng {t['by_part_level_units']['P1']['VD']}. Phần II: Biết {t['by_part_level_units']['P2']['NB']}, Hiểu {t['by_part_level_units']['P2']['TH']}, Vận dụng {t['by_part_level_units']['P2']['VD']}.",
          f"- Tổng điểm: {str(t['marks']).replace('.', ',')}.", "",
          "## Dấu hiệu của từng mức độ", ""]
    for lv in LEVELS:
        L.append(f"- **{LV_VI[lv]}**: {LEVEL_CUES[lv]}.")
    L += ["", "## Phụ lục I — Ma trận đề", ""]
    for i, r in enumerate(table_I()):
        L.append("| " + " | ".join(c.replace("|", "/") for c in r) + " |")
        if i == 0: L.append("|" + "---|" * len(r))
    L += ["", "## Phụ lục II — Bảng đặc tả", ""]
    for i, r in enumerate(table_II()):
        L.append("| " + " | ".join(c.replace("|", "/") for c in r) + " |")
        if i == 0: L.append("|" + "---|" * len(r))
    L += ["", "## Tình huống của bốn câu đúng/sai", ""]
    for cau, (bid, stem, sts) in P2_CAU.items():
        L.append(f"- Câu {cau} ({BAI[bid][1]}): {stem}.")
    L += ["", "Năng lực: " + "; ".join(f"{k} = {v}" for k, v in NL.items()) + "."]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    doc = document()
    (HERE / "matrix.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    (HERE / "matrix.docx").write_bytes(build_docx())
    (HERE / "matrix.md").write_text(build_md(doc), encoding="utf-8")
    print("wrote matrix.json / matrix.docx / matrix.md; rows", len(doc["rows"]), "units", sum(doc["totals"]["by_level_units"].values()))

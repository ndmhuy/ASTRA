"""Shared builder for the M0 sample matrices (one spec per subject -> matrix.json, matrix.docx, matrix.md).
A spec is plain data; see toan/build.py.  Run each subject's build.py with the app venv, then check.py."""
import io, json, os, re, sys, zipfile
from pathlib import Path
# Importing app code resolves the owner's Drive workspace unless pointed elsewhere: always use a scratch dir here.
_SCR = Path("/Users/huynguyen/Lecturing_Lab/lab-r1/runs/m0")
(_SCR / "base").mkdir(parents=True, exist_ok=True); (_SCR / "state").mkdir(exist_ok=True)
os.environ.setdefault("LECTURING_BASE_DIR", str(_SCR / "base")); os.environ.setdefault("LECTURING_STATE_DIR", str(_SCR / "state"))
GT = Path("/Users/huynguyen/Lecturing_Lab/lab-r1/work-r0/Grading_Tools")
LEVELS = ["NB", "TH", "VD"]
LV_VI = {"NB": "Biết", "TH": "Hiểu", "VD": "Vận dụng"}
KIND_COL = {"mcq": "Nhiều lựa chọn", "true_false": "Đúng sai", "short_answer": "Trả lời ngắn", "text_answer": "Tự luận"}


def _fmt(x):
    return f"{x:g}".replace(".", ",")


class Spec:
    """spec keys: subject, exam_type, title, intro, minutes, topics{tid:(chu_de, noi_dung)}, parts{pid:{type,unit,width?,label}},
    cells[(part, ref, tid, level, requirement, style, nl)], stems{(part,index):text}, level_cues, competencies"""
    def __init__(self, d):
        self.d = d
        self.topics = d["topics"]
        self.parts = d["parts"]
        self.cells = d["cells"]

    # a cell's address as printed in the tables
    @staticmethod
    def addr(part_type, ref):
        if part_type == "true_false":
            return f"{ref[0]}{ref[1].upper()}"
        return f"C{ref}"

    def cell_list(self):
        out = []
        for c in self.cells:
            part, ref, tid, lv, req, style, nl = c
            out.append(dict(part=part, ref=ref, tid=tid, level=lv, req=req, style=style, nl=nl,
                            ptype=self.parts[part]["type"], unit=self.parts[part]["unit"]))
        return out

    def rows(self):
        cl = self.cell_list(); rows = []
        for part in self.parts:
            ptype = self.parts[part]["type"]
            for tid in self.topics:
                for lv in LEVELS:
                    items = [c for c in cl if c["part"] == part and c["tid"] == tid and c["level"] == lv]
                    if not items:
                        continue
                    items.sort(key=lambda c: (c["ref"] if ptype != "true_false" else (c["ref"][0], c["ref"][1])))
                    chude, ten = self.topics[tid]
                    if ptype == "true_false":
                        refs = [{"index": c["ref"][0], "statement": c["ref"][1]} for c in items]
                        row = {"part_id": part, "topic": ten, "chu_de": chude, "level": lv, "count": None, "count_unit": "statement"}
                        note = "; ".join(f"Ý {c['ref'][0]}{c['ref'][1]}: {c['req']}" for c in items)
                    else:
                        refs = [{"index": c["ref"]} for c in items]
                        row = {"part_id": part, "topic": ten, "chu_de": chude, "level": lv, "count": len(items)}
                        note = "; ".join(f"Câu {c['ref']}: {c['req']}" for c in items)
                    row.update({"references": refs, "marks": round(sum(c["unit"] for c in items), 4), "note": note,
                                "items": [{"ref": self.addr(ptype, c["ref"]), "requirement": c["req"],
                                           "style": c["style"] if ptype != "true_false" else f"ý {c['ref'][1]} của câu {c['ref'][0]}: {self.d['stems'][(part, c['ref'][0])]}",
                                           "competency": c["nl"], "marks": c["unit"]} for c in items]})
                    rows.append(row)
        return rows

    def slots(self):
        """One entry per answer slot, in skeleton order (part, question, slot key): the slot-addressed form. Rows are derived from it."""
        sys.path.insert(0, str(GT))
        from exam_formats.blocks import blocks_for
        out = []
        for part, p in self.parts.items():
            blocks = blocks_for(self.d["exam_type"], self.d["subject"], part)
            spans, at = [], 1
            for bi, b in enumerate(blocks, 1):
                spans.append((bi, b.kind, at, at + b.count - 1)); at += b.count
            cells = [c for c in self.cell_list() if c["part"] == part]
            cells.sort(key=lambda c: (c["ref"] if p["type"] != "true_false" else (c["ref"][0], c["ref"][1])))
            for c in cells:
                q = c["ref"] if p["type"] != "true_false" else c["ref"][0]
                key = c["ref"][1] if p["type"] == "true_false" else None
                blk = next(({"index": bi, "kind": k, "first": a, "last": z} for bi, k, a, z in spans if a <= q <= z), None)
                chude, ten = self.topics[c["tid"]]
                out.append({"part_id": part, "block": blk, "index": q, "key": key, "position": q, "question_type": p["type"],
                            "topic": ten, "chu_de": chude, "level": c["level"], "requirement": c["req"],
                            "style": c["style"] if p["type"] != "true_false" else f"ý {key} của câu {q}: {self.d['stems'][(part, q)]}",
                            "competency": c["nl"], "marks": c["unit"]})
        return out

    def totals(self, rows):
        pc = {}
        for part, p in self.parts.items():
            idx = {c["ref"] if p["type"] != "true_false" else c["ref"][0] for c in self.cell_list() if c["part"] == part}
            pc[part] = len(idx)
        t = {"by_part_cau": pc, "units": {}, "by_level_units": {lv: 0 for lv in LEVELS},
             "by_part_level_units": {p: {lv: 0 for lv in LEVELS} for p in self.parts}, "marks": 0.0, "by_topic_units": {}}
        for r in rows:
            n = len(r["references"])
            t["units"][r["part_id"]] = t["units"].get(r["part_id"], 0) + n
            t["by_level_units"][r["level"]] += n
            t["by_part_level_units"][r["part_id"]][r["level"]] += n
            t["marks"] += r["marks"]
            t["by_topic_units"][r["topic"]] = t["by_topic_units"].get(r["topic"], 0) + n
        t["marks"] = round(t["marks"], 4)
        t["by_level_marks"] = {lv: round(sum(r["marks"] for r in rows if r["level"] == lv), 4) for lv in LEVELS}
        t["by_level_percent"] = {lv: round(100 * t["by_level_marks"][lv] / t["marks"], 1) for lv in LEVELS}
        return t

    def document(self):
        rows = self.rows()
        d = self.d
        return {"version": 1, "levels": LEVELS, "subject": d["subject"], "exam_type": d["exam_type"],
                "source": "mẫu M0 (2026-10-26), tự soạn, trừu tượng; không phải ma trận chính thức của đề nào",
                "built_from": "m0_sample", "level_cues": d["level_cues"], "competencies": d["competencies"],
                "scoring": d["scoring"], "totals": self.totals(rows), "slots": self.slots(), "rows": rows}

    # ---- tables
    def table_I(self):
        cl = self.cell_list()
        kinds = [(p, self.parts[p]["type"]) for p in self.parts]
        head = ["TT", "Chủ đề", "Nội dung/đơn vị kiến thức"]
        for p, k in kinds:
            head += [f"{KIND_COL[k]} - {LV_VI['NB']}", f"{KIND_COL[k]} - {LV_VI['TH']}", f"{KIND_COL[k]} - {LV_VI['VD']}"]
        head += ["Tổng - Biết", "Tổng - Hiểu", "Tổng - Vận dụng", "Tỷ lệ % điểm"]
        out = [head]
        tot_units = {p: {lv: 0 for lv in LEVELS} for p in self.parts}
        marks_total = sum(c["unit"] for c in cl)
        tt = 0
        for tid, (chude, ten) in self.topics.items():
            mine = [c for c in cl if c["tid"] == tid]
            if not mine:
                continue
            tt += 1
            row = [str(tt), chude, ten]
            lvtot = {lv: 0 for lv in LEVELS}
            for p, k in kinds:
                for lv in LEVELS:
                    its = sorted((c for c in mine if c["part"] == p and c["level"] == lv), key=lambda c: (c["ref"] if k != "true_false" else (c["ref"][0], c["ref"][1])))
                    row.append(" ".join(self.addr(k, c["ref"]) for c in its))
                    tot_units[p][lv] += len(its); lvtot[lv] += len(its)
            row += [str(lvtot[lv]) if lvtot[lv] else "" for lv in LEVELS]
            row.append(_fmt(round(100 * sum(c["unit"] for c in mine) / marks_total, 2)))
            out.append(row)
        lines = [["", "Tổng số câu", ""], ["", "Tổng số điểm", ""], ["", "Tỷ lệ %", ""]]
        by_level_units = {lv: sum(tot_units[p][lv] for p in self.parts) for lv in LEVELS}
        by_level_marks = {lv: sum(c["unit"] for c in cl if c["level"] == lv) for lv in LEVELS}
        for p, k in kinds:
            for lv in LEVELS:
                lines[0].append(str(tot_units[p][lv]))
                lines[1].append(_fmt(round(sum(c["unit"] for c in cl if c["part"] == p and c["level"] == lv), 4)))
                lines[2].append("")
        for lv in LEVELS:
            lines[0].append(str(by_level_units[lv])); lines[1].append(_fmt(round(by_level_marks[lv], 4)))
            lines[2].append(_fmt(round(100 * by_level_marks[lv] / marks_total, 1)))
        lines[0].append("100"); lines[1].append(_fmt(round(marks_total, 4))); lines[2].append("100")
        return out + lines

    def table_II(self):
        out = [["TT", "Chủ đề", "Nội dung/đơn vị kiến thức", "Mức độ", "Yêu cầu cần đạt", "Câu", "Dạng", "Năng lực"]]
        n = 0
        cl = self.cell_list()
        for tid, (chude, ten) in self.topics.items():
            for lv in LEVELS:
                for c in sorted((c for c in cl if c["tid"] == tid and c["level"] == lv),
                                key=lambda c: (list(self.parts).index(c["part"]), c["ref"] if c["ptype"] != "true_false" else (c["ref"][0], c["ref"][1]))):
                    n += 1
                    out.append([str(n), chude, ten, LV_VI[lv], c["req"], self.addr(c["ptype"], c["ref"]), KIND_COL[c["ptype"]], c["nl"]])
        return out

    # ---- files
    def docx(self):
        sys.path.insert(0, str(GT))
        from exchange.ooxml import DocxBuilder
        d = self.d
        b = DocxBuilder()
        b.heading(f"MÔN HỌC: {d['title']} — MA TRẬN ĐỀ MẪU (M0)")
        b.paragraph(d["intro"] + " Mẫu tự soạn để làm ví dụ về mức độ chi tiết; không phải ma trận chính thức của một đề cụ thể.")
        b.heading("Phụ lục I — Ma trận đề")
        b.table(self.table_I(), header=True)
        b.paragraph("")
        b.heading("Phụ lục II — Bảng đặc tả (yêu cầu cần đạt theo từng câu / ý)")
        b.table(self.table_II(), header=True)
        return _landscape(b.to_bytes())

    def markdown(self, doc):
        d, t = self.d, doc["totals"]
        L = [f"# {d['title']} — ma trận đề mẫu (M0)", "",
             "Mẫu tự soạn, trừu tượng; không sao chép từ đề hay ma trận chính thức. Dùng làm ví dụ về mức độ chi tiết cho vòng ma trận.", "",
             d["intro"], "", "## Tổng hợp", ""]
        L.append("- Câu theo phần: " + ", ".join(f"{p} {n}" for p, n in t["by_part_cau"].items()) + ". Đơn vị chấm: " + ", ".join(f"{p} {n}" for p, n in t["units"].items()) + ".")
        L.append("- Theo mức độ (đơn vị / điểm / %): " + "; ".join(f"{LV_VI[lv]} {t['by_level_units'][lv]} / {_fmt(t['by_level_marks'][lv])} / {_fmt(t['by_level_percent'][lv])}%" for lv in LEVELS) + ".")
        for p in self.parts:
            L.append(f"- {p}: " + ", ".join(f"{LV_VI[lv]} {t['by_part_level_units'][p][lv]}" for lv in LEVELS) + ".")
        L += [f"- Tổng điểm: {_fmt(t['marks'])}.", "", "## Dấu hiệu của từng mức độ", ""]
        for lv in LEVELS:
            L.append(f"- **{LV_VI[lv]}**: {d['level_cues'][lv]}.")
        for title, tab in (("Phụ lục I — Ma trận đề", self.table_I()), ("Phụ lục II — Bảng đặc tả", self.table_II())):
            L += ["", f"## {title}", ""]
            for i, r in enumerate(tab):
                L.append("| " + " | ".join(c.replace("|", "/") for c in r) + " |")
                if i == 0:
                    L.append("|" + "---|" * len(r))
        if d.get("stems"):
            L += ["", "## Tình huống của các câu đúng/sai", ""]
            for (part, idx), s in d["stems"].items():
                L.append(f"- {part} câu {idx}: {s}.")
        L += ["", "Năng lực: " + "; ".join(f"{k} = {v}" for k, v in d["competencies"].items()) + "."]
        return "\n".join(L) + "\n"

    def write(self, here: Path):
        doc = self.document()
        (here / "matrix.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
        (here / "matrix.docx").write_bytes(self.docx())
        (here / "matrix.md").write_text(self.markdown(doc), encoding="utf-8")
        print("wrote matrix.json / matrix.docx / matrix.md; rows", len(doc["rows"]), "units", sum(doc["totals"]["by_level_units"].values()), "marks", doc["totals"]["marks"])
        return doc


def _landscape(data: bytes) -> bytes:
    """A4 landscape, narrow margins, 8 pt table text, full-width tables. Layout only."""
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
                    s = m.group(0).replace("<w:r><w:t", '<w:r><w:rPr><w:sz w:val="16"/></w:rPr><w:t')
                    return s.replace("<w:rPr><w:b/></w:rPr>", '<w:rPr><w:b/><w:sz w:val="16"/></w:rPr>')
                x = re.sub(r"<w:tc>.*?</w:tc>", cell, x, flags=re.S)
                raw = x.encode("utf-8")
            zout.writestr(item, raw)
    return out.getvalue()

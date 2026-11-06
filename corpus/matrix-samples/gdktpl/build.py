"""M0 sample matrix: GDKT&PL, slot-addressed (via ../m0lib.py). The cell data (bài list, 24 MCQ cells, 4 situations of 4 ý) lives in
_v1.py, unchanged from the first version; this file only maps it onto the shared builder, so the Word file, the json rows and the new
`slots` list come from one source. Run with the app venv."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import _v1 as v
from m0lib import Spec

CELLS = [("P1", i, f"b{b}", lv, req, st, nl) for (i, b, lv, req, st, nl) in v.P1]
STEMS = {}
for cau, (bid, stem, sts) in v.P2_CAU.items():
    STEMS[("P2", cau)] = stem
    for (k, lv, req, nl) in sts:
        CELLS.append(("P2", (cau, k), f"b{bid}", lv, req, "", nl))

SPEC = {
 "subject": "GDKTPL", "exam_type": "THPTQG", "title": "GDKT&PL, LỚP 12",
 "intro": "Đề thi tốt nghiệp THPT: 24 câu nhiều lựa chọn (0,25 điểm/câu) và 4 câu đúng/sai (4 ý/câu, trung bình 0,25 điểm/ý), tổng 10 điểm, 50 phút.",
 "topics": {f"b{b}": v.BAI[b] for b in sorted(v.BAI)},
 "parts": {"P1": {"type": "mcq", "unit": 0.25}, "P2": {"type": "true_false", "unit": 0.25}},
 "cells": CELLS, "stems": STEMS, "level_cues": v.LEVEL_CUES, "competencies": v.NL,
 "scoring": {"P1": "mỗi câu 0,25 điểm", "P2": "mỗi câu 1,0 điểm (4 ý, điểm theo số ý đúng); trung bình 0,25 điểm mỗi ý", "total": 10.0, "duration_minutes": 50},
}

if __name__ == "__main__":
    Spec(SPEC).write(HERE)

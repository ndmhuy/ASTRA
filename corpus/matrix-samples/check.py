"""M0 checks for one subject sample.  usage: check.py <subject_dir> <exam_type> <subject_id>
Runs the app's own code (matrix.py, matrix_import.py) from the lab worktree. No model call, no network."""
import json, os, sys
from pathlib import Path
GT = Path("/Users/huynguyen/Lecturing_Lab/lab-r1/work-r0/Grading_Tools")
d, exam_type, subject = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
scratch = Path("/Users/huynguyen/Lecturing_Lab/lab-r1/runs/m0"); (scratch / "base").mkdir(parents=True, exist_ok=True); (scratch / "state").mkdir(exist_ok=True)
os.environ.update(LECTURING_BASE_DIR=str(scratch / "base"), LECTURING_STATE_DIR=str(scratch / "state"))
sys.path.insert(0, str(GT))
import logging; logging.disable(logging.CRITICAL)
from unittest import mock
from exam_generator import matrix as M, matrix_import as MI
from exam_generator.pipeline import composer_steps, session_config_for_paper

res = []
def check(name, ok, detail=""):
    res.append((name, bool(ok), detail)); print(("PASS " if ok else "FAIL ") + name + (f"  [{detail}]" if detail else ""))

raw = json.loads((d / "matrix.json").read_text(encoding="utf-8"))
doc = M.upgrade_matrix_document(raw)
check("json loads through upgrade_matrix_document, no row dropped", len(doc["rows"]) == len(raw["rows"]), f"{len(doc['rows'])} rows")
check("is_matrix_document", M.is_matrix_document(doc))
check("levels equal DEFAULT_LEVELS", tuple(doc["levels"]) == M.DEFAULT_LEVELS, str(doc["levels"]))
check("every row level is a DEFAULT_LEVELS word", all(r["level"] in M.DEFAULT_LEVELS for r in doc["rows"]))
ints = all((r["count"] is None and r.get("count_unit") == "statement") or (isinstance(r["count"], int) and not isinstance(r["count"], bool)) for r in doc["rows"])
check("every cell count is an integer (or a statement row addressed by references)", ints)
check("every reference index is an integer", all(isinstance(x["index"], int) for r in doc["rows"] for x in r.get("references", [])))

config = session_config_for_paper(exam_type, subject)
steps = composer_steps(exam_type, config)
parts = [{"part_id": s["part_id"], "display_name": s["label"], "display_name_en": s.get("label_en"),
          "question_type": s.get("question_type"), "width": s.get("width")} for s in steps]
expect = {s["part_id"]: int(s["count"]) for s in steps}
totals = M.matrix_part_totals(doc)
check("part totals equal the registered format", totals == expect, f"matrix {totals} / format {expect}")
v = M.matrix_validation(doc, exam_type, config, subject)
check("matrix_validation verdict ok (published layout)", v["verdict"] == "ok" and v["provenance"] == "published", f"{v['verdict']}/{v['provenance']}")
check("matrix_conflicts empty", M.matrix_conflicts(doc, exam_type, config, subject) == [])

# ---- SKELETON: the registered format is the authority; the sample only fills the slots it provides ----
from exam_formats.blocks import blocks_for
def skeleton_slots():
    """(part_id, question index, slot key, question type value) in layout order, read from the registered layout."""
    if exam_type.upper() == "THPTQG":
        from exam_formats.thptqg_2026 import layout_for
        lay = layout_for(subject)
        if lay is None:
            return None
        out = []
        for part in lay.parts:
            for qi, q in enumerate(part.questions(), 1):
                keys = [s.key for s in q.slots]
                for k in keys:
                    out.append((part.part_id, qi, k, getattr(q.qtype, "value", str(q.qtype))))
        return out
    out = []                                    # other formats: every câu of a part is one slot (V-ACT parts)
    for s in steps:
        for qi in range(1, int(s["count"]) + 1):
            out.append((s["part_id"], qi, None, str(s.get("question_type"))))
    return out

want = skeleton_slots()
check("SKELETON: the registered layout has a slot list", want is not None, f"{len(want or [])} slots")
have_slots = raw.get("slots") or []
have = [(s["part_id"], s["index"], s.get("key"), s.get("question_type")) for s in have_slots]
if want is not None:
    check("SKELETON: the sample is slot-addressed (a `slots` list exists)", bool(have_slots), f"{len(have_slots)} slots")
    check("SKELETON: slot count equals the layout's", len(have) == len(want), f"sample {len(have)} / layout {len(want)}")
    missing = [w for w in want if w not in have]; extra = [h for h in have if h not in want]; dup = len(have) - len(set(have))
    check("SKELETON: no missing, no extra, no duplicate slot", not missing and not extra and dup == 0, f"missing {missing[:3]} extra {extra[:3]} dup {dup}")
    check("SKELETON: same slots in the same order as the layout", have == want)
    check("SKELETON: part order equals the layout's", list(dict.fromkeys(h[0] for h in have)) == list(dict.fromkeys(w[0] for w in want)))
    check("SKELETON: every slot names part, position, level, topic and requirement",
          all(s.get("part_id") and s.get("position") and s.get("level") in M.DEFAULT_LEVELS and s.get("topic") and s.get("requirement") for s in have_slots))
# blocks: as registered, per part
for pid in dict.fromkeys(w[0] for w in (want or [])):
    exp = blocks_for(exam_type, subject, pid)
    if not exp:
        check(f"SKELETON: blocks of part {pid}", True, "no block layout is registered for this part, so there is no block order to check (not invented)")
        continue
    spans, at = [], 1
    for bi, b in enumerate(exp, 1):
        spans.append({"index": bi, "kind": b.kind, "first": at, "last": at + b.count - 1}); at += b.count
    got = []
    for s in have_slots:
        if s["part_id"] == pid:
            got.append(s.get("block"))
    exp_per_q = [next(sp for sp in spans if sp["first"] <= s["index"] <= sp["last"]) for s in have_slots if s["part_id"] == pid]
    check(f"SKELETON: blocks of part {pid} (same kinds, sizes, order)", got == exp_per_q, f"{len(exp)} blocks: " + ", ".join(f"{sp['kind']}x{sp['last']-sp['first']+1}" for sp in spans))
# the rows are only a distribution of the slots: rebuild them from the slots and compare
from collections import defaultdict
agg = defaultdict(set)
for s in have_slots:
    agg[(s["part_id"], s["topic"], s["level"])].add((s["index"], s.get("key") or ""))
rows_ref = {(r["part_id"], r["topic"], r["level"]): {(x["index"], x.get("statement", "")) for x in r.get("references", [])} for r in doc["rows"]}
check("SKELETON: rows are exactly the distribution of the slots (nothing added or dropped)", {k: v for k, v in agg.items()} == rows_ref, f"{len(agg)} cells / {len(rows_ref)} rows")

# marks: layout marks per part from the registry
from exam_formats.resolver import parts_for
lay = parts_for(exam_type, subject)
fmt_marks = sum(float(getattr(p, "score_per_correct", 0) or 0) * int(getattr(p, "num_questions", 0) or 0) for p in lay)
check("marks equal the format total", abs(doc["totals"]["marks"] - fmt_marks) < 1e-9 and abs(sum(r["marks"] for r in doc["rows"]) - fmt_marks) < 1e-9, f"matrix {doc['totals']['marks']} / format {fmt_marks}")

# round trip: the Word file parses with no assistant call
with mock.patch.object(MI, "propose_with_assistant", side_effect=AssertionError("assistant called")):
    prop = MI.propose_from_file("matrix.docx", (d / "matrix.docx").read_bytes(), parts)
check("docx parses by the deterministic reader (source=table)", prop["source"] == "table", prop["source"])
check("docx parse leaves nothing unread", prop["unread"] == [], str(prop["unread"][:2]))
key = lambda r: (r["part_id"], r["topic"], r["level"], tuple(sorted((x["index"], x.get("statement", "")) for x in r.get("references", []))))
a, b = sorted(map(key, prop["rows"])), sorted(map(key, doc["rows"]))
check("docx rows equal json rows (part, topic, level, references)", a == b, f"{len(a)} vs {len(b)}")
check("part totals read from the docx equal the format", M.matrix_part_totals({"version": 1, "levels": list(M.DEFAULT_LEVELS), "rows": prop["rows"]}) == expect)
lv_docx = {}
for r in prop["rows"]:
    lv_docx[r["level"]] = lv_docx.get(r["level"], 0) + len(r.get("references", []))
check("level units read from the docx equal the json totals", lv_docx == doc["totals"]["by_level_units"], f"{lv_docx}")
check("every statement-row group is complete (a-d per câu)", not any("incomplete statements" in u for u in prop["unread"]))

bad = [n for n, ok, _ in res if not ok]
print(f"\n{len(res) - len(bad)}/{len(res)} checks passed" + (f"; FAILED: {bad}" if bad else ""))
(d / "checks.txt").write_text("\n".join(("PASS " if ok else "FAIL ") + n + (f"  [{x}]" if x else "") for n, ok, x in res) + f"\n{len(res) - len(bad)}/{len(res)} passed\n", encoding="utf-8")
sys.exit(1 if bad else 0)

# Query the P2 baseline

For Huy and ASTRA teammates: run these commands offline from the repository root. Python 3.14.5 and SQLite with FTS5 were used; no third-party packages are required.

```sh
cd rag
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

The first query below builds the disposable index; `--rebuild` explicitly rebuilds it again. Without that flag, an existing index is reused even if inputs or Git HEAD change. Rebuild after changing the input data. The snapshot ID combines the build-time Git HEAD and a SHA-256 hash over the sorted paths and contents of indexed files.

The examples below were actually run with `python3` on 2026-11-06, from `rag/`. Exact scores and snapshot IDs can change after a rebuild.

### 1. Build the index and search mathematics grade 12.

```sh
python3 -m astra_rag.search -q 'hàm số' --subject Toan --grades 12 --kind curriculum --limit 1 --rebuild
```

```text
1. score=-6.797599 curriculum:toan-12-c1 | curriculum | Toán | grade=12
   Chương I. Ứng dụng đạo hàm để khảo sát và vẽ đồ thị hàm số
   rag/data/toan-12.jsonl#toan-12-c1 | draft
   Chương I. Ứng dụng đạo hàm để khảo sát và vẽ đồ thị hàm số
```

### 2. The unaccented spelling gives the same leading ID.

```sh
python3 -m astra_rag.search -q 'ham so' --subject Toan --grades 12 --kind curriculum --limit 1
```

```text
1. score=-6.797599 curriculum:toan-12-c1 | curriculum | Toán | grade=12
   Chương I. Ứng dụng đạo hàm để khảo sát và vẽ đồ thị hàm số
   rag/data/toan-12.jsonl#toan-12-c1 | draft
   Chương I. Ứng dụng đạo hàm để khảo sát và vẽ đồ thị hàm số
```

### 3. A wrong-grade trap: results remain in grade 10.

```sh
python3 -m astra_rag.search -q 'hàm số' --subject Toan --grades 10 --kind curriculum --limit 1
```

```text
1. score=-7.017247 curriculum:toan-10-c6-b15 | curriculum | Toán | grade=10
   Bài 15. Hàm số
   rag/data/toan-10.jsonl#toan-10-c6-b15 | draft
   Bài 15. Hàm số
```

### 4. Nonsense yields no match, not a fabricated citation.

```sh
python3 -m astra_rag.search -q zzzxqvnonexistent --subject Toan
```

```text
GAP: no_match
```

### 5. Cross-subject trap: no mathematics row is returned.

```sh
python3 -m astra_rag.search -q 'hàm số' --subject 'Sinh học' --grades 12 --kind curriculum --limit 1
```

```text
GAP: no_match
```

### 6. Profile hits display the review warning.

```sh
python3 -m astra_rag.search -q 'đạo hàm' --subject Toan --kind profile --limit 1
```

```text
1. score=-11.333945 profile:toan:3c744b8e2673 | profile | Toán | grade=11
   Quy tắc đạo hàm
   corpus/profiles/toan/topics/3c744b8e2673.json#3c744b8e2673 | agent-reviewed, not teacher-confirmed
   Quy tắc đạo hàm Các quy tắc tính đạo hàm của đa thức Các quy tắc tính đạo hàm: hàm đa thức Các quy tắc tính đạo hàm: tích và hàm mũ hợp Các quy tắc tí
   labels agent-reviewed, not teacher-confirmed
```

### 7. JSON produces machine-readable hits.

```sh
python3 -m astra_rag.search -q 'hàm số' --subject Toan --grades 12 --kind curriculum --limit 1 --json
```

```text
{
  "hits": [
    {
      "chunk_id": "curriculum:toan-12-c1",
      "kind": "curriculum",
      "source_id": "toan-12-c1",
      "subject": "Toán",
      "grade": 12,
      "locator": "rag/data/toan-12.jsonl#toan-12-c1",
      "title": "Chương I. Ứng dụng đạo hàm để khảo sát và vẽ đồ thị hàm số",
      "review_status": "draft",
      "snapshot_id": "3a087c7-abd83d19cca18cbd",
      "score": -6.797599081924882,
      "rank": 1,
      "excerpt": "Chương I. Ứng dụng đạo hàm để khảo sát và vẽ đồ thị hàm số"
    }
  ],
  "gap": null
}
```

### 8. The receipt includes the ranked IDs and snapshot.

```sh
python3 -m astra_rag.search -q 'hàm số' --subject Toan --grades 12 --kind curriculum --limit 1 --show-receipt
```

```text
1. score=-6.797599 curriculum:toan-12-c1 | curriculum | Toán | grade=12
   Chương I. Ứng dụng đạo hàm để khảo sát và vẽ đồ thị hàm số
   rag/data/toan-12.jsonl#toan-12-c1 | draft
   Chương I. Ứng dụng đạo hàm để khảo sát và vẽ đồ thị hàm số
Receipt: {"query": "hàm số", "filters": {"subject": "Toan", "grades": "12", "kind": "curriculum", "limit": 1}, "ranked_chunk_ids": ["curriculum:toan-12-c1"], "snapshot_id": "3a087c7-abd83d19cca18cbd", "retriever_version": "fts5-v1", "timestamp": "2026-11-06T14:58:43.853842+00:00"}
```

### 9. An invalid grade gives bad_grades.

```sh
python3 -m astra_rag.search -q 'hàm số' --subject Toan --grades 13
```

```text
GAP: bad_grades
```

Every search appends a line to `.index/receipts.jsonl`; read the latest with `tail -n 1 .index/receipts.jsonl`. Receipts include the original query, filters, ordered IDs, build snapshot, retriever version and UTC timestamp. They contain your queries, so handle the local file accordingly.

Each hit shows rank, SQLite BM25 score (smaller is better), stable chunk ID, kind, subject, grade, title, locator, review status and a text excerpt of up to 150 characters. A profile with multiple or unknown grades displays `grade=None`; multiple known grades are retained in the filter table, and unknown grades do not pass a grade filter. Locators identify the source file and row/topic ID. `GAP: no_rows` means no records satisfy the filters, `no_match` means no eligible record matched every query token, `empty_query` means no searchable tokens, and `bad_grades` means the grade list is invalid. No filter is widened.

This is lexical matching only: there is no synonym expansion or semantic retrieval. A match does not prove the text answers the question. Curriculum records are draft; profile labels are agent-reviewed and not teacher-confirmed. Profile text uses the topic names, raw topic names and available reasoning-move descriptions from JSON; it is not the complete profile document.

## Continuation: spelling expansion, bundles and offline demo

Run from `rag/`. `--expand` enables the limited spelling table (`om`→`ohm`, `niuton`→`newton`, `jun`/`jul`→`joule`); it never changes filters and is **off by default**. The provisional held-out comparison did not establish a gain; see [results.md](results.md).

```sh
python3 -m astra_rag.search -q om --subject 'Vật lí' --grades 11 --kind curriculum --expand
python3 -m astra_rag.bundle -q 'hàm số' --subject Toan --grades 12 --kind curriculum --budget-bytes 12000
python3 -m astra_rag.demo
python3 -m unittest discover -s tests -p 'test_evidence_bundle.py' -v
```

The bundle caller labels evidence as untrusted data and records a receipt ID. The byte budget limits the compact UTF-8 JSON encoding, **not model tokens**; its `budget_exhausted` gap indicates omitted ranked hits. The receipt lists the complete ranked search result before budget trimming. The standalone local caller does not invoke or integrate with an actual Writer. Do not treat its `evidence_role` field as enforcement against prompt injection; any future consumer must enforce that boundary.

`python3 -m astra_rag.demo` runs an interactive terminal demo. Streamlit, hybrid retrieval, a teacher-reviewed gold set, and screenshots are not provided by this demo.

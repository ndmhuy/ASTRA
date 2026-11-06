"""Local retrieval UI. Start: python -m rag_workflow.app"""

import argparse
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
import time
import sys
from urllib.parse import unquote, urlsplit
import uuid

from .demo import demo_documents, make_document
from .document_loader import load_documents
from .existing_corpus import load_existing_corpus
from .models import CONFIG, Gap
from .results import collection_fingerprint, document_dict
from .workflow import run_documents

WEB = Path(__file__).with_name("web")


def create_server(port=8765, documents=None, corpus_info=None):
    collection = list(demo_documents() if documents is None else documents)
    lock = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        def send(self, status, data, content_type="application/json; charset=utf-8"):
            raw = (
                json.dumps(data, ensure_ascii=False).encode("utf-8")
                if "json" in content_type
                else data
            )
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self):
            route = unquote(urlsplit(self.path).path)
            if route in ("/", "/app.js", "/style.css"):
                name = "index.html" if route == "/" else route[1:]
                mime = {
                    "index.html": "text/html",
                    "app.js": "text/javascript",
                    "style.css": "text/css",
                }[name]
                self.send(200, (WEB / name).read_bytes(), mime + "; charset=utf-8")
            elif route == "/api/collection":
                with lock:
                    snapshot = list(collection)
                self.send(
                    200,
                    {
                        "documents": [
                            dict(
                                document_id=d.document_id,
                                title=d.title,
                                subject=d.subject,
                                grade=d.grade,
                                chapter=d.chapter,
                                evidence_class=d.evidence_class,
                                content_kind=d.content_kind,
                                approval_status=d.approval_status,
                            )
                            for d in snapshot
                        ],
                        "corpus_info": corpus_info,
                        "subjects": CONFIG["subjects"],
                        "editions": sorted({d.edition for d in snapshot}),
                        "max_top_k": CONFIG["max_top_k"],
                    },
                )
            elif route.startswith("/api/documents/"):
                with lock:
                    document = next(
                        (d for d in collection if d.document_id == route.split("/")[-1]), None
                    )
                if document:
                    self.send(200, document_dict(document))
                else:
                    self.send(404, {"error": "Document not found."})
            else:
                self.send(404, {"error": "Not found."})

        def do_POST(self):
            # Only the local page may submit requests; no remote website imports.
            if self.headers.get("Origin") not in (None, f"http://{self.headers.get('Host')}"):
                return self.send(403, {"error": "Cross-origin requests are not allowed."})
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 2_000_000:
                    return self.send(413, {"error": "Request must be at most 2 MB."})
                payload = json.loads(self.rfile.read(length))
                if not isinstance(payload, dict):
                    raise ValueError("Expected a JSON object.")
                if self.path == "/api/search":
                    started = time.perf_counter()
                    with lock:
                        snapshot = list(collection)
                    corpus_hash = (
                        corpus_info["corpus_sha256"]
                        if corpus_info
                        else collection_fingerprint(snapshot)
                    )
                    result = run_documents(payload, snapshot, corpus_hash, corpus_info).to_dict()
                    result["elapsed_ms"] = round((time.perf_counter() - started) * 1000, 1)
                    result["collection_size"] = len(snapshot)
                    return self.send(200, result)
                if self.path == "/api/documents":
                    if corpus_info:
                        raise ValueError("Use --demo or --corpus for session note imports.")
                    if payload.get("permission_confirmed") is not True:
                        raise ValueError("Confirm permission to use this text locally.")
                    document = make_document(
                        payload["subject"],
                        payload["grade"],
                        payload.get("chapter"),
                        payload["title"],
                        payload["content"],
                        "local-" + uuid.uuid4().hex,
                        lesson=payload.get("lesson"),
                        semester=payload.get("semester"),
                        evidence_class="third_party",
                        approved_by="Local user (personal-use selection)",
                        approved_on=date.today().isoformat(),
                        rights_evidence="User confirmed local use; not independently verified",
                        source_locator=payload.get("source_locator") or "User-supplied text",
                    )
                    with lock:
                        collection.append(document)
                    return self.send(201, {"document_id": document.document_id})
                self.send(404, {"error": "Not found."})
            except (ValueError, TypeError, KeyError) as exc:
                self.send(400, {"error": str(exc)})

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    inputs = parser.add_mutually_exclusive_group()
    inputs.add_argument("--corpus", type=Path, help="Approved JSONL pack")
    inputs.add_argument("--demo", action="store_true", help="Use 12 original demo notes")
    parser.add_argument(
        "--corpus-ref",
        default="origin/staging/rag",
        help="Local Git snapshot of the existing corpus",
    )
    args = parser.parse_args()
    info = None
    documents = None
    try:
        if args.corpus:
            documents = load_documents(args.corpus)[0]
        elif not args.demo:
            documents, info = load_existing_corpus(args.corpus_ref)
            print(json.dumps(info, ensure_ascii=True), flush=True)
        server = create_server(args.port, documents, info)
    except (Gap, OSError) as exc:
        print(f"Cannot start ASTRA: {exc}", file=sys.stderr)
        return 2
    print(f"ASTRA retrieval app: http://127.0.0.1:{server.server_port}", flush=True)
    print(
        "Existing corpus is read-only. Ctrl+C to stop."
        if info
        else "Imported text stays in memory until the server stops. Ctrl+C to stop.",
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

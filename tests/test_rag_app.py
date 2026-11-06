import json
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from rag_workflow.app import create_server


class AppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = create_server(0)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def request(self, path, data=None, headers=None):
        raw = json.dumps(data).encode() if data is not None else None
        with urlopen(Request(self.url + path, data=raw, headers=headers or {}), timeout=5) as response:
            body = response.read()
            return json.loads(body) if "json" in response.headers["Content-Type"] else body

    def test_app_serves_ui_and_assets(self):
        self.assertIn(b"Retrieval prototype", self.request("/"))
        self.assertIn(b"/api/search", self.request("/app.js"))
        self.assertIn(b"@media", self.request("/style.css"))

    def test_demo_query_retrieves_full_sources(self):
        response = self.request("/api/search", {"query_text": "Vật lí lớp 11 chương 4 về định luật Ohm"})
        self.assertEqual(response["status"], "success")
        self.assertEqual(len(response["documents"]), 2)
        for hit in response["documents"]:
            self.assertEqual((hit["subject"], hit["grade"], hit["chapter"]), ("vat-li", 11, 4))
            full = self.request("/api/documents/" + hit["document_id"])
            self.assertIn("content", full)
            self.assertEqual(full["content_sha256"], hit["content_sha256"])

    def test_import_becomes_retrievable_and_preserves_text(self):
        payload = dict(subject="toan", grade=10, chapter=7, title="My local geometry note",
                       content="<script>alert('test')</script> Vector geometry note about perpendicular vectors.",
                       permission_confirmed=True, source_locator="Personal notes, section 7")
        receipt = self.request("/api/documents", payload)
        response = self.request("/api/search", {"query_text": "Toán lớp 10 chương 7 về vector"})
        self.assertEqual(response["documents"][0]["document_id"], receipt["document_id"])
        self.assertEqual(self.request("/api/documents/" + receipt["document_id"])["content"], payload["content"])

    def test_import_requires_permission_and_valid_metadata(self):
        for payload in ({"permission_confirmed": False}, {"permission_confirmed": True},
                        dict(permission_confirmed=True, subject="toan", grade=10,
                             title="Invalid note", content=None)):
            with self.assertRaises(HTTPError) as error:
                self.request("/api/documents", payload)
            self.assertEqual(error.exception.code, 400)

    def test_invalid_requests_and_cross_origin_post(self):
        with self.assertRaises(HTTPError) as error:
            self.request("/api/search", {}, {"Origin": "http://other.example"})
        self.assertEqual(error.exception.code, 403)
        response = self.request("/api/search", {"query_text": "Physics"})
        self.assertEqual(response["status"], "gap")
        self.assertEqual(response["documents"], [])

    def test_unknown_source_is_404(self):
        with self.assertRaises(HTTPError) as error:
            self.request("/api/documents/missing")
        self.assertEqual(error.exception.code, 404)


if __name__ == "__main__":
    unittest.main()

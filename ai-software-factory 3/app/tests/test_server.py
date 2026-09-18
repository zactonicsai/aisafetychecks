import json
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from app.server import build_server


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = build_server("127.0.0.1", 0)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def request(self, path, payload=None):
        data = json.dumps(payload).encode() if payload is not None else None
        request = Request(f"http://127.0.0.1:{self.port}{path}", data=data, headers={"Content-Type": "application/json"})
        with urlopen(request, timeout=2) as response:
            return response.status, json.loads(response.read())

    def test_health(self):
        status, body = self.request("/api/health")
        self.assertEqual(200, status)
        self.assertEqual("ok", body["status"])

    def test_catalog_has_language_profiles(self):
        _, body = self.request("/api/catalog")
        self.assertTrue({"python-ai", "java", "cpp", "go", "rust", "web"}.issubset(body["profiles"]))

    def test_pipeline_creates_signed_artifact(self):
        status, body = self.request("/api/pipelines/run", {"project": "unit-test", "profile": "python-ai"})
        self.assertEqual(201, status)
        self.assertEqual("passed", body["status"])
        self.assertTrue(body["signed"])
        self.assertIn("@sha256:", body["artifact"])

    def test_bad_profile_is_rejected(self):
        with self.assertRaises(HTTPError) as caught:
            self.request("/api/pipelines/run", {"project": "unit-test", "profile": "unknown"})
        self.assertEqual(400, caught.exception.code)

    def test_path_traversal_is_rejected(self):
        with self.assertRaises(HTTPError) as caught:
            urlopen(f"http://127.0.0.1:{self.port}/../../README.md", timeout=2)
        self.assertEqual(404, caught.exception.code)


if __name__ == "__main__":
    unittest.main()


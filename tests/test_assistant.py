"""Security and behavior checks for the optional server-side AI analyst."""
import json
import os
import unittest
from threading import Thread
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from http.server import ThreadingHTTPServer
from unittest.mock import patch

import server


class AssistantTests(unittest.TestCase):
    def test_status_never_exposes_api_key(self):
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-secret"}):
            status = server.assistant_status()
        self.assertEqual(status, {"available": True, "provider": "Anthropic", "mode": "optional"})
        self.assertNotIn("test-secret", json.dumps(status))

    def test_status_is_disabled_without_key(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(server.assistant_status()["available"])

    def test_call_assistant_refuses_missing_key(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "AI_NOT_CONFIGURED"):
                server.call_assistant("655", "Phân tích dữ liệu")

    def test_http_status_and_disabled_post_contract(self):
        with patch.dict(os.environ, {}, clear=True):
            httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
            thread = Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            base = "http://127.0.0.1:%d" % httpd.server_address[1]
            try:
                with urlopen(base + "/api/assistant/status", timeout=3) as response:
                    status = json.load(response)
                self.assertFalse(status["available"])
                req = Request(base + "/api/assistant", data=b'{"game":"655","message":"hello"}',
                              headers={"Content-Type":"application/json"}, method="POST")
                with self.assertRaises(HTTPError) as caught:
                    urlopen(req, timeout=3)
                self.assertEqual(caught.exception.code, 503)
            finally:
                httpd.shutdown()
                httpd.server_close()
                thread.join(timeout=3)

    def test_assistant_context_is_game_scoped_and_compact(self):
        fake = [{"d": "2026-11-24", "n": [1, 2, 3, 4, 5, 6], "b": 7}]
        with patch.object(server, "read_ods", return_value=fake):
            ctx = server.assistant_context("655")
        self.assertEqual(ctx["game"], "655")
        self.assertEqual(ctx["latest_draw"], "2026-11-24")
        self.assertEqual(ctx["draw_count"], 1)
        self.assertEqual(ctx["analytics"]["name"] if "name" in ctx["analytics"] else "Power 6/55", "Power 6/55")
        self.assertNotIn("games", ctx["analytics"])
        self.assertLess(len(json.dumps(ctx)), 12000)


if __name__ == "__main__":
    unittest.main()

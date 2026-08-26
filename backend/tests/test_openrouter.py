import json
import unittest
from unittest.mock import patch

from studylens import openrouter


class FakeResponse:
    def __init__(self, payload=None, lines=(), status_code=200):
        self._payload = payload or {}
        self._lines = lines
        self.status_code = status_code
        self.reason_phrase = "OK"

    @property
    def is_error(self):
        return self.status_code >= 400

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.is_error:
            raise RuntimeError(self.reason_phrase)

    async def aiter_lines(self):
        for line in self._lines:
            yield line

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None


class FakeClient:
    response = FakeResponse()
    last_post = None
    last_stream = None

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None

    async def post(self, url, **kwargs):
        FakeClient.last_post = (url, kwargs)
        return FakeClient.response

    def stream(self, method, url, **kwargs):
        FakeClient.last_stream = (method, url, kwargs)
        return FakeClient.response


class OpenRouterContractTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.patcher = patch.object(openrouter.httpx, "AsyncClient", FakeClient)
        self.patcher.start()
        openrouter.OPENROUTER_API_KEY = "test-key"
        openrouter.OPENROUTER_MODEL = "test/chat-model"
        openrouter.OPENROUTER_EMBED_MODEL = "test/embed-model"

    def tearDown(self):
        self.patcher.stop()

    async def test_embeddings_are_returned_in_input_order(self):
        FakeClient.response = FakeResponse(
            {"data": [{"index": 1, "embedding": [2.0]}, {"index": 0, "embedding": [1.0]}]}
        )
        result = await openrouter.embed(["first", "second"])
        self.assertEqual(result, [[1.0], [2.0]])
        url, kwargs = FakeClient.last_post
        self.assertTrue(url.endswith("/embeddings"))
        self.assertEqual(kwargs["json"]["model"], "test/embed-model")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer test-key")

    async def test_json_generation_requests_json_object_mode(self):
        FakeClient.response = FakeResponse(
            {"choices": [{"message": {"content": '{"ok": true}'}}]}
        )
        result = await openrouter.json_generate("make json", "system")
        self.assertEqual(json.loads(result), {"ok": True})
        self.assertEqual(
            FakeClient.last_post[1]["json"]["response_format"], {"type": "json_object"}
        )

    async def test_stream_ignores_keepalive_and_done_frames(self):
        FakeClient.response = FakeResponse(
            lines=(
                ": OPENROUTER PROCESSING",
                'data: {"choices":[{"delta":{"content":"Hello"}}]}',
                'data: {"choices":[{"delta":{"content":" world"}}]}',
                'data: [DONE]',
            )
        )
        result = [token async for token in openrouter.stream("question")]
        self.assertEqual(result, ["Hello", " world"])
        self.assertTrue(FakeClient.last_stream[2]["json"]["stream"])


if __name__ == "__main__":
    unittest.main()

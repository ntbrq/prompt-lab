import pytest
import respx
import httpx
from app.services.openai_compatible import OpenAICompatibleProvider


class TestOpenAICompatibleProvider:
    @respx.mock
    def test_chat(self):
        respx.post("https://api.example.com/v1/chat/completions").mock(
            return_value=httpx.Response(200, json={
                "choices": [{"message": {"content": "Hello!"}}]
            })
        )

        provider = OpenAICompatibleProvider("test-key", "https://api.example.com/v1", "model-1")
        result = provider.chat([{"role": "user", "content": "Hi"}])
        assert result == "Hello!"

    @respx.mock
    def test_chat_stream(self):
        chunks = [
            b'data: {"choices":[{"delta":{"content":"Hello"}}]}\n\n',
            b'data: {"choices":[{"delta":{"content":" World"}}]}\n\n',
            b'data: [DONE]\n\n',
        ]

        respx.post("https://api.example.com/v1/chat/completions").mock(
            return_value=httpx.Response(200, stream=iter(chunks), headers={"content-type": "text/event-stream"})
        )

        provider = OpenAICompatibleProvider("test-key", "https://api.example.com/v1", "model-1")
        result = list(provider.chat_stream([{"role": "user", "content": "Hi"}]))
        assert "".join(result) == "Hello World"

    @respx.mock
    def test_chat_error(self):
        respx.post("https://api.example.com/v1/chat/completions").mock(
            return_value=httpx.Response(401, json={"error": "Unauthorized"})
        )

        provider = OpenAICompatibleProvider("bad-key", "https://api.example.com/v1", "model-1")
        with pytest.raises(httpx.HTTPStatusError):
            provider.chat([{"role": "user", "content": "Hi"}])


class TestPromptOptimizer:
    @respx.mock
    def test_optimize(self):
        respx.post("https://api.example.com/v1/chat/completions").mock(
            return_value=httpx.Response(200, json={
                "choices": [{"message": {"content": "Optimized prompt here.\n\n## Changes\n- Made it better"}}]
            })
        )

        from app.services.optimizer import PromptOptimizer
        provider = OpenAICompatibleProvider("test-key", "https://api.example.com/v1", "model-1")
        optimizer = PromptOptimizer(provider)
        result = optimizer.optimize("Original prompt", "improve")
        assert "Optimized" in result

    @respx.mock
    def test_optimize_types(self):
        respx.post("https://api.example.com/v1/chat/completions").mock(
            return_value=httpx.Response(200, json={
                "choices": [{"message": {"content": "Result"}}]
            })
        )

        from app.services.optimizer import PromptOptimizer
        provider = OpenAICompatibleProvider("test-key", "https://api.example.com/v1", "model-1")
        optimizer = PromptOptimizer(provider)

        for opt_type in ("improve", "simplify", "rephrase", "expand"):
            result = optimizer.optimize("Test", opt_type)
            assert result == "Result"

    @respx.mock
    def test_translate(self):
        respx.post("https://api.example.com/v1/chat/completions").mock(
            return_value=httpx.Response(200, json={
                "choices": [{"message": {"content": "翻译结果"}}]
            })
        )

        from app.services.optimizer import PromptOptimizer
        provider = OpenAICompatibleProvider("test-key", "https://api.example.com/v1", "model-1")
        optimizer = PromptOptimizer(provider)
        result = optimizer.optimize("Translate this", "translate", target_language="Chinese")
        assert "翻译" in result

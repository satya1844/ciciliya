import asyncio
import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock

import src.llm.groq_client as groq_client


def test_get_groq_response_returns_content(monkeypatch):
    mock_create = AsyncMock(
        return_value=SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="This is a test answer."))]
        )
    )
    mock_client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=mock_create))
    )

    monkeypatch.setattr(groq_client, "client", mock_client)
    monkeypatch.setattr(groq_client, "MODELS", ["test-model"])

    answer = asyncio.run(groq_client.get_groq_response("What is testing?", context="Test context"))

    assert answer == "This is a test answer."
    mock_create.assert_awaited_once()


def test_get_groq_response_raises_when_all_models_fail(monkeypatch):
    mock_create = AsyncMock(side_effect=RuntimeError("model unavailable"))
    mock_client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=mock_create))
    )

    monkeypatch.setattr(groq_client, "client", mock_client)
    monkeypatch.setattr(groq_client, "MODELS", ["unavailable-model"])

    with pytest.raises(Exception):
        asyncio.run(groq_client.get_groq_response("question", context="ctx"))


def test_get_groq_response_stream_yields_tokens(monkeypatch):
    async def fake_stream():
        yield SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="Hel"))])
        yield SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="lo"))])

    mock_create = AsyncMock(return_value=fake_stream())
    mock_client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=mock_create))
    )

    monkeypatch.setattr(groq_client, "client", mock_client)
    monkeypatch.setattr(groq_client, "MODELS", ["stream-model"])

    async def collect_tokens():
        gathered = []
        async for token in groq_client.get_groq_response_stream("hi", context="ctx"):
            gathered.append(token)
        return gathered

    tokens = asyncio.run(collect_tokens())

    assert tokens == ["Hel", "lo"]
    mock_create.assert_awaited_once()

import pytest
from unittest.mock import Mock

from src.search.serper_search import search_serper


def _make_response(payload):
    response = Mock()
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    return response


def test_search_serper_returns_formatted_results(monkeypatch):
    payload = {
        "organic": [
            {"title": "Test Title 1", "link": "http://example.com/1", "snippet": "Snippet 1"},
            {"title": "Test Title 2", "link": "http://example.com/2", "snippet": "Snippet 2"},
        ]
    }

    monkeypatch.setenv("SERPER_API_KEY", "test-key")
    monkeypatch.setattr(
        "src.search.serper_search.requests.post",
        lambda *args, **kwargs: _make_response(payload),
    )

    results = search_serper("test query", max_results=2)

    assert results == [
        {"title": "Test Title 1", "url": "http://example.com/1", "snippet": "Snippet 1"},
        {"title": "Test Title 2", "url": "http://example.com/2", "snippet": "Snippet 2"},
    ]


def test_search_serper_returns_none_without_api_key(monkeypatch):
    monkeypatch.delenv("SERPER_API_KEY", raising=False)

    assert search_serper("query") is None


def test_search_serper_handles_request_errors(monkeypatch):
    monkeypatch.setenv("SERPER_API_KEY", "test-key")

    def _raise(*_, **__):
        raise RuntimeError("boom")

    monkeypatch.setattr("src.search.serper_search.requests.post", _raise)

    assert search_serper("query") is None

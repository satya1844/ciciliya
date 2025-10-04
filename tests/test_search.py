import pytest
from unittest.mock import patch, MagicMock
from src.scraper.scraper import scrape_url
from src.search.ddg_search import search_web

@pytest.fixture
def mock_ddgs_text():
    """Fixture to mock the DDGS().text method."""
    mock_results = [
        {'title': 'Test Title 1', 'href': 'http://example.com/1', 'body': 'Snippet 1'},
        {'title': 'Test Title 2', 'href': 'http://example.com/2', 'body': 'Snippet 2'},
    ]
    with patch('src.search.ddg_search.DDGS.text', return_value=mock_results) as mock_method:
        yield mock_method

@pytest.fixture
def mock_fetch_html():
    """Fixture to mock the fetch_html function."""
    with patch('src.scraper.scraper.fetch_html') as mock_fetch:
        yield mock_fetch

@pytest.fixture
def mock_extract_readable():
    """Fixture to mock the extract_readable function."""
    with patch('src.scraper.scraper.extract_readable') as mock_extract:
        yield mock_extract

@pytest.fixture
def mock_render_with_playwright():
    """Fixture to mock the _render_with_playwright function."""
    with patch('src.scraper.scraper._render_with_playwright') as mock_render:
        yield mock_render

def test_search_web_returns_formatted_results(mock_ddgs_text):
    """
    Tests that search_web correctly calls the DDGS API and formats the results.
    """
    query = "test query"
    max_results = 2
    
    results = search_web(query, max_results=max_results)
    
    # Assert that the mock was called correctly
    mock_ddgs_text.assert_called_once_with(query, max_results=max_results)
    
    # Assert that the results are formatted as expected
    assert len(results) == 2
    assert results[0] == {'title': 'Test Title 1', 'url': 'http://example.com/1', 'snippet': 'Snippet 1'}
    assert results[1] == {'title': 'Test Title 2', 'url': 'http://example.com/2', 'snippet': 'Snippet 2'}

def test_search_web_handles_empty_results(mock_ddgs_text):
    """
    Tests that search_web returns an empty list when the API provides no results.
    """
    mock_ddgs_text.return_value = []
    
    results = search_web("empty query")
    
    assert results == []

def test_search_web_handles_missing_keys(mock_ddgs_text):
    """
    Tests that search_web handles API responses with missing keys gracefully.
    """
    mock_ddgs_text.return_value = [
        {'href': 'http://example.com/1'}, # Missing title and body
        {'title': 'Test Title 2', 'body': 'Snippet 2'}, # Missing href
    ]
    
    results = search_web("missing keys query")
    
    assert len(results) == 2
    assert results[0] == {'title': '', 'url': 'http://example.com/1', 'snippet': ''}
    assert results[1] == {'title': 'Test Title 2', 'url': '', 'snippet': 'Snippet 2'}

def test_scrape_url_static_path_success(mock_fetch_html, mock_extract_readable, mock_render_with_playwright):
    """
    Tests the fast path where static HTML is sufficient and Playwright is NOT called.
    """
    test_url = "http://example.com"
    mock_html = "<html><body><p>This is a long test content...</p></body></html>"
    # Make the text long enough to pass the min_chars check
    long_text = "This is a test. " * 100
    mock_article = {"title": "Test Title", "text": long_text}

    mock_fetch_html.return_value = mock_html
    mock_extract_readable.return_value = mock_article

    result = scrape_url(test_url)

    mock_fetch_html.assert_called_once_with(test_url)
    mock_extract_readable.assert_called_once_with(mock_html)
    mock_render_with_playwright.assert_not_called() # Ensure fallback is not used
    assert result == mock_article

def test_scrape_url_uses_playwright_fallback(mock_fetch_html, mock_extract_readable, mock_render_with_playwright):
    """
    Tests the slow path where static HTML is too short, triggering the Playwright fallback.
    """
    test_url = "http://example.com/js-heavy"
    short_static_html = "<html><body>short</body></html>"
    rendered_html = "<html><body>This is the full content rendered by JS.</body></html>"
    
    # First call to extract_readable (from static fetch) returns a short article
    short_article = {"title": "Short Title", "text": "short"}
    # Second call (from Playwright) returns the full article
    full_article = {"title": "Full Title", "text": "This is the full content rendered by JS."}

    mock_fetch_html.return_value = short_static_html
    mock_extract_readable.side_effect = [short_article, full_article]
    mock_render_with_playwright.return_value = rendered_html

    result = scrape_url(test_url)

    assert mock_extract_readable.call_count == 2
    mock_render_with_playwright.assert_called_once_with(test_url)
    assert result == full_article

def test_scrape_url_fetch_fails_gracefully(mock_fetch_html, mock_render_with_playwright):
    """
    Tests that if fetch_html fails, it attempts the Playwright fallback.
    """
    test_url = "http://example.com/404"
    mock_fetch_html.side_effect = ConnectionError("Failed to connect")
    mock_render_with_playwright.return_value = "<html><body>Fallback content</body></html>"

    # This test doesn't care about the final extracted content, just the flow
    with patch('src.scraper.scraper.extract_readable') as mock_extract:
        mock_extract.return_value = {"title": "Fallback", "text": "Fallback content"}
        scrape_url(test_url)
        mock_render_with_playwright.assert_called_once_with(test_url)

def test_scrape_url_all_failures_returns_empty(mock_fetch_html, mock_render_with_playwright):
    """
    Tests that if both static fetch and Playwright fail, it returns an empty article.
    """
    test_url = "http://example.com/broken"
    mock_fetch_html.side_effect = Exception("Static fetch failed")
    mock_render_with_playwright.side_effect = Exception("Playwright failed")

    result = scrape_url(test_url)

    assert result == {"title": "", "text": "", "html": ""}

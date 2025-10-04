import pytest
from unittest.mock import patch, MagicMock
from src.scraper.scraper import scrape_url

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

def test_scrape_url_static_path_success(mock_fetch_html, mock_extract_readable, mock_render_with_playwright):
    """
    Tests the fast path where static HTML is sufficient and Playwright is NOT called.
    """
    test_url = "http://example.com"
    # Make the text long enough to pass the min_chars check in scrape_url
    long_text = "This is a test sentence. " * 100
    mock_html = f"<html><body><p>{long_text}</p></body></html>"
    mock_article = {"title": "Test Title", "text": long_text, "html": mock_html}

    mock_fetch_html.return_value = mock_html
    mock_extract_readable.return_value = mock_article

    result = scrape_url(test_url)

    # Assertions for the happy path
    mock_fetch_html.assert_called_once_with(test_url)
    mock_extract_readable.assert_called_once_with(mock_html)
    mock_render_with_playwright.assert_not_called() # Crucially, fallback is not used
    assert result == mock_article

def test_scrape_url_uses_playwright_fallback_on_short_content(mock_fetch_html, mock_extract_readable, mock_render_with_playwright):
    """
    Tests the slow path where static HTML is too short, triggering the Playwright fallback.
    """
    test_url = "http://example.com/js-heavy"
    short_static_html = "<html><body>short</body></html>"
    rendered_html = "<html><body>This is the full content rendered by JS.</body></html>"
    
    # Mock the two calls to extract_readable
    short_article = {"title": "Short Title", "text": "short", "html": short_static_html}
    full_article = {"title": "Full Title", "text": "This is the full content rendered by JS.", "html": rendered_html}
    mock_extract_readable.side_effect = [short_article, full_article]
    
    mock_fetch_html.return_value = short_static_html
    mock_render_with_playwright.return_value = rendered_html

    result = scrape_url(test_url)

    # Assertions for the fallback path
    assert mock_fetch_html.call_count == 1
    mock_render_with_playwright.assert_called_once_with(test_url)
    assert mock_extract_readable.call_count == 2
    assert result == full_article

def test_scrape_url_fetch_fails_gracefully_and_uses_fallback(mock_fetch_html, mock_extract_readable, mock_render_with_playwright):
    """
    Tests that if fetch_html fails, it attempts the Playwright fallback and doesn't crash.
    """
    test_url = "http://example.com/404"
    mock_fetch_html.side_effect = ConnectionError("Failed to connect")
    
    rendered_html = "<html><body>Fallback content</body></html>"
    fallback_article = {"title": "Fallback", "text": "Fallback content", "html": rendered_html}
    mock_render_with_playwright.return_value = rendered_html
    mock_extract_readable.return_value = fallback_article

    result = scrape_url(test_url)

    # Assertions for fetch failure
    mock_render_with_playwright.assert_called_once_with(test_url)
    assert result == fallback_article

def test_scrape_url_all_failures_returns_empty_article(mock_fetch_html, mock_render_with_playwright):
    """
    Tests that if both static fetch and Playwright fail, it returns a default empty article.
    """
    test_url = "http://example.com/broken"
    mock_fetch_html.side_effect = Exception("Static fetch failed")
    mock_render_with_playwright.side_effect = Exception("Playwright failed")

    result = scrape_url(test_url)

    # The function should not raise an exception, but return a predictable empty state
    assert result == {"title": "", "text": "", "html": ""}

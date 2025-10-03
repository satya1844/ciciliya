# src/scraper/scraper.py
from multiprocessing import context
from .web_scraper import fetch_html
from .content_extractor import extract_readable


def _render_with_playwright(url: str, timeout_ms: int = 20000) -> str:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = browser.new_page()
        page.goto(url, timeout=timeout_ms)
        content = page.content()
        browser.close()
        return content
    


def scrape_url(url: str, min_chars: int = 8000) -> dict:
    """Fetch and extract readable content from a URL"""
    html = fetch_html(url)
    article = extract_readable(html)

    text = article.get("text") or ""
    if len(text) >= min_chars:
        return article
    
    try:
        rendered_html = _render_with_playwright(url)
        return extract_readable(rendered_html)
    except Exception as e:
        pass
    
    return article

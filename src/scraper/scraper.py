# src/scraper/scraper.py
from multiprocessing import context
from .web_scraper import fetch_html
from .content_extractor import extract_readable

def _render_with_playwright(url: str, timeout_ms: int = 20000) -> str:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/127.0.0.0 Safari/537.36"
            ),
            locale="en-US",
        )
        page = context.new_page()
        page.set_default_timeout(timeout_ms)
        # Speed up by blocking heavy assets
        page.route("**/*", lambda route: route.abort() if route.request.resource_type in {"image", "media", "font"} else route.continue_())
        page.goto(url, wait_until="networkidle")
        page.wait_for_load_state("domcontentloaded")
        html = page.content()
        browser.close()
        return html

def scrape_url(url: str, min_chars: int = 1000) -> dict:
    """Fetch and extract readable content from a URL with JS fallback."""
    # 1) Fast path: static fetch
    try:
        html = fetch_html(url)
        article = extract_readable(html)
        if len(article.get("text") or "") >= min_chars:
            return article
    except Exception:
        article = {"title": "", "text": "", "html": ""}

    # 2) Slow path: JS-rendered fallback
    try:
        rendered = _render_with_playwright(url)
        return extract_readable(rendered)
    except Exception:
        # Return whatever we got from static path (possibly empty)
        return article

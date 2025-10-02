# src/scraper/scraper.py
from .web_scraper import fetch_html
from .content_extractor import extract_readable

def scrape_url(url: str):
    """Fetch and extract readable content from a URL"""
    html = fetch_html(url)
    return extract_readable(html)

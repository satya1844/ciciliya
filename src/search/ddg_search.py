
# Explain about this file in detail

# This file contains a function for searching the web using the DuckDuckGo Search API. It defines a function `search_web` that takes a search query and an optional maximum number of results to return. The function uses the `DDGS` class from the DuckDuckGo Search library to perform the search and return the results in a structured format.

from typing import List, Dict, Any 

try:
    # Preferred new package
    from ddgs import DDGS
except ImportError:
    # Fallback to old package if not upgraded yet
    from duckduckgo_search import DDGS  # type: ignore


def search_web(query:str, max_results:int = 5) -> List[Dict[str,Any]]:
    with DDGS() as ddgs:
        raw = list(ddgs.text(query, max_results=max_results))
    results = []
    for r in raw:
        url = r.get("href") or r.get("link")
        results.append({
            "title": r.get("title") or "",
            "url": url or "",
            "snippet": r.get("body") or r.get("snippet") or "",
        })
    return results

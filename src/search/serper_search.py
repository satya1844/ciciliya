import os
import requests
from typing import List, Dict, Optional

def search_serper(query: str, max_results: int = 5) -> Optional[List[Dict]]:
    """
    Performs a web search using the Serper.dev API (Google Search results).
    Free tier: 2,500 searches per month without requiring a credit card.
    """
    api_key = os.environ.get("SERPER_API_KEY")
    if not api_key:
        print("Error: SERPER_API_KEY is not set. Get your free key from https://serper.dev/")
        return None

    url = "https://google.serper.dev/search"
    
    payload = {
        "q": query,
        "num": max_results
    }
    
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Extract relevant information from the response
        results = []
        if "organic" in data:
            for item in data["organic"]:
                results.append({
                    "title": item.get("title", "No Title"),
                    "url": item.get("link", ""),
                    "description": item.get("snippet", ""),
                })
        
        return results

    except requests.exceptions.RequestException as e:
        print(f"Error calling Serper API: {e}")
        return None
    except Exception as e:
        print(f"Error processing Serper response: {e}")
        return None
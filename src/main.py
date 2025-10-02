import argparse

from src.scraper.scraper import scrape_url
from .search.ddg_search import search_web

def print_results(results):
    if not results:
        print("No results found.")
        return
    for idx, r in enumerate(results, start=1):
        print(f"Result {idx}:")
        print(f"Title: {r['title']}")
        print(f"URL: {r['url']}")
        print(f"Snippet: {r['snippet']}\n")
        print()

def interactive():
    print("Real-Time Browsing Chatbot - Stage 2 (Search + Scrape)")
    print("Type 'exit' to quit.")
    while True:
        q = input("Enter your search query: ").strip()
        if not q:
            continue
        if q.lower() == 'exit':
            print("Exiting...")
            break
        results = search_web(q, max_results=5)
        print_results(results)

        if not results:
            continue
        choice = input("Enter the result number to scrape (or 'n' to skip): ").strip()
        if choice.lower() == 'n':
            continue
        
        if not choice.isdigit():
            print("Please enter a valid number.")
            continue
        
        
        idx = int(choice) - 1
        if 0 <= idx < len(results):
            url = results[idx]["url"]
            try:
                article = scrape_url(url)
                print("\n--- Scraped Article ---")
                print(f"Title: {article.get('title','')}")
                print(f"URL: {url}\n")
                print(article.get('text','')[:2000])
                print("\n-----------------------\n")
            except Exception as e:
                print(f"Scrape failed: {e}")
        else:
            print("Out of range.")
            continue
def main():
    parser = argparse.ArgumentParser(description="Real-Time Browsing Chatbot")
    parser.add_argument('--query', '-q', type=str, help='Search query')
    parser.add_argument('--url', type=str, help='URL of the page to fetch')

    parser.add_argument('--max_results', '-m', type=int, default=5, help='Maximum number of search results to retrieve')
    args = parser.parse_args()

    if args.url:
        try:
            article = scrape_url(args.url)
            print(f"Title: {article.get('title','')}")
            print(f"URL: {args.url}\n")
            print(article.get('text',''))
        except Exception as e:
            print(f"Scrape failed: {e}")
        return



    if args.query:
        results = search_web(args.query, max_results=args.max_results)
        print_results(results)
    else:
        interactive()

if __name__ == "__main__":
    main()

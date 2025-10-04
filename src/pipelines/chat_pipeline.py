import argparse
import time
from typing import List, Dict
# import numpy as np
from ..search.ddg_search import search_web
from ..scraper.scraper import scrape_url
from ..utils.chunking import chunk_text
from ..llm.gemini_client import GeminiClient
from ..llm.groq_client import GroqClient

from ..vector_store.chroma_db import ChromaDBManager
from langchain.docstore.document import Document as LangchainDocument
 

#This function is no longer needed with ChromaDB
# def _cosine_sim_matrix(a: np.ndarray, b: np.ndarray) -> np.ndarray:
#     a = a.astype(float); b = b.astype(float)
#     a_norm = a / (np.linalg.norm(a, axis=1, keepdims=True) + 1e-12)
#     b_norm = b / (np.linalg.norm(b, axis=1, keepdims=True) + 1e-12)
#     return a_norm @ b_norm.T

def run_rag(query: str, max_results: int = 5, top_docs: int = 3, top_chunks: int = 8, provider: str = "gemini"):
    start_time = time.time()
    last_step_time = start_time

    # 1. Search
    print(f"[{time.time() - start_time:.2f}s] 1. Searching for '{query}'...")
    results = search_web(query, max_results=max_results)
    if not results:
        print("No results found.")
        return
    print(f"   -> Search complete in {time.time() - last_step_time:.2f}s. Found {len(results)} results.")
    last_step_time = time.time()

    # 2. Scrape
    print(f"[{time.time() - start_time:.2f}s] 2. Scraping top {top_docs} documents...")
    docs: List[Dict] = []
    for r in results[:top_docs]:
        url = r["url"]
        try:
            article = scrape_url(url)
            text = (article.get("text") or "").strip()
            if text:
                docs.append({"url": url, "title": article.get("title", "") or r.get("title",""), "text": text})
                print(f"   - Scraped: {url}")
        except Exception as e:
            print(f"   - Failed to scrape {url}: {e}")

    if not docs:
        print("Failed to scrape any documents.")
        return
    print(f"   -> Scraping complete in {time.time() - last_step_time:.2f}s. Got {len(docs)} documents.")
    last_step_time = time.time()

    # 3. Chunk
    print(f"[{time.time() - start_time:.2f}s] 3. Chunking documents...")
    all_docs:List[LangchainDocument] = []
  
    for d in docs:
        for ch in chunk_text(d["text"],max_words=220, overlap=40):
            all_docs.append(LangchainDocument(page_content=ch, metadata={"url": d["url"], "title": d["title"]}))
    if not all_docs:
        print("No chunks produced.")
        return
    print(f"   -> Chunking complete in {time.time() - last_step_time:.2f}s. Produced {len(all_docs)} chunks.")

    # 4. Embed & retrieve with ChromaDB
    print(f"[{time.time() - start_time:.2f}s] 4. Embedding & retrieving with ChromaDB...")
    db_manager = ChromaDBManager()

    db_manager.add_documents(all_docs)

    query_results: List[str] = db_manager.query(query, n_results=top_chunks)

    top_contexts = query_results

    # Extract unique sources from the metadata of retrieved documents
    # top_sources = [doc.metadata['url'] for doc in query_results if 'url' in doc.metadata]
    # Since we can't get metadata from the query results, we'll rely on the initial docs for sources.
    top_sources = [d["url"] for d in docs]


    print(f"   -> Embedding & Retrieval complete in {time.time() - last_step_time:.2f}s.")
    last_step_time = time.time()

    print(f"[{time.time() - start_time:.2f}s] 5. Generating answer with {provider.upper()}...")
    if provider.lower() == "groq":
        llm = GroqClient()
        answer = llm.answer(query, top_contexts)
    else:
        client = GeminiClient()
        answer = client.answer(query, top_contexts)
    print(f"   -> Generation complete in {time.time() - last_step_time:.2f}s.")

    print("\n=== Answer ===\n")
    print((answer or "").strip())
    print("\n=== Sources ===")
    for i, url in enumerate(dict.fromkeys(top_sources), start=1):
        print(f"[{i}] {url}")

    print(f"\n--- Total execution time: {time.time() - start_time:.2f}s ---")


def main():
    # ... existing code ...
    p = argparse.ArgumentParser(description="RAG: search → scrape → retrieve → answer (Gemini/Groq)")
    p.add_argument("-q", "--query", required=True, help="User question")
    p.add_argument("-m", "--max_results", type=int, default=5, help="Search results to fetch")
    p.add_argument("--top_docs", type=int, default=3, help="Top documents to scrape")
    p.add_argument("--top_chunks", type=int, default=8, help="Top chunks for context")
    p.add_argument("--provider", choices=["gemini", "groq"], default="gemini", help="LLM provider for answer generation")
    args = p.parse_args()
    run_rag(args.query, max_results=args.max_results, top_docs=args.top_docs, top_chunks=args.top_chunks, provider=args.provider)

if __name__ == "__main__":
    main()
    

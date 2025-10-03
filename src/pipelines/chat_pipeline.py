import argparse
from typing import List, Dict
import numpy as np
from ..search.ddg_search import search_web
from ..scraper.scraper import scrape_url
from ..utils.chunking import chunk_text
from ..llm.gemini_client import GeminiClient
from ..llm.groq_client import GroqClient


def _cosine_sim_matrix(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a = a.astype(float); b = b.astype(float)
    a_norm = a / (np.linalg.norm(a, axis=1, keepdims=True) + 1e-12)
    b_norm = b / (np.linalg.norm(b, axis=1, keepdims=True) + 1e-12)
    return a_norm @ b_norm.T

def run_rag(query: str, max_results: int = 5, top_docs: int = 3, top_chunks: int = 8, provider: str = "gemini"):
    results = search_web(query, max_results=max_results)
    if not results:
        print("No results found.")
        return

    docs: List[Dict] = []
    for r in results[:top_docs]:
        url = r["url"]
        try:
            article = scrape_url(url)
            text = (article.get("text") or "").strip()
            if text:
                docs.append({"url": url, "title": article.get("title", "") or r.get("title",""), "text": text})
        except Exception as e:
            print(f"Failed to scrape {url}: {e}")

    if not docs:
        print("Failed to scrape any documents.")
        return

    # build chunks after scraping loop
    chunks, meta = [], []
    for d in docs:
        for ch in chunk_text(d["text"], max_words=220, overlap=40):
            chunks.append(ch)
            meta.append({"url": d["url"], "title": d["title"]})

    if not chunks:
        print("No chunks produced.")
        return

    # Use Gemini embeddings for retrieval; generation provider is independent
    client = GeminiClient()
    doc_embs = client.embed_texts(chunks, as_query=False)
    query_emb = client.embed_text(query, as_query=True)  # use single-text helper

    sims = _cosine_sim_matrix(doc_embs, np.expand_dims(query_emb, 0)).squeeze()
    top_idx = np.argsort(-sims)[:top_chunks]
    top_contexts = [chunks[i] for i in top_idx]
    top_sources = [meta[i]["url"] for i in top_idx]

    # Choose LLM provider for final answer
    if provider.lower() == "groq":
        llm = GroqClient()
        answer = llm.answer(query, top_contexts)
    else:
        answer = client.answer(query, top_contexts)

    print("\n=== Answer ===\n")
    print((answer or "").strip())
    print("\n=== Sources ===")
    for i, url in enumerate(dict.fromkeys(top_sources), start=1):
        print(f"[{i}] {url}")


def main():
    p = argparse.ArgumentParser(description="RAG: search → scrape → retrieve → answer (Gemini)")
    p.add_argument("-q", "--query", required=True, help="User question")
    p.add_argument("-m", "--max_results", type=int, default=5, help="Search results to fetch")
    p.add_argument("--top_docs", type=int, default=3, help="Top documents to scrape")
    p.add_argument("--top_chunks", type=int, default=8, help="Top chunks for context")
    p.add_argument("--provider", choices=["gemini", "groq"], default="gemini", help="LLM provider for answer generation")
    args = p.parse_args()
    run_rag(args.query, max_results=args.max_results, top_docs=args.top_docs, top_chunks=args.top_chunks, provider=args.provider)

if __name__ == "__main__":
    main()




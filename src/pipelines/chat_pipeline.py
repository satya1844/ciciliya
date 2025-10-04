import argparse
import time
from typing import List, Dict, Optional, AsyncGenerator
from ..search.serper_search import search_serper
from ..scraper.scraper import scrape_url  # Corrected import
from ..utils.chunking import chunk_text
# Switch from Gemini to Groq
from ..llm.groq_client import get_groq_response, get_groq_response_stream
from ..vector_store.chroma_db import ChromaDBManager
from langchain.docstore.document import Document as LangchainDocument
 

#This function is no longer needed with ChromaDB
# def _cosine_sim_matrix(a: np.ndarray, b: np.ndarray) -> np.ndarray:
#     a = a.astype(float); b = b.astype(float)
#     a_norm = a / (np.linalg.norm(a, axis=1, keepdims=True) + 1e-12)
#     b_norm = b / (np.linalg.norm(b, axis=1, keepdims=True) + 1e-12)
#     return a_norm @ b_norm.T

async def run_rag(query: str, max_results: int = 3) -> Optional[Dict]:
    start_time = time.time()
    last_step_time = start_time
    
    # Define constants that were previously passed as CLI args
    top_docs_to_scrape = max_results
    top_chunks_for_context = 8

    # 1. Search
    print(f"[{time.time() - start_time:.2f}s] 1. Searching for '{query}'...")
    results = search_serper(query, max_results=max_results)
    if not results:
        print("No results found.")
        return None
    print(f"   -> Search complete in {time.time() - last_step_time:.2f}s. Found {len(results)} results.")
    last_step_time = time.time()

    # 2. Scrape
    print(f"[{time.time() - start_time:.2f}s] 2. Scraping top {top_docs_to_scrape} documents...")
    docs: List[Dict] = []
    for r in results[:top_docs_to_scrape]:
        url = r["url"]
        if not url: continue
        try:
            article = scrape_url(url) # Corrected function call
            text = (article.get("text") or "").strip()
            if text:
                docs.append({"url": url, "title": article.get("title", "") or r.get("title",""), "text": text})
                print(f"   - Scraped: {url}")
        except Exception as e:
            print(f"   - Failed to scrape {url}: {e}")

    if not docs:
        print("Failed to scrape any documents.")
        return None
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
        return None
    print(f"   -> Chunking complete in {time.time() - last_step_time:.2f}s. Produced {len(all_docs)} chunks.")
    last_step_time = time.time()

    # 4. Embed & retrieve with ChromaDB
    print(f"[{time.time() - start_time:.2f}s] 4. Embedding & retrieving with ChromaDB...")
    db_manager = ChromaDBManager()
    db_manager.add_documents(all_docs)
    retrieved_chunks: List[Document] = db_manager.query(query, n_results=top_chunks_for_context)
    
    # Prepare context and sources for the LLM
    context = "\n\n".join([doc.page_content for doc in retrieved_chunks])
    
    # Deduplicate sources based on URL
    unique_sources = {doc.metadata['url']: doc.metadata for doc in retrieved_chunks}
    sources = list(unique_sources.values())

    print(f"   -> Embedding & Retrieval complete in {time.time() - last_step_time:.2f}s.")
    last_step_time = time.time()

    # 5. Generate with Groq
    print(f"[{time.time() - start_time:.2f}s] 5. Generating answer with GROQ...")
    prompt = f"Answer the following question: {query}"
    
    try:
        # Call the Groq function
        answer = await get_groq_response(prompt, context)
        print(f"   -> Generation complete in {time.time() - last_step_time:.2f}s.")
    except Exception as e:
        print(f"   -> Generation failed: {e}")
        answer = "Sorry, I was unable to generate an answer due to a temporary issue with the AI service. Please try again later."

    return {
        "answer": answer,
        "sources": [{"url": s.get('url', ''), "title": s.get('title', '')} for s in sources]
    }

async def run_rag_stream(query: str, max_results: int = 3) -> AsyncGenerator[Dict, None]:
    start_time = time.time()
    last_step_time = start_time
    
    # Define constants that were previously passed as CLI args
    top_docs_to_scrape = max_results
    top_chunks_for_context = 8

    # 1. Search
    print(f"[{time.time() - start_time:.2f}s] 1. Searching for '{query}'...")
    results = search_serper(query, max_results=max_results)
    if not results:
        yield {"type": "error", "data": "Could not find any sources."}
        return
    print(f"   -> Search complete in {time.time() - last_step_time:.2f}s. Found {len(results)} results.")
    last_step_time = time.time()

    # 2. Scrape
    print(f"[{time.time() - start_time:.2f}s] 2. Scraping top {top_docs_to_scrape} documents...")
    docs: List[Dict] = []
    for r in results[:top_docs_to_scrape]:
        url = r["url"]
        if not url: continue
        try:
            article = scrape_url(url) # Corrected function call
            text = (article.get("text") or "").strip()
            if text:
                docs.append({"url": url, "title": article.get("title", "") or r.get("title",""), "text": text})
                print(f"   - Scraped: {url}")
        except Exception as e:
            print(f"   - Failed to scrape {url}: {e}")

    if not docs:
        yield {"type": "error", "data": "Failed to scrape any documents."}
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
        yield {"type": "error", "data": "No chunks produced."}
        return
    print(f"   -> Chunking complete in {time.time() - last_step_time:.2f}s. Produced {len(all_docs)} chunks.")
    last_step_time = time.time()

    # 4. Embed & retrieve with ChromaDB
    print(f"[{time.time() - start_time:.2f}s] 4. Embedding & retrieving with ChromaDB...")
    db_manager = ChromaDBManager()
    db_manager.add_documents(all_docs)
    retrieved_chunks: List[Document] = db_manager.query(query, n_results=top_chunks_for_context)
    
    # Prepare context and sources for the LLM
    context = "\n\n".join([doc.page_content for doc in retrieved_chunks])
    
    # Deduplicate sources based on URL
    unique_sources = {doc.metadata['url']: doc.metadata for doc in retrieved_chunks}
    sources = list(unique_sources.values())

    print(f"   -> Embedding & Retrieval complete in {time.time() - last_step_time:.2f}s.")
    last_step_time = time.time()

    # 5. Generate and Stream Answer with Groq
    prompt = f"Answer the following question: {query}"
    # Call the Groq stream function
    async for token in get_groq_response_stream(prompt, context):
        yield {"type": "token", "data": token}

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


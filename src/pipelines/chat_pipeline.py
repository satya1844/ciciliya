import argparse
import time
from typing import List, Dict, Optional, AsyncGenerator, Tuple

from ..search.serper_search import search_serper
from ..scraper.scraper import scrape_url
from ..utils.chunking import chunk_text
from ..llm.groq_client import get_groq_response, get_groq_response_stream
from ..vector_store.chroma_db import ChromaDBManager, Document


class PipelineError(RuntimeError):
    """Raised when a pipeline stage cannot produce context."""


def _build_context(
    query: str,
    max_results: int,
    top_docs_to_scrape: int = 3,
    top_chunks_for_context: int = 8,
) -> Tuple[str, List[Dict]]:
    start_time = time.time()
    last_step_time = start_time

    results = search_serper(query, max_results=max_results)
    if results is None:
        raise PipelineError("Search service unavailable or API key missing.")
    if not results:
        raise PipelineError("No search results found for that query.")
    print(f"[{time.time() - start_time:.2f}s] Search complete. {len(results)} results found.")
    last_step_time = time.time()

    docs: List[Dict] = []
    for r in results[:top_docs_to_scrape]:
        url = r.get("url")
        if not url:
            continue
        try:
            article = scrape_url(url)
            text = (article.get("text") or "").strip()
            if text:
                docs.append(
                    {
                        "url": url,
                        "title": article.get("title", "") or r.get("title", ""),
                        "text": text,
                        "snippet": r.get("snippet", ""),
                    }
                )
                print(f"   - Scraped {url}")
        except Exception as exc:  # noqa: BLE001
            print(f"   - Failed to scrape {url}: {exc}")

    if not docs:
        raise PipelineError("Failed to scrape any documents from search results.")
    print(f"   -> Scraping complete in {time.time() - last_step_time:.2f}s ({len(docs)} documents).")
    last_step_time = time.time()

    all_docs: List[Document] = []
    for doc in docs:
        for chunk in chunk_text(doc["text"], max_words=220, overlap=40):
            all_docs.append(
                Document(
                    page_content=chunk,
                    metadata={
                        "url": doc["url"],
                        "title": doc["title"],
                        "snippet": doc.get("snippet", ""),
                    },
                )
            )

    if not all_docs:
        raise PipelineError("No content chunks available after processing scraped documents.")
    print(f"   -> Chunking complete in {time.time() - last_step_time:.2f}s ({len(all_docs)} chunks).")
    last_step_time = time.time()

    db_manager = ChromaDBManager(path=None)
    db_manager.add_documents(all_docs)
    retrieved_chunks: List[Document] = db_manager.query(query, n_results=top_chunks_for_context)

    if not retrieved_chunks:
        raise PipelineError("Could not retrieve relevant passages from the vector store.")

    context = "\n\n".join(doc.page_content for doc in retrieved_chunks)
    sources: Dict[str, Dict] = {}
    for doc in retrieved_chunks:
        metadata = doc.metadata or {}
        url = metadata.get("url")
        if not url or url in sources:
            continue
        sources[url] = {
            "url": url,
            "title": metadata.get("title", "Untitled"),
            "snippet": metadata.get("snippet", ""),
        }

    print(f"   -> Retrieval complete in {time.time() - last_step_time:.2f}s.")
    return context, list(sources.values())


async def run_rag(query: str, max_results: int = 3) -> Dict:
    try:
        context, sources = _build_context(
            query,
            max_results=max_results,
            top_docs_to_scrape=max_results,
        )
    except PipelineError as exc:
        return {"success": False, "error": str(exc), "answer": None, "sources": []}

    try:
        answer = await get_groq_response(query, context=context)
        return {"success": True, "answer": answer, "sources": sources}
    except Exception as exc:  # noqa: BLE001
        message = "Answer generation failed. Please try again later."
        print(f"   -> Generation failed: {exc}")
        return {"success": False, "error": message, "answer": None, "sources": sources}


async def run_rag_stream(query: str, max_results: int = 3) -> AsyncGenerator[Dict, None]:
    try:
        context, sources = _build_context(
            query,
            max_results=max_results,
            top_docs_to_scrape=max_results,
        )
    except PipelineError as exc:
        yield {"type": "error", "data": str(exc)}
        return

    try:
        async for token in get_groq_response_stream(query, context=context):
            yield {"type": "token", "data": token}
    except Exception as exc:  # noqa: BLE001
        print(f"   -> Streaming failed: {exc}")
        yield {"type": "error", "data": "Answer generation failed. Please try again later."}
        return

    yield {"type": "sources", "data": sources}


def main():
    parser = argparse.ArgumentParser(description="Run a single RAG query from the terminal.")
    parser.add_argument("-q", "--query", required=True, help="User question")
    parser.add_argument("-m", "--max_results", type=int, default=3, help="Search results to fetch")
    args = parser.parse_args()

    import asyncio

    result = asyncio.run(run_rag(args.query, max_results=args.max_results))
    if not result["success"]:
        print(f"Error: {result['error']}")
        return

    print(result["answer"])
    if result["sources"]:
        print("\nSources:")
        for idx, source in enumerate(result["sources"], start=1):
            print(f"[{idx}] {source['title']} - {source['url']}")


if __name__ == "__main__":
    main()


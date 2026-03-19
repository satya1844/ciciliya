# Ciciliya

Ciciliya is a **real-time browsing chatbot** that searches the web, scrapes relevant pages, and answers user questions using LLMs.

It includes:
- A **Python backend** (FastAPI) that performs search, scraping, extraction, retrieval, and LLM generation.
- A **React frontend** (Vite + Tailwind) that provides a streaming chat interface.
- A **CLI tool** for quick search + scraping directly from the terminal.

---

## 🚀 Features (Implemented Today)

✅ **Web search** using the Serper.dev API (Google search results)

✅ **Web page scraping** using `requests` + HTML parsing, with a **Playwright fallback** for JavaScript-heavy sites

✅ **Readable content extraction** using `readability-lxml` + BeautifulSoup

✅ **Retrieval-Augmented Generation (RAG)** pipeline:
- chunking text into semantic chunks
- embedding using `sentence-transformers` (all-MiniLM-L6-v2)
- storing + querying in **ChromaDB**
- generating answers with **Groq LLM** (streaming and non-streaming responses)

✅ **FastAPI backend** exposing:
- `/api/query` for standard responses
- `/api/stream` for streaming (SSE) token-by-token responses

✅ **React chat UI** with streaming updates, message history, and source attribution

✅ **Unit tests** covering search, scraping, and LLM helper logic

---

## 🧰 Prerequisites

### Required

- **Python 3.10+**
- **Node.js 18+** (for frontend)

### Optional (for full scraping support)

- **Playwright browsers**

  ```bash
  python -m playwright install chromium
  ```

---

## 🔑 Environment Variables

Create a `.env` file in the project root (you can copy `.env.example`) and set:

```ini
SERPER_API_KEY=<your-serper-key>
GROQ_API_KEY=<your-groq-key>
# Optional: alternative LLM provider (Gemini)
GOOGLE_API_KEY=<your-google-api-key>
# or
GEMINI_API_KEY=<your-gemini-key>
```

> Note: The CLI only requires `SERPER_API_KEY`. The RAG pipeline and API server require an LLM API key (`GROQ_API_KEY` or `GOOGLE_API_KEY`/`GEMINI_API_KEY`).

---

## 🏃‍♂️ Run the CLI (Quick Search + Scrape)

```bash
python -m src.main
```

Then type a search query, select a result number, and Ciciliya will scrape the chosen page.

### CLI Options

```bash
python -m src.main --query "latest AI news" --max_results 5
python -m src.main --url "https://example.com/article"
```

---

## 🖥️ Run the Backend API (FastAPI)

Install dependencies and start the server:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn src.api:app --reload --host 0.0.0.0 --port 8000
```

### API Endpoints

- `GET /` — basic status check
- `POST /api/query` — standard query (returns full answer)
- `POST /api/stream` — streaming response via Server-Sent Events (SSE)

---

## 🌐 Run the Frontend (React)

```bash
cd frontend
npm install
npm run dev
```

Open the URL shown in the terminal (usually `http://localhost:5173`).

> The frontend expects the backend at `http://localhost:8000` by default. Update `frontend/src/services/api.js` if you run the backend elsewhere.

---

## 🧪 Tests

Run unit tests with:

```bash
pytest
```

---

## 📁 Project Structure (Key Files)

- `src/main.py` — CLI entrypoint (search + scraping)
- `src/api.py` — FastAPI server with standard and streaming endpoints
- `src/pipelines/chat_pipeline.py` — RAG pipeline (search→scrape→embed→retrieve→LLM)
- `src/search/serper_search.py` — Serper.dev search wrapper
- `src/scraper/` — scraping + content extraction logic
- `src/llm/` — LLM wrappers (Groq + Gemini)
- `src/vector_store/` — ChromaDB embedding storage + retrieval
- `frontend/` — React chat UI (streaming SSE client)

---

## 🧩 Notes & Current Limitations

- **Search requires `SERPER_API_KEY`.** Without it, search cannot run.
- **LLM generation requires a valid API key (Groq or Gemini).** The code uses Groq by default.
- **Playwright is used only as a fallback**; it is slower and requires browser installation.
- The project is currently focused on single-query interactions; multi-turn chat state is not persisted.

---

## 📜 License

This repository is licensed under the terms in the `LICENSE` file.

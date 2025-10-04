import os
from typing import List, Optional
import numpy as np
import google.generativeai as genai
from dotenv import load_dotenv

# Load .env at import time so local development picks up API keys
load_dotenv()

def _get_api_key() -> str:
    return os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or ""

class GeminiClient:
    def __init__(self, model_name: str = "gemini-1.5-flash-latest", embed_model: str = "text-embedding-004"):
        api_key = _get_api_key()
        if not api_key:
            raise RuntimeError("Set GOOGLE_API_KEY or GEMINI_API_KEY in your environment.")
        # Force REST to avoid gRPC model routing issues on Windows
        genai.configure(api_key=api_key, transport="rest")
        # Auto-select a valid model if the preferred one isn't available
        selected = self._select_supported_model(preferred=model_name)
        self.model = genai.GenerativeModel(selected)
        self.embed_model = embed_model

    @staticmethod
    def _select_supported_model(preferred: Optional[str] = None) -> str:
        """Pick a supported model for generateContent, preferring a user-provided name.

        Falls back to a ranked list using genai.list_models(). Returns the fully-qualified
        model name (e.g., 'models/gemini-1.5-flash-8b') when available to match API responses.
        """
        try:
            models = list(genai.list_models())
        except Exception:
            # If listing models fails, return the preferred (may still work) or a safe default
            return preferred or "gemini-1.0-pro"

        # Filter models that can generate content
        def supports_generate(m) -> bool:
            methods = getattr(m, "supported_generation_methods", None) or []
            # Normalize names defensively
            methods_norm = {str(x).lower() for x in methods}
            return ("generatecontent" in methods_norm) or ("generate_content" in methods_norm) or ("text" in methods_norm)

        supported = [m for m in models if supports_generate(m)]
        if not supported:
            return preferred or "gemini-1.0-pro"

        # Build lookup of names (both fully-qualified and bare) to the object
        name_to_model = {}
        for m in supported:
            full = getattr(m, "name", "")  # e.g., 'models/gemini-1.5-flash-8b'
            bare = full.split("/")[-1] if full else ""
            if full:
                name_to_model[full] = m
            if bare:
                name_to_model[bare] = m

        # If user specified a model and it's supported, honor it
        if preferred and preferred in name_to_model:
            return preferred

        # Rank preferred candidates and pick the first available
        ranked = [
            "gemini-1.5-flash-8b",  # fast and widely available
            "gemini-1.5-flash",     
            "gemini-1.5-pro",
            "gemini-1.0-pro",
            "gemini-pro",
        ]
        for cand in ranked:
            if cand in name_to_model:
                # Use fully qualified name if present to avoid routing issues
                m = name_to_model[cand]
                return getattr(m, "name", cand)

        # Fall back to the first supported model
        m = supported[0]
        return getattr(m, "name", preferred or "gemini-1.0-pro")

    def embed_texts(self, texts: List[str], as_query: bool = False) -> np.ndarray:
        if not texts:
            return np.zeros((0, 768), dtype=float)
        task = "retrieval_query" if as_query else "retrieval_document"
        vecs: List[List[float]] = []
        for t in texts:
            resp = genai.embed_content(model=self.embed_model, content=t, task_type=task)
            vecs.append(resp["embedding"])
        return np.array(vecs, dtype=float)

    def embed_text(self, text: str, as_query: bool = False) -> np.ndarray:
        return self.embed_texts([text], as_query=as_query)[0]

    def answer(self, question: str, contexts: List[str]) -> str:
        if not contexts:
            return "No sufficient context found."
        context_block = "\n\n".join(f"[Source {i+1}]\n{c}" for i, c in enumerate(contexts))
        prompt = (
            "Answer using only the provided sources. Cite sources as [Source N]. "
            "If uncertain, say you don't know.\n\n"
            f"Question:\n{question}\n\nSources:\n{context_block}\n\nAnswer:"
        )
        try:
            resp = self.model.generate_content(prompt)
            return (getattr(resp, "text", None) or "").strip()
        except Exception as e:
            return f"LLM error: {e}"

async def get_gemini_response(user_prompt: str, context: str) -> str:
    """
    Generates a response from the Gemini model.
    Raises an exception if the API call fails.
    """
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        You are a helpful AI assistant that answers questions based on the provided context.
        Your answer must be grounded in the information given in the "CONTEXT" section.
        Do not use any information outside of the provided context.
        If the context does not contain the answer, say "I'm sorry, I couldn't find an answer in the provided sources."

        CONTEXT:
        {context}

        QUESTION:
        {user_prompt}

        ANSWER:
        """
        response = await model.generate_content_async(prompt)
        return response.text
    except Exception as e:
        print(f"LLM error: {e}")
        # Re-raise the exception to be handled by the caller
        raise e
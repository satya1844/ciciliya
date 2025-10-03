import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

try:
    from groq import Groq
except Exception as e:
    Groq = None  # type: ignore


class GroqClient:
    """Thin wrapper around Groq API for text generation.

    Exposes answer(question, contexts) similar to GeminiClient so the pipeline can swap providers.
    """

    def __init__(self, model: str = "llama-3.1-8b-instant"):
        api_key = os.getenv("GROQ_API_KEY") or os.getenv("GROQ_KEY") or ""
        if not api_key:
            raise RuntimeError("Set GROQ_API_KEY in your environment or .env")
        if Groq is None:
            raise RuntimeError("groq package not installed. Run: pip install groq")
        self.client = Groq(api_key=api_key)
        self.model = model

    def answer(self, question: str, contexts: List[str]) -> str:
        if not contexts:
            return "No sufficient context found."
        system = (
            "You are a helpful assistant. Answer strictly using the provided sources. "
            "Cite sources as [Source N]. If uncertain, say you don't know."
        )
        context_block = "\n\n".join(f"[Source {i+1}]\n{c}" for i, c in enumerate(contexts))
        user = f"Question:\n{question}\n\nSources:\n{context_block}\n\nAnswer:"

        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.2,
            max_tokens=600,
        )
        return (resp.choices[0].message.content or "").strip()

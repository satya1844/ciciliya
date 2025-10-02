from typing import List

def chunk_text(text: str, max_words: int = 220, overlap: int = 40) -> List[str]:
    words = text.split()
    if not words:
        return []
    chunks = []
    step = max(1, max_words - overlap)
    for i in range(0, len(words), step):
        chunk = " ".join(words[i : i + max_words])
        if chunk.strip():
            chunks.append(chunk)
    return chunks

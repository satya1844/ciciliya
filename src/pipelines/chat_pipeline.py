import argparse
from typing import List, Dict
import numpy as np
from ..search.ddg_search import search_web
from ..scraper.scraper import scrape_url
from ..utils.chunking import chunk_text
from ..llm.gemini_client import GeminiClient


def _cosine_sim_matrix(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a = a.astype(float); b = b.astype(float)
    a_norm = a / (np.linalg.norm(a, axis=1, keepdims=True) + 1e-12)
    b_norm = b / (np.linalg.norm(b, axis=1, keepdims=True) + 1e-12)
    return a_norm @ b_norm.T


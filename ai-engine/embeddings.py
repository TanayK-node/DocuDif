from typing import List, Optional
import numpy as np
import torch
from sentence_transformers import SentenceTransformer

DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
_EMBEDDER_INSTANCE: Optional[SentenceTransformer] = None

def get_embedder(model_name: str = DEFAULT_EMBEDDING_MODEL) -> SentenceTransformer:
    global _EMBEDDER_INSTANCE
    if _EMBEDDER_INSTANCE is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        _EMBEDDER_INSTANCE = SentenceTransformer(model_name, device=device)
    return _EMBEDDER_INSTANCE

def compute_embeddings(texts: List[str], model_name: str = DEFAULT_EMBEDDING_MODEL) -> np.ndarray:
    """
    Compute normalized embeddings for a list of strings.
    Returns L2-normalized float32 vectors.
    """
    if not texts:
        return np.empty((0, 384), dtype=np.float32)

    embedder = get_embedder(model_name)
    embeddings = embedder.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False
    )
    return embeddings.astype(np.float32)


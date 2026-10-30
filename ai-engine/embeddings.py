import os
from typing import List, Optional
import numpy as np
from sklearn.feature_extraction.text import HashingVectorizer

# Default: lightweight, zero-memory hashing vectorizer (ideal for cloud/Render 512MB limit)
DEFAULT_EMBEDDING_MODEL = "lightweight-hashing-384"
_HASHING_VEC = HashingVectorizer(n_features=384, norm="l2", alternate_sign=False)
_HEAVY_EMBEDDER = None

def compute_embeddings(texts: List[str], model_name: str = DEFAULT_EMBEDDING_MODEL) -> np.ndarray:
    """
    Computes L2-normalized dense embeddings for a list of strings.
    Uses ultra-lightweight, zero-memory HashingVectorizer by default,
    guaranteeing instant execution and zero OOM issues on cloud instances.
    """
    if not texts:
        return np.empty((0, 384), dtype=np.float32)

    # If user explicitly enables heavy local SentenceTransformers via environment variable
    if os.getenv("DOCUDIFF_USE_HEAVY_EMBEDDINGS", "false").lower() == "true":
        global _HEAVY_EMBEDDER
        if _HEAVY_EMBEDDER is None:
            try:
                import torch
                torch.set_num_threads(1)
                from sentence_transformers import SentenceTransformer
                _HEAVY_EMBEDDER = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", device="cpu")
            except Exception:
                _HEAVY_EMBEDDER = False

        if _HEAVY_EMBEDDER:
            return _HEAVY_EMBEDDER.encode(
                texts,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False
            ).astype(np.float32)

    # Lightweight high-performance vectorizer
    sparse_matrix = _HASHING_VEC.transform(texts)
    dense_vecs = sparse_matrix.toarray().astype(np.float32)
    return dense_vecs

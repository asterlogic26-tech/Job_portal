import logging
from typing import List, Union
import numpy as np

logger = logging.getLogger(__name__)

_model = None


def get_model():
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("Sentence transformer model loaded.")
        except Exception as e:
            logger.warning(f"Could not load sentence transformer: {e}. Using random embeddings.")
            _model = "dummy"
    return _model


def embed_text(text: str) -> List[float]:
    """Embed a single text string into a vector."""
    model = get_model()
    if model == "dummy":
        return list(np.random.rand(384).astype(float))
    try:
        embedding = model.encode(text, normalize_embeddings=True)
        return embedding.tolist()
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        return list(np.zeros(384).astype(float))


def embed_batch(texts: List[str]) -> List[List[float]]:
    """Embed a batch of texts."""
    model = get_model()
    if model == "dummy":
        return [list(np.random.rand(384).astype(float)) for _ in texts]
    try:
        embeddings = model.encode(texts, normalize_embeddings=True, batch_size=32)
        return [e.tolist() for e in embeddings]
    except Exception as e:
        logger.error(f"Batch embedding failed: {e}")
        return [list(np.zeros(384).astype(float)) for _ in texts]


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    a = np.array(vec1)
    b = np.array(vec2)
    if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
        return 0.0
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

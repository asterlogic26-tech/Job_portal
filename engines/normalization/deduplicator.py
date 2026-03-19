import hashlib
import logging
from typing import Optional
from engines.embedding.embedder import cosine_similarity

logger = logging.getLogger(__name__)

DUPLICATE_COSINE_THRESHOLD = 0.95


def compute_content_hash(title: str, company: str, description: str) -> str:
    """Compute a hash for deduplication."""
    content = f"{title.lower().strip()}::{company.lower().strip()}::{description[:500].strip()}"
    return hashlib.sha256(content.encode()).hexdigest()


def is_near_duplicate(
    embedding1: list,
    embedding2: list,
    threshold: float = DUPLICATE_COSINE_THRESHOLD,
) -> bool:
    """Check if two embeddings represent near-duplicate content."""
    similarity = cosine_similarity(embedding1, embedding2)
    return similarity >= threshold

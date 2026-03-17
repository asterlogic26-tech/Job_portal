"""
Tests for engines.embedding.embedder.

The sentence-transformer model is NOT loaded during these tests
(it requires significant memory and network access).  We mock the
``get_model()`` helper to return the "dummy" sentinel, which causes
the module to fall back to deterministic random/zero vectors.
"""
import pytest
from unittest.mock import patch


# ── embed_text ────────────────────────────────────────────────────────────────

class TestEmbedText:
    def test_returns_list_of_floats(self):
        from engines.embedding.embedder import embed_text
        with patch("engines.embedding.embedder.get_model", return_value="dummy"):
            vec = embed_text("Hello world")
        assert isinstance(vec, list)
        assert all(isinstance(v, float) for v in vec)

    def test_vector_dimension_is_384(self):
        from engines.embedding.embedder import embed_text
        with patch("engines.embedding.embedder.get_model", return_value="dummy"):
            vec = embed_text("test text")
        assert len(vec) == 384

    def test_empty_string_does_not_crash(self):
        from engines.embedding.embedder import embed_text
        with patch("engines.embedding.embedder.get_model", return_value="dummy"):
            vec = embed_text("")
        assert len(vec) == 384

    def test_model_exception_returns_zero_vector(self):
        """If the model raises, embed_text must still return a zero vector."""
        from engines.embedding.embedder import embed_text
        import unittest.mock as um

        mock_model = um.MagicMock()
        mock_model.encode.side_effect = RuntimeError("GPU OOM")

        with patch("engines.embedding.embedder.get_model", return_value=mock_model):
            vec = embed_text("test")
        assert len(vec) == 384
        assert all(v == 0.0 for v in vec)


# ── embed_batch ───────────────────────────────────────────────────────────────

class TestEmbedBatch:
    def test_returns_list_of_vectors(self):
        from engines.embedding.embedder import embed_batch
        with patch("engines.embedding.embedder.get_model", return_value="dummy"):
            vecs = embed_batch(["first", "second", "third"])
        assert len(vecs) == 3
        assert all(len(v) == 384 for v in vecs)

    def test_empty_batch_returns_empty_list(self):
        from engines.embedding.embedder import embed_batch
        with patch("engines.embedding.embedder.get_model", return_value="dummy"):
            vecs = embed_batch([])
        assert vecs == []

    def test_batch_model_exception_returns_zero_vectors(self):
        from engines.embedding.embedder import embed_batch
        import unittest.mock as um

        mock_model = um.MagicMock()
        mock_model.encode.side_effect = RuntimeError("fail")

        with patch("engines.embedding.embedder.get_model", return_value=mock_model):
            vecs = embed_batch(["a", "b"])
        assert len(vecs) == 2
        assert all(len(v) == 384 for v in vecs)


# ── cosine_similarity ─────────────────────────────────────────────────────────

class TestCosineSimilarity:
    def test_identical_vectors_score_one(self):
        from engines.embedding.embedder import cosine_similarity
        vec = [1.0, 0.0, 0.0]
        assert cosine_similarity(vec, vec) == pytest.approx(1.0, abs=1e-6)

    def test_opposite_vectors_score_minus_one(self):
        from engines.embedding.embedder import cosine_similarity
        a = [1.0, 0.0]
        b = [-1.0, 0.0]
        assert cosine_similarity(a, b) == pytest.approx(-1.0, abs=1e-6)

    def test_orthogonal_vectors_score_zero(self):
        from engines.embedding.embedder import cosine_similarity
        a = [1.0, 0.0]
        b = [0.0, 1.0]
        assert cosine_similarity(a, b) == pytest.approx(0.0, abs=1e-6)

    def test_zero_vector_returns_zero(self):
        from engines.embedding.embedder import cosine_similarity
        assert cosine_similarity([0.0, 0.0], [1.0, 0.0]) == 0.0

    def test_result_between_minus_one_and_one(self):
        import random
        from engines.embedding.embedder import cosine_similarity
        random.seed(42)
        a = [random.gauss(0, 1) for _ in range(384)]
        b = [random.gauss(0, 1) for _ in range(384)]
        sim = cosine_similarity(a, b)
        assert -1.0 <= sim <= 1.0

import logging
import uuid
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)


class VectorStore:
    """Qdrant vector store wrapper."""

    def __init__(self, url: str, collection_name: str, vector_size: int = 384):
        self.url = url
        self.collection_name = collection_name
        self.vector_size = vector_size
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from qdrant_client import QdrantClient
                from qdrant_client.models import Distance, VectorParams
                self._client = QdrantClient(url=self.url)
                # Ensure collection exists
                try:
                    self._client.get_collection(self.collection_name)
                except Exception:
                    self._client.create_collection(
                        collection_name=self.collection_name,
                        vectors_config=VectorParams(
                            size=self.vector_size,
                            distance=Distance.COSINE,
                        ),
                    )
                    logger.info(f"Created Qdrant collection: {self.collection_name}")
            except Exception as e:
                logger.warning(f"Qdrant not available: {e}. Using in-memory fallback.")
                self._client = InMemoryVectorStore()
        return self._client

    def upsert(self, id: str, vector: List[float], payload: Dict[str, Any]) -> bool:
        client = self._get_client()
        try:
            if isinstance(client, InMemoryVectorStore):
                return client.upsert(id, vector, payload)
            from qdrant_client.models import PointStruct
            client.upsert(
                collection_name=self.collection_name,
                points=[PointStruct(id=id, vector=vector, payload=payload)],
            )
            return True
        except Exception as e:
            logger.error(f"Qdrant upsert failed: {e}")
            return False

    def search(self, vector: List[float], limit: int = 20, filter_dict: Optional[Dict] = None) -> List[Dict]:
        client = self._get_client()
        try:
            if isinstance(client, InMemoryVectorStore):
                return client.search(vector, limit)
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            query_filter = None
            if filter_dict:
                conditions = [
                    FieldCondition(key=k, match=MatchValue(value=v))
                    for k, v in filter_dict.items()
                ]
                query_filter = Filter(must=conditions)

            results = client.search(
                collection_name=self.collection_name,
                query_vector=vector,
                limit=limit,
                query_filter=query_filter,
            )
            return [
                {"id": str(r.id), "score": r.score, "payload": r.payload}
                for r in results
            ]
        except Exception as e:
            logger.error(f"Qdrant search failed: {e}")
            return []

    def delete(self, id: str) -> bool:
        client = self._get_client()
        try:
            if isinstance(client, InMemoryVectorStore):
                return client.delete(id)
            from qdrant_client.models import PointIdsList
            client.delete(
                collection_name=self.collection_name,
                points_selector=PointIdsList(points=[id]),
            )
            return True
        except Exception as e:
            logger.error(f"Qdrant delete failed: {e}")
            return False


class InMemoryVectorStore:
    """Fallback in-memory vector store when Qdrant is unavailable."""

    def __init__(self):
        self._store: Dict[str, Dict] = {}

    def upsert(self, id: str, vector: List[float], payload: Dict) -> bool:
        self._store[id] = {"vector": vector, "payload": payload}
        return True

    def search(self, vector: List[float], limit: int = 20) -> List[Dict]:
        import numpy as np
        if not self._store:
            return []
        results = []
        query = np.array(vector)
        for id, data in self._store.items():
            stored = np.array(data["vector"])
            score = float(np.dot(query, stored) / (np.linalg.norm(query) * np.linalg.norm(stored) + 1e-8))
            results.append({"id": id, "score": score, "payload": data["payload"]})
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]

    def delete(self, id: str) -> bool:
        return bool(self._store.pop(id, None))

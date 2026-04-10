from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    Tries to use ChromaDB if available; falls back to an in-memory store.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

        try:
            import chromadb  # noqa: F401

            # TODO: initialize chromadb client + collection
            self._client = chromadb.Client()
            self._collection = self._client.get_or_create_collection(name=self._collection_name)
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        # TODO: build a normalized stored record for one document
        record = {
            "id": f"{doc.id}-{self._next_index}",
            "content": doc.content,
            "metadata": {**doc.metadata, "doc_id": doc.id},
            "embedding": self._embedding_fn(doc.content),
        }
        self._next_index += 1
        return record

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        # TODO: run in-memory similarity search over provided records
        if top_k <= 0 or not records:
            return []

        query_embedding = self._embedding_fn(query)
        scored: list[dict[str, Any]] = []
        for record in records:
            score = _dot(query_embedding, record.get("embedding", []))
            scored.append(
                {
                    "id": record.get("id"),
                    "content": record.get("content", ""),
                    "metadata": record.get("metadata", {}),
                    "score": score,
                }
            )
        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store
        """
        # TODO: embed each doc and add to store
        if not docs:
            return

        records = [self._make_record(doc) for doc in docs]

        if self._use_chroma and self._collection is not None:
            self._collection.add(
                ids=[record["id"] for record in records],
                documents=[record["content"] for record in records],
                embeddings=[record["embedding"] for record in records],
                metadatas=[record["metadata"] for record in records],
            )
            return

        self._store.extend(records)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        # TODO: embed query, compute similarities, return top_k
        if top_k <= 0:
            return []

        if self._use_chroma and self._collection is not None:
            query_embedding = self._embedding_fn(query)
            result = self._collection.query(query_embeddings=[query_embedding], n_results=top_k)

            ids = result.get("ids", [[]])[0]
            documents = result.get("documents", [[]])[0]
            metadatas = result.get("metadatas", [[]])[0]
            distances = result.get("distances", [[]])[0]

            output: list[dict[str, Any]] = []
            for idx, doc_id in enumerate(ids):
                distance = distances[idx] if idx < len(distances) else 0.0
                output.append(
                    {
                        "id": doc_id,
                        "content": documents[idx] if idx < len(documents) else "",
                        "metadata": metadatas[idx] if idx < len(metadatas) and metadatas[idx] is not None else {},
                        "score": -float(distance),
                    }
                )
            output.sort(key=lambda item: item["score"], reverse=True)
            return output[:top_k]

        return self._search_records(query=query, records=self._store, top_k=top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        # TODO
        if self._use_chroma and self._collection is not None:
            return int(self._collection.count())
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        # TODO: filter by metadata, then search among filtered chunks
        if top_k <= 0:
            return []

        if not metadata_filter:
            return self.search(query=query, top_k=top_k)

        if self._use_chroma and self._collection is not None:
            query_embedding = self._embedding_fn(query)
            result = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=metadata_filter,
            )
            ids = result.get("ids", [[]])[0]
            documents = result.get("documents", [[]])[0]
            metadatas = result.get("metadatas", [[]])[0]
            distances = result.get("distances", [[]])[0]

            output: list[dict[str, Any]] = []
            for idx, doc_id in enumerate(ids):
                distance = distances[idx] if idx < len(distances) else 0.0
                output.append(
                    {
                        "id": doc_id,
                        "content": documents[idx] if idx < len(documents) else "",
                        "metadata": metadatas[idx] if idx < len(metadatas) and metadatas[idx] is not None else {},
                        "score": -float(distance),
                    }
                )
            output.sort(key=lambda item: item["score"], reverse=True)
            return output[:top_k]

        filtered_records = [
            record
            for record in self._store
            if all(record.get("metadata", {}).get(key) == value for key, value in metadata_filter.items())
        ]
        return self._search_records(query=query, records=filtered_records, top_k=top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        # TODO: remove all stored chunks where metadata['doc_id'] == doc_id
        if self._use_chroma and self._collection is not None:
            try:
                existing = self._collection.get(where={"doc_id": doc_id})
                existing_ids = existing.get("ids", [])
                if not existing_ids:
                    return False
                self._collection.delete(where={"doc_id": doc_id})
                return True
            except Exception:
                return False

        size_before = len(self._store)
        self._store = [
            record for record in self._store if record.get("metadata", {}).get("doc_id") != doc_id
        ]
        return len(self._store) < size_before

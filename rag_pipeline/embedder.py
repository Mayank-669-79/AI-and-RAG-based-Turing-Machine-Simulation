"""Create embeddings for document chunks and queries."""
"""Embedding model wrapper with lazy loading."""

from __future__ import annotations

from typing import Sequence


DEFAULT_EMBEDDING_MODEL = (
    "sentence-transformers/all-MiniLM-L6-v2"
)


class Embedder:
    """Create embeddings using Sentence Transformers."""

    def __init__(
        self,
        model_name: str = DEFAULT_EMBEDDING_MODEL,
    ) -> None:
        self.model_name = model_name
        self._model = None

    def _load(self):
        """Load the embedding model only when it is needed."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:
                raise RuntimeError(
                    "sentence-transformers is required. "
                    "Install it with: "
                    "pip install sentence-transformers"
                ) from exc

            self._model = SentenceTransformer(self.model_name)

        return self._model

    def embed(
        self,
        texts: Sequence[str],
    ) -> list[list[float]]:
        """Return vectors for a list of text values."""
        if not texts:
            return []

        vectors = self._load().encode(
            list(texts),
            normalize_embeddings=True,
        )

        return vectors.tolist()

    def embed_one(self, text: str) -> list[float]:
        """Return one vector for a query string."""
        return self.embed([text])[0]

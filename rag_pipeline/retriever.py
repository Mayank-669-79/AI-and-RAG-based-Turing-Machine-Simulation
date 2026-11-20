"""Retrieve relevant chunks for a user query."""


"""Retrieve relevant automata knowledge for a user condition."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .embedder import (
    DEFAULT_EMBEDDING_MODEL,
    Embedder,
)
from .store import (
    DEFAULT_COLLECTION,
    get_collection,
    query_collection,
)


def retrieve_context(
    query: str,
    top_k: int = 4,
    persist_directory: str | Path | None = None,
    collection_name: str = DEFAULT_COLLECTION,
    model_name: str = DEFAULT_EMBEDDING_MODEL,
) -> list[dict[str, Any]]:
    """Return relevant knowledge chunks with metadata.

    Retrieved text is reference material only.
    It must never be executed as code.
    """
    if not query or not query.strip():
        raise ValueError("query must not be empty")

    if top_k <= 0:
        raise ValueError("top_k must be positive")

    directory = (
        persist_directory
        or os.getenv(
            "CHROMA_PERSIST_DIRECTORY",
            "data/chroma",
        )
    )

    collection = get_collection(
        persist_directory=directory,
        collection_name=collection_name,
    )

    embedder = Embedder(model_name=model_name)
    query_embedding = embedder.embed_one(query)

    result = query_collection(
        collection=collection,
        query_embedding=query_embedding,
        top_k=top_k,
    )

    documents = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0]
    ids = result.get("ids", [[]])[0]

    matches: list[dict[str, Any]] = []

    for index, text in enumerate(documents):
        metadata = (
            metadatas[index]
            if index < len(metadatas)
            else {}
        )

        matches.append(
            {
                "chunk_id": (
                    ids[index]
                    if index < len(ids)
                    else None
                ),
                "text": text,
                "source": metadata.get("source"),
                "topic": metadata.get("topic"),
                "language": metadata.get("language"),
                "content_type": metadata.get(
                    "content_type"
                ),
                "distance": (
                    distances[index]
                    if index < len(distances)
                    else None
                ),
            }
        )

    return matches

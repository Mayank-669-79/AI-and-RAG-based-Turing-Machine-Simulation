"""Manage the vector store."""
"""ChromaDB persistence helpers for RAG documents."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable


# Name of the ChromaDB collection used by this project.
DEFAULT_COLLECTION = "tm_automata_knowledge"


def get_collection(
    persist_directory: str | Path = "data/chroma",
    collection_name: str = DEFAULT_COLLECTION,
):
    """Open or create a persistent ChromaDB collection."""
    try:
        import chromadb
    except ImportError as exc:
        raise RuntimeError(
            "chromadb is required. "
            "Install it with: pip install chromadb"
        ) from exc

    # Create the storage directory if it does not exist.
    persist_path = Path(persist_directory)
    persist_path.mkdir(parents=True, exist_ok=True)

    # Create a persistent ChromaDB client.
    client = chromadb.PersistentClient(
        path=str(persist_path)
    )

    # Return an existing collection or create a new one.
    return client.get_or_create_collection(
        name=collection_name,
        metadata={
            "description": (
                "Curated Turing Machine knowledge "
                "for RAG retrieval"
            )
        },
    )


def upsert_chunks(
    collection: Any,
    chunks: Iterable[Any],
    embeddings: list[list[float]],
) -> int:
    """Insert or replace document chunks and embeddings."""
    chunk_list = list(chunks)

    # Every chunk must have exactly one embedding.
    if len(chunk_list) != len(embeddings):
        raise ValueError(
            "The number of chunks must equal "
            "the number of embeddings"
        )

    if not chunk_list:
        return 0

    # Store text, metadata, IDs, and vectors in ChromaDB.
    collection.upsert(
        ids=[
            chunk.chunk_id
            for chunk in chunk_list
        ],
        documents=[
            chunk.text
            for chunk in chunk_list
        ],
        metadatas=[
            chunk.metadata()
            for chunk in chunk_list
        ],
        embeddings=embeddings,
    )

    return len(chunk_list)


def query_collection(
    collection: Any,
    query_embedding: list[float],
    top_k: int = 4,
) -> dict:
    """Search the collection using an embedded query."""
    if top_k <= 0:
        raise ValueError("top_k must be positive")

    # Return the most relevant documents and metadata.
    return collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=[
            "documents",
            "metadatas",
            "distances",
        ],
    )

"""Load source documents into the RAG pipeline."""
"""Ingest Markdown knowledge files into ChromaDB."""

from __future__ import annotations

import argparse
from pathlib import Path

from .chunker import load_knowledge_chunks
from .embedder import (
    DEFAULT_EMBEDDING_MODEL,
    Embedder,
)
from .store import (
    DEFAULT_COLLECTION,
    get_collection,
    upsert_chunks,
)


PACKAGE_DIR = Path(__file__).resolve().parent

DEFAULT_KNOWLEDGE_DIR = (
    PACKAGE_DIR / "knowledge_base"
)


def ingest_knowledge_base(
    knowledge_dir: str | Path = DEFAULT_KNOWLEDGE_DIR,
    persist_directory: str | Path = "data/chroma",
    collection_name: str = DEFAULT_COLLECTION,
    model_name: str = DEFAULT_EMBEDDING_MODEL,
    chunk_size: int = 1800,
    overlap: int = 250,
) -> int:
    """Chunk, embed, and store all Markdown documents."""
    chunks = load_knowledge_chunks(
        knowledge_dir=knowledge_dir,
        chunk_size=chunk_size,
        overlap=overlap,
    )

    if not chunks:
        raise RuntimeError(
            f"No Markdown files found in {knowledge_dir}"
        )

    embedder = Embedder(model_name=model_name)

    embeddings = embedder.embed(
        [chunk.text for chunk in chunks]
    )

    collection = get_collection(
        persist_directory=persist_directory,
        collection_name=collection_name,
    )

    return upsert_chunks(
        collection=collection,
        chunks=chunks,
        embeddings=embeddings,
    )


def main() -> None:
    """Run knowledge-base ingestion from the command line."""
    parser = argparse.ArgumentParser(
        description="Ingest TM RAG knowledge"
    )

    parser.add_argument(
        "--knowledge-dir",
        default=str(DEFAULT_KNOWLEDGE_DIR),
    )

    parser.add_argument(
        "--persist-dir",
        default="data/chroma",
    )

    parser.add_argument(
        "--collection",
        default=DEFAULT_COLLECTION,
    )

    parser.add_argument(
        "--model",
        default=DEFAULT_EMBEDDING_MODEL,
    )

    parser.add_argument(
        "--chunk-size",
        type=int,
        default=1800,
    )

    parser.add_argument(
        "--overlap",
        type=int,
        default=250,
    )

    args = parser.parse_args()

    count = ingest_knowledge_base(
        knowledge_dir=args.knowledge_dir,
        persist_directory=args.persist_dir,
        collection_name=args.collection,
        model_name=args.model,
        chunk_size=args.chunk_size,
        overlap=args.overlap,
    )

    print(
        f"Ingested {count} chunks into "
        f"'{args.collection}'."
    )


if __name__ == "__main__":
    main()

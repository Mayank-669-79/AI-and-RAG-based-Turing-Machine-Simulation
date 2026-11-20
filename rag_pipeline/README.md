# RAG Pipeline

A modular Retrieval-Augmented Generation (RAG) pipeline.

## Structure

- `ingest.py` — load source documents
- `chunker.py` — split documents into chunks
- `embedder.py` — generate embeddings
- `retriever.py` — retrieve relevant chunks
- `store.py` — manage vector storage
- `knowledge_base/` — Markdown knowledge sources

## Getting started

Implement each module and connect the stages:

1. Ingest documents from `knowledge_base/`.
2. Chunk the document text.
3. Generate embeddings for each chunk.
4. Store embeddings and metadata.
5. Retrieve relevant chunks for a query.

"""Utilities for splitting Markdown knowledge files into searchable chunks."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DocumentChunk:
    """A text chunk plus metadata used by the vector store."""

    chunk_id: str
    text: str
    source: str
    topic: str
    language: str = "binary"
    content_type: str = "reference"

    def metadata(self) -> dict[str, str]:
        """Return Chroma-compatible string metadata."""
        return {
            "source": self.source,
            "topic": self.topic,
            "language": self.language,
            "content_type": self.content_type,
        }


def _topic_for_path(path: Path, text: str) -> str:
    """Infer a stable topic from the file name and document text."""
    name = path.stem.lower()
    text_lower = text.lower()

    if "even_zero" in name or "parity" in text_lower:
        return "count_parity"

    if "ends_with" in name:
        return "ends_with"

    if "contains" in name or "substring" in name:
        return "contains"

    if "transition" in name:
        return "transition_rules"

    if "basic" in name:
        return "tm_basics"

    return name.replace("-", "_")


def _content_type_for_path(path: Path) -> str:
    """Classify a knowledge document for UI explanations."""
    if "examples" in path.parts:
        return "construction_example"

    return "reference"


def _normalise(text: str) -> str:
    """Clean excess whitespace while preserving paragraph boundaries."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_markdown(
    path: str | Path,
    chunk_size: int = 1800,
    overlap: int = 250,
) -> list[DocumentChunk]:
    """Split one Markdown file into overlapping chunks.

    chunk_size and overlap are character counts.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError(
            "overlap must be >= 0 and smaller than chunk_size"
        )

    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(f"Knowledge file not found: {file_path}")

    text = _normalise(file_path.read_text(encoding="utf-8"))

    if not text:
        return []

    paragraphs = [
        part.strip()
        for part in text.split("\n\n")
        if part.strip()
    ]

    pieces: list[str] = []
    current = ""

    for paragraph in paragraphs:
        candidate = (
            f"{current}\n\n{paragraph}".strip()
            if current
            else paragraph
        )

        if len(candidate) <= chunk_size:
            current = candidate
        else:
            if current:
                pieces.append(current)

            # Split an unusually long paragraph safely.
            while len(paragraph) > chunk_size:
                pieces.append(paragraph[:chunk_size].strip())
                paragraph = paragraph[max(0, chunk_size - overlap):]

            current = paragraph

    if current:
        pieces.append(current)

    source = file_path.name
    topic = _topic_for_path(file_path, text)
    content_type = _content_type_for_path(file_path)

    chunks: list[DocumentChunk] = []

    for index, piece in enumerate(pieces, start=1):
        digest = hashlib.sha1(
            piece.encode("utf-8")
        ).hexdigest()[:10]

        chunks.append(
            DocumentChunk(
                chunk_id=f"{file_path.stem}-{index:03d}-{digest}",
                text=piece,
                source=source,
                topic=topic,
                content_type=content_type,
            )
        )

    return chunks


def load_knowledge_chunks(
    knowledge_dir: str | Path,
    chunk_size: int = 1800,
    overlap: int = 250,
) -> list[DocumentChunk]:
    """Load and chunk every Markdown file in a knowledge directory."""
    root = Path(knowledge_dir)

    if not root.exists():
        raise FileNotFoundError(
            f"Knowledge directory not found: {root}"
        )

    chunks: list[DocumentChunk] = []

    for path in sorted(root.rglob("*.md")):
        chunks.extend(
            chunk_markdown(
                path,
                chunk_size=chunk_size,
                overlap=overlap,
            )
        )

    return chunks

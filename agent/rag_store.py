from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import faiss
import numpy as np

from agent.embeddings import SentenceEmbeddingSimilarity

BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_KNOWLEDGE_DIR = BASE_DIR / "knowledge" / "brain_boosting"
DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"


@dataclass(slots=True)
class KnowledgeChunk:
    doc_id: str
    title: str
    content: str
    tags: list[str]
    source_path: str
    chunk_index: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "title": self.title,
            "content": self.content,
            "tags": self.tags,
            "source_path": self.source_path,
            "chunk_index": self.chunk_index,
        }


class FaissRagStore:
    """Local file-backed RAG store indexed with FAISS."""

    def __init__(
        self,
        knowledge_dir: Path | str = DEFAULT_KNOWLEDGE_DIR,
        embedding_model: SentenceEmbeddingSimilarity | None = None,
        chunk_size: int = 900,
        chunk_overlap: int = 120,
    ) -> None:
        self.knowledge_dir = Path(knowledge_dir)
        self.embedding_model = embedding_model or SentenceEmbeddingSimilarity(DEFAULT_EMBEDDING_MODEL)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.documents = self._load_documents()
        self.index = self._build_index(self.documents)

    def query(self, text: str, limit: int = 3) -> list[dict[str, Any]]:
        if self.index is None or not self.documents:
            return []

        query_vector = self.embedding_model.encode(text).reshape(1, -1)
        if not np.any(query_vector):
            return []

        scores, indexes = self.index.search(query_vector, min(limit, len(self.documents)))
        results: list[dict[str, Any]] = []
        for score, index in zip(scores[0], indexes[0]):
            if index < 0 or score <= 0:
                continue
            document = self.documents[int(index)]
            results.append({"score": round(float(score), 4), **document.to_dict()})
        return results

    def _build_index(self, documents: list[KnowledgeChunk]) -> faiss.IndexFlatIP | None:
        if not documents:
            return None

        texts = [f"{doc.title}\n{doc.content}\nTags: {', '.join(doc.tags)}" for doc in documents]
        vectors = self.embedding_model.encode_many(texts)
        index = faiss.IndexFlatIP(vectors.shape[1])
        index.add(vectors)
        return index

    def _load_documents(self) -> list[KnowledgeChunk]:
        if not self.knowledge_dir.exists():
            return []

        documents: list[KnowledgeChunk] = []
        for path in sorted(self.knowledge_dir.rglob("*")):
            if path.suffix.lower() not in {".md", ".txt"}:
                continue
            text = path.read_text(encoding="utf-8").strip()
            if not text:
                continue
            title = self._extract_title(text, path)
            tags = self._extract_tags(text)
            source_path = str(path.relative_to(BASE_DIR))
            for chunk_index, chunk in enumerate(self._chunk_text(text)):
                doc_id = self._doc_id(source_path, chunk_index, chunk)
                documents.append(
                    KnowledgeChunk(
                        doc_id=doc_id,
                        title=title,
                        content=chunk,
                        tags=tags,
                        source_path=source_path,
                        chunk_index=chunk_index,
                    )
                )
        return documents

    def _chunk_text(self, text: str) -> list[str]:
        paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
        chunks: list[str] = []
        current = ""

        for paragraph in paragraphs:
            candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
            if len(candidate) <= self.chunk_size:
                current = candidate
                continue
            if current:
                chunks.append(current)
            current = paragraph

        if current:
            chunks.append(current)

        if self.chunk_overlap <= 0 or len(chunks) < 2:
            return chunks

        overlapped = [chunks[0]]
        for chunk in chunks[1:]:
            previous_tail = self._word_tail(overlapped[-1])
            overlapped.append(f"{previous_tail}\n\n{chunk}".strip())
        return overlapped

    def _word_tail(self, text: str) -> str:
        tail = text[-self.chunk_overlap :].strip()
        if " " not in tail:
            return tail
        return tail.split(" ", 1)[1].strip()

    def _extract_title(self, text: str, path: Path) -> str:
        match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
        if match:
            return match.group(1).strip()
        return path.stem.replace("-", " ").replace("_", " ").title()

    def _extract_tags(self, text: str) -> list[str]:
        match = re.search(r"^Tags:\s*(.+)$", text, re.IGNORECASE | re.MULTILINE)
        if not match:
            return []
        return [tag.strip().lower() for tag in match.group(1).split(",") if tag.strip()]

    def _doc_id(self, source_path: str, chunk_index: int, chunk: str) -> str:
        digest = hashlib.sha1(f"{source_path}:{chunk_index}:{chunk}".encode("utf-8")).hexdigest()[:12]
        return f"kb-{digest}"


# Backward-compatible names for older imports.
FileRagStore = FaissRagStore
LocalChromaStore = FaissRagStore

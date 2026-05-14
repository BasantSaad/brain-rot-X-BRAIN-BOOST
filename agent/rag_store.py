from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agent.embeddings import SimpleEmbeddingModel


@dataclass(slots=True)
class KnowledgeDocument:
    doc_id: str
    title: str
    content: str
    tags: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "title": self.title,
            "content": self.content,
            "tags": self.tags,
        }


class LocalChromaStore:
    """A lightweight local retrieval store that mirrors the role of Chroma in this project."""

    def __init__(self, embedding_model: SimpleEmbeddingModel | None = None) -> None:
        self.embedding_model = embedding_model or SimpleEmbeddingModel()
        self.documents = self._seed_documents()
        self.index = {doc.doc_id: self.embedding_model.embed(f"{doc.title} {doc.content} {' '.join(doc.tags)}") for doc in self.documents}

    def query(self, text: str, limit: int = 3) -> list[dict[str, Any]]:
        query_vector = self.embedding_model.embed(text)
        scored = []
        for doc in self.documents:
            score = self.embedding_model.similarity(query_vector, self.index[doc.doc_id])
            if score > 0:
                scored.append({"score": round(score, 4), **doc.to_dict()})
        scored.sort(key=lambda item: (-item["score"], item["title"]))
        return scored[:limit]

    def _seed_documents(self) -> list[KnowledgeDocument]:
        return [
            KnowledgeDocument(
                doc_id="kb-session-1",
                title="Focus session tuning",
                content="When energy is low, shorten deep-work sessions to 20-30 minutes. When energy is stable and sleep improves, move toward 45-60 minutes.",
                tags=["session", "focus", "timer", "minutes", "study"],
            ),
            KnowledgeDocument(
                doc_id="kb-sleep-1",
                title="Sleep protection",
                content="Protect the last two hours before bedtime by reducing fast-switching apps and turning to lighter, calmer tasks. Consistent sleep improves focus recovery.",
                tags=["sleep", "bedtime", "night", "recovery"],
            ),
            KnowledgeDocument(
                doc_id="kb-weekly-1",
                title="Weekly progress interpretation",
                content="Weekly progress becomes more reliable when timer completions, check-ins, and app usage logs are saved consistently for seven days.",
                tags=["weekly", "summary", "streak", "progress"],
            ),
            KnowledgeDocument(
                doc_id="kb-risk-1",
                title="Risk window coaching",
                content="A risk window is the period where distraction usually rises. During that time, reduce social apps and use shorter tasks or timers.",
                tags=["risk", "window", "distraction", "apps"],
            ),
            KnowledgeDocument(
                doc_id="kb-parent-1",
                title="Parent guidance",
                content="Parent summaries should stay supportive. Use weekly trends and gentle boundaries instead of minute-by-minute surveillance.",
                tags=["parent", "guardian", "support", "summary"],
            ),
        ]

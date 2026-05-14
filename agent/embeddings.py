from __future__ import annotations

import math
import re
from collections import Counter


class SimpleEmbeddingModel:
    """A tiny local embedding model used as an offline stand-in for real vector embeddings."""

    token_pattern = re.compile(r"[a-z0-9]+", re.IGNORECASE)

    def embed(self, text: str) -> Counter[str]:
        tokens = [token.lower() for token in self.token_pattern.findall(text) if len(token) > 1]
        return Counter(tokens)

    def similarity(self, left: Counter[str], right: Counter[str]) -> float:
        if not left or not right:
            return 0.0
        shared = set(left) & set(right)
        numerator = sum(left[token] * right[token] for token in shared)
        left_norm = math.sqrt(sum(value * value for value in left.values()))
        right_norm = math.sqrt(sum(value * value for value in right.values()))
        if left_norm == 0 or right_norm == 0:
            return 0.0
        return numerator / (left_norm * right_norm)

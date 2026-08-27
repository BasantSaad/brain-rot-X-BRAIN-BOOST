from __future__ import annotations

import math
import re
from collections import Counter


class SimpleEmbeddingModel:
    """A tiny local embedding model used as an offline stand-in for real vector embeddings."""
    
    #It creates a pattern that finds words made only of letters and numbers, ignoring case.
    #This is used to tokenize the input text into individual words for embedding.
    #->  [a-z0-9]+ → one or more characters together ,re.IGNORECASE → also matches uppercase (A–Z)
    token_pattern = re.compile(r"[a-z0-9]+", re.IGNORECASE)

    #simple text embedding using word frequency (bag-of-words)
    '''
    Counter[str] ≈ Counter mapping strings → integers
    each word with its frequency in the text, 
    e.g. "hello world hello" → {"hello": 2, "world": 1}
    '''
    def embed(self, text: str) -> Counter[str]:
        tokens = [token.lower() for token in self.token_pattern.findall(text) if len(token) > 1]
        return Counter(tokens)


    # cosine similarity between two embeddings
    #How similar are these two texts based on shared words and their frequency
    def similarity(self, left: Counter[str], right: Counter[str]) -> float:
        # there no any shared words, or one of the texts is empty, similarity is 0
        if not left or not right:
            return 0.0 #no similarity if either embedding is empty
        
        #Get words that exist in BOTH texts
        shared = set(left) & set(right)

        #Compute dot product of the two vectors (sum of products of shared word frequencies)
        numerator = sum(left[token] * right[token] for token in shared)
        
        #Compute vector length (left or right) = sqrt(sum of squares of word frequencies in left)
        left_norm = math.sqrt(sum(value * value for value in left.values()))
        right_norm = math.sqrt(sum(value * value for value in right.values()))

        '''for example:
        left = {"tiktok": 2, "app": 1}
        right = {"tiktok": 1, "social": 3}
        shared = {"tiktok"}
        numerator = 2*1 = 2
        left_norm = sqrt(2² + 1²) = sqrt(5) ≈ 2.23
        right_norm = sqrt(1² + 3²) = sqrt(10) ≈ 3.16
        similarity = 2 / (2.23 * 3.16) ≈ 0.28
        '''
        if left_norm == 0 or right_norm == 0:
            return 0.0
        return numerator / (left_norm * right_norm)


#NOTTTTTTTTTT USED THAT I TEST AND STATE THE TYPES OF EMBEDDINGS ❓❓❓❓❓❓❓IN THE RETRIEVE FUNCTION IN THE ASSISTANT ENGINE
#___________________________________________________
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------    
#TF-IDF embedding model
import math
from collections import Counter, defaultdict

class TFIDFSimilarity:

    def __init__(self):
        self.idf = defaultdict(float)
        self.docs_count = 0

    def build_idf(self, corpus: list[list[str]]):
        """corpus = list of token lists"""
        self.docs_count = len(corpus)
        df = defaultdict(int)

        for doc in corpus:
            unique_tokens = set(doc)
            for token in unique_tokens:
                df[token] += 1

        for token, freq in df.items():
            self.idf[token] = math.log((self.docs_count + 1) / (freq + 1)) + 1

    def tfidf_vector(self, tokens: list[str]) -> Counter:
        tf = Counter(tokens)
        total = len(tokens)

        return Counter({
            token: (count / total) * self.idf[token]
            for token, count in tf.items()
        })

    def similarity(self, left: Counter, right: Counter) -> float:
        shared = set(left) & set(right)

        numerator = sum(left[t] * right[t] for t in shared)

        left_norm = math.sqrt(sum(v * v for v in left.values()))
        right_norm = math.sqrt(sum(v * v for v in right.values()))

        if left_norm == 0 or right_norm == 0:
            return 0.0

        return numerator / (left_norm * right_norm)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class SentenceEmbeddingSimilarity:

    def __init__(self, model_name="all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(model_name)

    def encode(self, text: str):
        return self.encode_many([text])[0]

    def encode_many(self, texts: list[str]):
        return self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
        ).astype("float32")

    def similarity(self, left: str, right: str) -> float:
        import numpy as np

        vec1 = self.encode(left)
        vec2 = self.encode(right)

        dot = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot / (norm1 * norm2)

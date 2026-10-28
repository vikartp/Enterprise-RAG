"""Dense and Sparse embedding generation."""

from __future__ import annotations

import math
from collections import Counter
from typing import Optional

import numpy as np
from openai import AsyncOpenAI

from app.config import get_settings


class DenseEmbedder:
    """Generate dense embeddings using OpenAI text-embedding-3-small."""

    def __init__(self):
        settings = get_settings()
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        self._model = settings.embedding_model

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts into dense vectors."""
        if not texts:
            return []

        response = await self._client.embeddings.create(
            model=self._model,
            input=texts,
        )
        return [item.embedding for item in response.data]

    async def embed_query(self, query: str) -> list[float]:
        """Embed a single query string."""
        result = await self.embed_texts([query])
        return result[0]


class SparseEmbedder:
    """
    Generate sparse (BM25-style) embeddings for keyword matching.

    Uses a simple token frequency approach compatible with Qdrant's
    sparse vector format. For production, consider SPLADE or learned
    sparse representations.
    """

    def __init__(self, vocab: Optional[dict[str, int]] = None):
        self._vocab = vocab or {}
        self._next_id = max(self._vocab.values(), default=-1) + 1
        self._idf: dict[str, float] = {}
        self._avg_dl: float = 0.0
        self._doc_count: int = 0
        # BM25 parameters
        self._k1 = 1.5
        self._b = 0.75

    def _tokenize(self, text: str) -> list[str]:
        """Simple whitespace + lowercasing tokenizer."""
        import re
        # Basic tokenization: lowercase, split on non-alphanumeric
        tokens = re.findall(r"\b[a-z0-9]+(?:'[a-z]+)?\b", text.lower())
        return tokens

    def fit(self, documents: list[str]) -> None:
        """
        Fit the BM25 model on a corpus of documents.
        Computes IDF values and builds vocabulary.
        """
        self._doc_count = len(documents)
        doc_freq: Counter[str] = Counter()
        total_dl = 0

        for doc in documents:
            tokens = self._tokenize(doc)
            total_dl += len(tokens)
            unique_tokens = set(tokens)
            for token in unique_tokens:
                doc_freq[token] += 1
                if token not in self._vocab:
                    self._vocab[token] = self._next_id
                    self._next_id += 1

        self._avg_dl = total_dl / max(self._doc_count, 1)

        # Compute IDF: log((N - df + 0.5) / (df + 0.5) + 1)
        for token, df in doc_freq.items():
            self._idf[token] = math.log(
                (self._doc_count - df + 0.5) / (df + 0.5) + 1.0
            )

    def encode(self, text: str) -> tuple[list[int], list[float]]:
        """
        Encode text into sparse vector format (indices, values).

        Returns:
            Tuple of (indices, values) for Qdrant SparseVector.
        """
        tokens = self._tokenize(text)
        if not tokens:
            return [], []

        tf: Counter[str] = Counter(tokens)
        doc_len = len(tokens)

        indices: list[int] = []
        values: list[float] = []

        for token, freq in tf.items():
            if token not in self._vocab:
                self._vocab[token] = self._next_id
                self._next_id += 1

            idx = self._vocab[token]
            idf = self._idf.get(token, 1.0)

            # BM25 TF normalization
            tf_norm = (freq * (self._k1 + 1)) / (
                freq + self._k1 * (1 - self._b + self._b * doc_len / max(self._avg_dl, 1))
            )
            score = idf * tf_norm

            if score > 0:
                indices.append(idx)
                values.append(float(score))

        return indices, values

    def encode_batch(self, texts: list[str]) -> list[tuple[list[int], list[float]]]:
        """Encode multiple texts into sparse vectors."""
        return [self.encode(text) for text in texts]


# Module-level singletons (lazily initialized)
_dense_embedder: Optional[DenseEmbedder] = None
_sparse_embedder: Optional[SparseEmbedder] = None


def get_dense_embedder() -> DenseEmbedder:
    """Get or create the dense embedder singleton."""
    global _dense_embedder
    if _dense_embedder is None:
        _dense_embedder = DenseEmbedder()
    return _dense_embedder


def get_sparse_embedder() -> SparseEmbedder:
    """Get or create the sparse embedder singleton."""
    global _sparse_embedder
    if _sparse_embedder is None:
        _sparse_embedder = SparseEmbedder()
    return _sparse_embedder

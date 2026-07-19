import json
import numpy as np
from sentence_transformers import SentenceTransformer

from src.config import CHUNKS_PATH, EMBEDDINGS_PATH, EMBEDDING_MODEL_NAME

class VectorSearcher:

    _model = None
    _chunks = None
    _vectors = None

    def __init__(self):

        if VectorSearcher._chunks is None:
            with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
                VectorSearcher._chunks = json.load(f)

        if VectorSearcher._vectors is None:
            VectorSearcher._vectors = np.load(EMBEDDINGS_PATH)

        if VectorSearcher._model is None:
            VectorSearcher._model = SentenceTransformer(
                EMBEDDING_MODEL_NAME
            )

        self.chunks = VectorSearcher._chunks
        self.vectors = VectorSearcher._vectors

    @property
    def model(self):
        return VectorSearcher._model

    def search(
        self,
        query: str,
        library: str = None,
        limit: int = 5,
    ):
        if not query.strip():
            return []

        query_vector = self.model.encode(
            [query],
            normalize_embeddings=True,
        )[0]

        assert self.vectors.shape[1] == query_vector.shape[0], (
            f"Embedding dimension mismatch. "
            f"Database has {self.vectors.shape[1]}, "
            f"query has {query_vector.shape[0]}."
        )

        scores = self.vectors @ query_vector

        if library:
            mask = np.array(
                [
                    chunk["library"] == library
                    for chunk in self.chunks
                ]
            )
            scores = np.where(mask, scores, -1.0)

        if len(scores) > limit:
            top_indices = np.argpartition(
                -scores,
                limit,
            )[:limit]

            top_indices = top_indices[
                np.argsort(-scores[top_indices])
            ]
        else:
            top_indices = np.argsort(-scores)

        results = []

        for idx in top_indices:

            if scores[idx] < 0:
                continue

            chunk = self.chunks[idx].copy()
            chunk["score"] = float(scores[idx])

            results.append(chunk)

        return results
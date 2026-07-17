import json
import numpy as np
from sentence_transformers import SentenceTransformer

from src.config import CHUNKS_PATH, EMBEDDINGS_PATH, EMBEDDING_MODEL_NAME

class VectorSearcher:
	def __init__(self):
		with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
			self.chunks = json.load(f)
		self.vectors = np.load(EMBEDDINGS_PATH)
		self.model = SentenceTransformer(EMBEDDING_MODEL_NAME)
	
	def search(self, query: str, library: str = None, limit: int = 5):
		q_vector = self.model.encode([query], normalize_embeddings=True)[0]
		scores = self.vectors @ q_vector
		top_indices = np.argsort(-scores)

		results = []
		for i in top_indices:
			chunk = self.chunks[i]
			if library and chunk["library"] != library:
				continue

			chunk_copy = chunk.copy()
			chunk_copy["vector_score"] = float(scores[i])
			results.append(chunk_copy)
			if len(results) >= limit:
				break
		
		return results
		
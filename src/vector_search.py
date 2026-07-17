import json
import numpy as np
from sentence_transformers import SentenceTransformer

from src.config import CHUNKS_PATH, EMBEDDINGS_PATH, EMBEDDING_MODEL_NAME

class VectorSearcher:
	_model = None

	def __init__(self):
		with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
			self.chunks = json.load(f)
		self.vectors = np.load(EMBEDDINGS_PATH)
		if VectorSearcher._model is None:
			VectorSearcher.model = SentenceTransformer(EMBEDDING_MODEL_NAME)
	
	def search(self, query: str, library: str = None, limit: int = 5):
		q_vector = self.model.encode([query], normalize_embeddings=True)[0]
		
		assert self.vectors.shape[1] == q_vector.shape[0], \
            		f"Dimension mismatch! DB expects {self.vectors.shape[1]}, query model returned {q_vector.shape[0]}."
		
		scores = self.vectors @ q_vector

		if library:
			for idx, chunk in enumerate(self.chunks):
				if chunk["library"] != library:
					scores[idx] = -1.0
		if len(scores) > limit:
			top_indices = np.argpartition(-scores, limit)[:limit]
			top_indices = top_indices[np.argsort(-scores[top_indices])]
		else:
			top_indices = np.argsort(-scores)
			    
		results = []
		for i in top_indices:
			score = float(scores[i])
			if score < 0:
				continue
			chunk_copy = self.chunks[i].copy()
			chunk_copy["score"] = score
			results.append(chunk_copy)
					
		return results
	
	@property
	def model(self):
		return VectorSearcher._model
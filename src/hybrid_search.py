from src.keyword_search import KeywordSearcher
from src.vector_search import VectorSearcher

RRF_K = 60

# To reflect Evaluation results, default weights (KW: 10.0, VEC: 1.0) 
class HybridSearcher:
	def __init__(self, kw_weight: float = 10.0, vec_weight: float = 1.0):
		self.vector_searcher = VectorSearcher()
		self.keyword_searcher = KeywordSearcher()
		self.kw_weight = kw_weight
		self.vec_weight = vec_weight
	
	def search(self, query: str, library: str = None, limit: int = 5, kw_weight: float = None, vec_weight: float = None):
		actual_kw_weight = self.kw_weight if kw_weight is None else kw_weight
		actual_vec_weight = self.vec_weight if vec_weight is None else vec_weight
		
		vec_results = self.vector_searcher.search(query, library=library, limit=20)
		kw_results = self.keyword_searcher.search(query, library=library, limit=20)

		rrf_scores = {}
		retrieved_chunks = {}

		for rank, chunk in enumerate(kw_results, start=1):
			chunk_id = chunk["id"]
			rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + (actual_kw_weight / (RRF_K + rank))
			if chunk_id not in retrieved_chunks:
				retrieved_chunks[chunk_id] = chunk.copy()
			retrieved_chunks[chunk_id]["keyword_rank"] = rank

		for rank, chunk in enumerate(vec_results, start=1):
			chunk_id = chunk["id"]
			rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + (actual_vec_weight / (RRF_K + rank))
			if chunk_id not in retrieved_chunks:
				retrieved_chunks[chunk_id] = chunk.copy()
			retrieved_chunks[chunk_id]["vector_rank"] = rank

		ranked_items = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

		final_results = []
		for chunk_id, rrf_score in ranked_items[:limit]:
			result = retrieved_chunks[chunk_id]
			result["rrf_score"] = round(rrf_score, 4)
			final_results.append(result)

		return final_results
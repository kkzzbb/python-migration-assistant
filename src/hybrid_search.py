from src.keyword_search import KeywordSearcher
from src.vector_search import VectorSearcher

class HybridSearcher:
	def __init__(self):
		self.vector_searcher = VectorSearcher()
	
	def search(self, query: str, library: str = None, limit: int = 5):
		vec_results = self.vector_searcher.search(query, library=library, limit=20)

		with KeywordSearcher() as kw_searcher:
			kw_results = kw_searcher.search(query, library=library, limit=20)
		
		scores = {}
		chunk_data = {}

		for rank, chunk in enumerate(kw_results, start=1):
			chunk_id = chunk["id"]
			scores[chunk_id] = scores.get(chunk_id, 0.0) + (1 / (60 + rank))
			if chunk_id not in chunk_data:
				chunk_data[chunk_id] = chunk
		
		ranked_items = sorted(scores.items(), key=lambda x: x[1], reverse=True)

		final_results = []
		for chunk_id, rrf_score in ranked_items[:limit]:
			result = chunk_data[chunk_id].copy()
			result["score"] = round(rrf_score, 4)
			final_results.append(result)

		return final_results
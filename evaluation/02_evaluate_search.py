import pandas as pd
from tqdm.auto import tqdm
from src.hybrid_search import HybridSearcher
from src.keyword_search import KeywordSearcher
from src.vector_search import VectorSearcher
from src.config import GROUND_TRUTH_PATH

def hit_rate(relevance: list[list[int]]) -> float:
	cnt = sum(1 for line in relevance if 1 in line)
	return cnt / len(relevance) if relevance else 0.0

def mrr(relevance: list[list[int]]) -> float:
	total_score = 0.0
	for line in relevance:
		for rank, is_rel in enumerate(line):
			if is_rel == 1:
				total_score += 1 / (rank + 1)
				break
	return total_score / len(relevance) if relevance else 0.0

def evaluate_searcher(searcher, searcher_name: str, ground_truth: list[dict], **search_kwargs) -> tuple[float, float]:
	document_relevance_total = []
	
	for q in tqdm(ground_truth, desc=f"Evaluating {searcher_name}", leave=False):
		exact_chunk_id = str(q["document"])
		target_library = q.get("library")
		exact_file_id = exact_chunk_id.rsplit("-", 1)[0]

		results = searcher.search(
			query=q["question"], 
			library=target_library, 
			limit=5,
			**search_kwargs
		)
		
		doc_rel = [int(str(d["id"]).rsplit("-", 1)[0] == exact_file_id) for d in results]
		document_relevance_total.append(doc_rel)
	hr = hit_rate(document_relevance_total)
	mrr_score = mrr(document_relevance_total)

	print(f"\n--- {searcher_name.upper()} ---")
	print(f"Hit Rate @ 5: {hr:.4f}")
	print(f"MRR @ 5:      {mrr_score:.4f}")
		
	return hr, mrr_score
            
def run_diagnostics():
	print(f"Loading ground truth from {GROUND_TRUTH_PATH}...")
	df_ground_truth = pd.read_csv(GROUND_TRUTH_PATH)
	ground_truth = df_ground_truth.to_dict(orient="records")
    
	print("\nRunning isolated diagnostics...")
    
	evaluate_searcher(KeywordSearcher(), "Keyword Search Only (BM25)", ground_truth)
	evaluate_searcher(VectorSearcher(), "Vector Search Only", ground_truth)

	print("\n--- TUNING HYBRID SEARCH ---")
	hybrid = HybridSearcher()

	weight_combinations = [
        	(1.0, 1.0), 
        	(2.0, 1.0), 
		(5.0, 1.0), 
		(10.0, 1.0)  
    	]

	for kw_w, vec_w in weight_combinations:
		name = f"Hybrid (KW: {kw_w}, VEC: {vec_w})"
		evaluate_searcher(
			hybrid, 
			name, 
			ground_truth, 
			kw_weight=kw_w, 
			vec_weight=vec_w
		)

if __name__ == "__main__":
	run_diagnostics()
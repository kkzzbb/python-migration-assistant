import pandas as pd
from tqdm.auto import tqdm
from src.hybrid_search import HybridSearcher
from src.keyword_search import KeywordSearcher
from src.vector_search import VectorSearcher
from src.config import GROUND_TRUTH_PATH

def hit_rate(relevance):
    cnt = sum(1 for line in relevance if 1 in line)
    return cnt / len(relevance) if relevance else 0.0

def mrr(relevance):
    total_score = 0.0
    for line in relevance:
        for rank in range(len(line)):
            if line[rank] == 1:
                total_score += 1 / (rank + 1)
                break
    return total_score / len(relevance) if relevance else 0.0

def evaluate_searcher(searcher, searcher_name, ground_truth):
    document_relevance_total = []
    
    for q in ground_truth:
        exact_chunk_id = str(q["document"])
        target_library = q.get("library")
        exact_file_id = exact_chunk_id.rsplit("-", 1)[0]

        results = searcher.search(query=q["question"], library=target_library, limit=5)
        doc_rel = [int(str(d["id"]).rsplit("-", 1)[0] == exact_file_id) for d in results]
        document_relevance_total.append(doc_rel)

    print(f"\n--- {searcher_name.upper()} ---")
    print(f"Hit Rate @ 5: {hit_rate(document_relevance_total):.4f}")
    print(f"MRR @ 5:      {mrr(document_relevance_total):.4f}")
          
def run_diagnostics():
    print(f"Loading ground truth from {GROUND_TRUTH_PATH}...")
    df_ground_truth = pd.read_csv(GROUND_TRUTH_PATH)
    ground_truth = df_ground_truth.to_dict(orient="records")
    
    print("Running isolated diagnostics...")
    
    evaluate_searcher(KeywordSearcher(), "Keyword Search Only (BM25)", ground_truth)

    evaluate_searcher(VectorSearcher(), "Vector Search Only", ground_truth)

    print("\n--- TUNING HYBRID SEARCH ---")
    hybrid = HybridSearcher()

    weight_combinations = [
        (1.0, 1.0),  # Baseline (Equal)
        (2.0, 1.0),  # Keyword is 2x more important
        (5.0, 1.0),  # Keyword is 5x more important
        (10.0, 1.0)  # Keyword is 10x more important
    ]

    for kw_w, vec_w in weight_combinations:
        document_relevance_total = []
        for q in ground_truth:
            exact_chunk_id = str(q["document"])
            target_library = q.get("library")
            exact_file_id = exact_chunk_id.rsplit("-", 1)[0] 
            
            # Pass the custom weights here!
            results = hybrid.search(
                query=q["question"], 
                library=target_library, 
                limit=5,
                kw_weight=kw_w,
                vec_weight=vec_w
            )
            
            doc_rel = [int(str(d["id"]).rsplit("-", 1)[0] == exact_file_id) for d in results]
            document_relevance_total.append(doc_rel)
            
        print(f"Weights (KW: {kw_w}, VEC: {vec_w}) -> Hit Rate: {hit_rate(document_relevance_total):.4f} | MRR: {mrr(document_relevance_total):.4f}")

if __name__ == "__main__":
    run_diagnostics()
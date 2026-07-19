import json
import pandas as pd
from tqdm.auto import tqdm
from openai import OpenAI
from src.rag import MigrationAssistant
from src.config import CHUNKS_PATH, GROUND_TRUTH_PATH, RAG_ANSWERS_PATH


def evaluate_rag():
	df_ground_truth = pd.read_csv(GROUND_TRUTH_PATH)
	ground_truth = df_ground_truth.to_dict(orient="records")
      
	with open(CHUNKS_PATH, "r") as f:
		chunks = {c["id"]: c for c in json.load(f)}
		
	assistant = MigrationAssistant()
	client = OpenAI()
	results = []

	print("Generating RAG and Baseline answers...")
	for q in tqdm(ground_truth):
		doc_id = q["document"]
		original_chunk = chunks.get(doc_id, {})
	
		rag_response = assistant.answer_question(q["question"])
		baseline_response = client.responses.create(
			model="gpt-5.4-mini",
			input=[{"role": "user", "content": q["question"]}]
		)

		results.append({
			"question": q["question"],
			"answer_llm": rag_response["answer"],
			"answer_baseline": baseline_response.output_text,
			"answer_orig": original_chunk.get("content", ""),
			"document": doc_id,
		})
		
	df_results = pd.DataFrame(results)
	df_results.to_csv(RAG_ANSWERS_PATH, index=False)
	print(f"Saved RAG and Baseline responses to {RAG_ANSWERS_PATH}")

if __name__ == "__main__":
	evaluate_rag()
import json
import os
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

	if os.path.exists(RAG_ANSWERS_PATH):
		df_existing = pd.read_csv(RAG_ANSWERS_PATH)
		results = df_existing.to_dict(orient="records")
		processed_questions = {r["question"] for r in results}
	else:
		results = []
		processed_questions = set()

	to_process = [q for q in ground_truth if q["question"] not in processed_questions]
	if not to_process:
		print("All questions already processed!")
		return

	print(f"Resuming evaluation. {len(to_process)} questions remaining...")

	for q in tqdm(to_process):
		doc_id = q["document"]
		original_chunk = chunks.get(doc_id, {})
	
		library_filter = q.get("library") if "library" in q else None
		rag_response = assistant.answer_question(q["question"], library=library_filter)

		try:
			baseline_response = client.responses.create(
				model="gpt-5.4-mini",
				input=[{"role": "user", "content": q["question"]}]
			)
			baseline_text = baseline_response.output_text
		except Exception as e:
			baseline_text = f"Error: {e}"

		results.append({
			"question": q["question"],
			"answer_llm": rag_response["answer"],
			"answer_baseline": baseline_text,
			"answer_orig": original_chunk.get("content", ""),
			"document": doc_id,
		})

		pd.DataFrame(results).to_csv(RAG_ANSWERS_PATH, index=False)
		
	print(f"Saved RAG and Baseline responses to {RAG_ANSWERS_PATH}")

if __name__ == "__main__":
	evaluate_rag()
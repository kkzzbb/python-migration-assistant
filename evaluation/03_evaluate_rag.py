import json
import os
import pandas as pd
from tqdm.auto import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI
from src.rag import MigrationAssistant
from src.config import CHUNKS_PATH, GROUND_TRUTH_PATH, RAG_ANSWERS_PATH

def process_question(q, assistant, client, chunks):
	doc_id = q["document"]
	original_chunk = chunks.get(doc_id, {})

	library_filter = q.get("library") if "library" in q and pd.notna(q.get("library")) else None

	try:
		rag_response = assistant.answer_question(q["question"], library=library_filter)
		answer_llm = rag_response["answer"]
	except Exception as e:
		answer_llm = f"Error: {e}"

	try:
		baseline_response = client.responses.create(
			model="gpt-5.4-mini",
			input=[{"role": "user", "content": q["question"]}]
		)
		baseline_text = baseline_response.output_text
	except Exception as e:
		baseline_text = f"Error: {e}"

	return {
		"question": q["question"],
		"answer_llm": answer_llm,
		"answer_baseline": baseline_text,
		"answer_orig": original_chunk.get("content", ""),
		"document": doc_id,		
	}


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

	print(f"Resuming evaluation with 10 parallel workers. {len(to_process)} questions remaining...")

	new_results = []
	with ThreadPoolExecutor(max_workers=10) as executor:
		futures = [
			executor.submit(process_question, q, assistant, client, chunks)
			for q in to_process
		]
		for future in tqdm(as_completed(futures), total=len(futures)):
			new_results.append(future.result())

	results.extend(new_results)
	pd.DataFrame(results).to_csv(RAG_ANSWERS_PATH, index=False)
	print(f"Successfully saved RAG and Baseline responses to {RAG_ANSWERS_PATH}")

if __name__ == "__main__":
	evaluate_rag()
import json
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel
from concurrent.futures import ThreadPoolExecutor
from src.config import CHUNKS_PATH, EVAL_DIR, GROUND_TRUTH_PATH

class Questions(BaseModel):
	questions: list[str]

data_gen_instructions = """
You emulate a developer migrating their Python code to a new framework version.
Formulate 5 questions this developer might ask based on the provided documentation chunk. 
The chunk should contain the answer to the questions.
If possible, use fewer words from the record.
The output should resemble how developers ask questions on StackOverflow or GitHub.
""".strip()

def generate_ground_truth(chunk, client):
	user_prompt = json.dumps(chunk)
	messages = [
   		{"role": "developer", "content": data_gen_instructions},
        	{"role": "user", "content": user_prompt}
   	]

	response = client.responses.parse(
        	model="gpt-5.4-mini",
        	input=messages,
        	text_format=Questions
    	)

	results = []
	for q in response.output_parsed.questions:
		results.append({
		"question": q,
		"document": chunk["id"],
		"library": chunk.get("library", "")
	})
	
	return results


if __name__ == "__main__":
	load_dotenv()
	client = OpenAI()

	with open(CHUNKS_PATH, "r") as f:
		chunks = json.load(f)

	sample_chunks = chunks[:50]
	ground_truth = []

	print("Generating ground truth questions...")
	for chunk in sample_chunks:
		records = generate_ground_truth(chunk, client)
		ground_truth.extend(records)
	
	df = pd.DataFrame(ground_truth)
	EVAL_DIR.mkdir(parents=True, exist_ok=True)
	df.to_csv(GROUND_TRUTH_PATH, index=False)

	print(f"Generated {len(df)} questions and saved to {GROUND_TRUTH_PATH}")
	
	
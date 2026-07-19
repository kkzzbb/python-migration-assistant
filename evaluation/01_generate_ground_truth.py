import json
import pandas as pd
import random
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel
from typing import Literal
from pydantic import BaseModel
from src.config import CHUNKS_PATH, EVAL_DIR, GROUND_TRUTH_PATH

class Question(BaseModel):
	question: str
	type: Literal["keyword", "symptom"]

class Questions(BaseModel):
	questions: list[Question]

data_gen_instructions = """
You emulate a developer migrating a FastAPI, Pydantic, or SQLAlchemy project.

Generate exactly 5 realistic questions answerable using ONLY the provided documentation.

For each question, assign one type:

- keyword: mentions APIs, decorators, classes, functions, or migration terms.
- symptom: describes a migration problem or unexpected behavior without relying on API names.

Rules:
1. Choose the type naturally; do not force any ratio.
2. Every question must be answerable from this documentation.
3. Use wording different from the documentation.
4. Keep questions short and realistic.
5. Avoid generic questions like:
   - "How do I migrate to Pydantic v2?"
   - "What's new?"
6. if possible use fewer words
7. Do not invent information.
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

	valid_chunks = [c for c in chunks if c.get("word_count", 0) > 40]
	random.seed(42)

	fastapi_chunks = [c for c in valid_chunks if c["library"] == "fastapi"]
	pydantic_chunks = [c for c in valid_chunks if c["library"] == "pydantic"]
	sqlalchemy_chunks = [c for c in valid_chunks if c["library"] == "sqlalchemy"]
	

	sample_chunks = (
		random.sample(fastapi_chunks, 17)
		+ random.sample(pydantic_chunks, 17)
		+ random.sample(sqlalchemy_chunks, 16)
	)
	ground_truth = []

	print("Generating ground truth questions...")
	for chunk in sample_chunks:
		records = generate_ground_truth(chunk, client)
		ground_truth.extend(records)
	
	df = pd.DataFrame(ground_truth)
	EVAL_DIR.mkdir(parents=True, exist_ok=True)
	df.to_csv(GROUND_TRUTH_PATH, index=False)

	print(f"Generated {len(df)} questions and saved to {GROUND_TRUTH_PATH}")
	
	
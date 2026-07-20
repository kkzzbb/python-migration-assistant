import json
import pandas as pd
import random
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel
from src.config import CHUNKS_PATH, EVAL_DIR, GROUND_TRUTH_PATH

class Questions(BaseModel):
	questions: list[str]

data_gen_instructions = """
You emulate a Python developer upgrading an application (FastAPI, Pydantic, or SQLAlchemy) from an older version to a newer one.

Generate exactly 5 realistic, code-focused migration questions that can be answered using ONLY this documentation chunk.

CRITICAL RULES:
1. Questions MUST focus on syntax changes, code refactoring, or upgrading legacy patterns.
2. Whenever possible, phrase the question as a "How do I rewrite this old code to the new version?" scenario.
3. Explicitly mention framework versions if applicable (e.g., Pydantic v1 vs v2, SQLAlchemy 1.x vs 2.0).
4. Avoid purely conceptual or "what is" questions. We only want "how to migrate" questions.
5. Do not invent migration rules outside this chunk.

EXAMPLES:
- BAD: "What changed with type annotations?"
- GOOD: "I'm updating my FastAPI dependencies. How do I use `Annotated` with `Depends()` instead of the old parameter syntax?"
- BAD: "Is Query.add_column() deprecated?"
- GOOD: "I am upgrading to SQLAlchemy 2.0. How do I rewrite `session.query(User).filter(User.id == 1).first()`?"
- BAD: "Does Pydantic v2 support exclude_if?"
- GOOD: "How do I migrate my old Pydantic v1 `@validator('name')` method to the new Pydantic v2 syntax?"
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
	
	
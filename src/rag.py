import time
from openai import OpenAI
from dotenv import load_dotenv
from src.hybrid_search import HybridSearcher
from src.monitoring import save_conversation
from src.config import LLM_MODEL_NAME

load_dotenv()

SYSTEM_PROMPT = """You are an expert Python Migration Assistant.
You help developers upgrade their code for FastAPI, Pydantic, and SQLAlchemy.

RULES:
1. If the retrieved context is insufficient, do not guess. Say "I don't have enough information in the migration guides to answer this."
2. Use the retrieved documentation as the primary source. Do not introduce migration rules that are not supported by the retrieved context.
3. If multiple retrieved documents disagree, mention that explicitly.
4. Always mention which library and version the answer comes from (e.g., "According to Pydantic v2...").
5. If code is supplied, only modify code supported by the retrieved documentation.
6. Do not invent migration rules.
7. If multiple documentation chunks discuss the same topic, combine them into one answer.
8. When explaining migration, ONLY show the final, modernized code. Do NOT output legacy or deprecated code snippets.
"""

MAX_CONTEXT_CHARS = 12000

def calculate_cost(usage):
	if usage:
		input_cost = (usage.input_tokens / 1_000_000) * 0.15
		output_cost = (usage.output_tokens / 1_000_000) * 0.60
		return input_cost + output_cost
	return 0.0

class MigrationAssistant:
	def __init__(self):
		self.searcher = HybridSearcher()
		self.client = OpenAI()
		self.model = LLM_MODEL_NAME

	def answer_question(self, question: str, user_code: str = "", library: str = None):
		start_time = time.time()
		retrieved_chunks = self.searcher.search(question, library=library, limit=5)
		if not retrieved_chunks:
			return {
                		"answer": "I couldn't find any relevant migration guide for this specific question.",
                		"sources": [],
                		"retrieved": 0,
				"conversation_id": None,
                		"response_time": 0.0,
                		"cost": 0.0
            		}
		
		context_text = ""
		for chunk in retrieved_chunks:
			chunk_text = (
				f"Library: {chunk['library']}\n"
               			f"Version: {chunk['version']}\n"
                		f"Heading: {chunk['heading']}\n\n"
                		f"{chunk['content']}\n\n"
            		)
			if len(context_text) + len(chunk_text) > MAX_CONTEXT_CHARS:
				break
			context_text += chunk_text

		user_prompt = f"## Documentation\n{context_text}\n"
		if user_code.strip():
			user_prompt += f"## User Code\n{user_code}\n\n"
		user_prompt += f"## User Question\n{question}"

		messages = [
			{"role": "developer", "content": SYSTEM_PROMPT},
			{"role": "user", "content": user_prompt}
		]

		response = self.client.responses.create(
            		model=self.model,
            		input=messages
       		)
		response_time = time.time() - start_time
		answer = response.output_text
		usage = response.usage
		cost = calculate_cost(usage)
		sources = [
         		{
                		"library": c["library"],
                		"version": c["version"],
                		"heading": c["heading"],
                		"filename": c["filename"],
            		}
           		for c in retrieved_chunks
        	]
		conversation_id = save_conversation(
			question=question,
			answer=answer,
			library=str(library),
			model=self.model,
			usage=usage,
			response_time=response_time,
			cost=cost
		)

		return {
			"answer": answer,
            		"sources": sources,
            		"retrieved": len(retrieved_chunks),
			"conversation_id": conversation_id,
			"response_time": response_time,
			"cost": cost,
			"usage": usage
		}
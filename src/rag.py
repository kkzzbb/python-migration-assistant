from openai import OpenAI
from dotenv import load_dotenv
from src.hybrid_search import HybridSearcher

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
8. When explaining migration, show before/after code whenever possible.
"""

MAX_CONTEXT_CHARS = 12000

class MigrationAssistant:
	def __init__(self):
		self.searcher = HybridSearcher()
		self.client = OpenAI()

	def answer_question(self, question: str, user_code: str = "", library: str = None):
		retrieved_chunks = self.searcher.search(question, library=library, limit=5)
		if not retrieved_chunks:
			return {
                		"answer": "I couldn't find any relevant migration guide for this specific question.",
                		"sources": [],
                		"retrieved": 0
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

		response = self.client.responses.create(
            		model="gpt-5.4-mini",
    			instructions=SYSTEM_PROMPT,
    			input=user_prompt,
            		temperature=0.0
       		)
		answer = response.output_text
		sources = [
         		{
                		"library": c["library"],
                		"version": c["version"],
                		"heading": c["heading"],
                		"filename": c["filename"],
            		}
           		for c in retrieved_chunks
        	]
		return {
			"answer": answer,
            		"sources": sources,
            		"retrieved": len(retrieved_chunks)
		}
import pandas as pd
from tqdm.auto import tqdm
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field
from src.config import RAG_ANSWERS_PATH

class BlendingEvaluation(BaseModel):
	reasoning: str = Field(description="Analysis of the syntax versions used in the answer.")
	contains_legacy_syntax: bool = Field(description="True if the answer recommends legacy or outdated syntax (e.g. Pydantic v1, SQLAlchemy 1.x), False otherwise.")

blending_judge_instructions = """
You are an expert Python framework auditor. 
Determine if the provided answer relies on legacy syntax, blends multiple versions, or hallucinates outdated methods (e.g., using `session.query` for SQLAlchemy 2.0, or `@validator` for Pydantic V2).
""".strip()

blending_judge_prompt = """
Question: {question}
Answer to Evaluate: {answer}
""".strip()

def judge_version_blending():
	load_dotenv()
	client = OpenAI()

	df_answers = pd.read_csv(RAG_ANSWERS_PATH)
	answers = df_answers.to_dict(orient="records")
	evaluations = []

	print("Evaluating Version Blending Defense...")
	for rec in tqdm(answers):
		baseline_prompt = blending_judge_prompt.format(question=rec["question"], answer=rec["answer_baseline"])
		try:
			baseline_res = client.responses.parse(
				model="gpt-5.4-mini",
				input=[
					{"role": "developer", "content": blending_judge_instructions},
					{"role": "user", "content": baseline_prompt}
				],
				text_format=BlendingEvaluation
			).output_parsed
			baseline_has_legacy = baseline_res.contains_legacy_syntax
			baseline_reasoning = baseline_res.reasoning
		except Exception as e:
			baseline_has_legacy = True
			baseline_reasoning = f"Error: {e}"

		rag_prompt = blending_judge_prompt.format(question=rec["question"], answer=rec["answer_llm"])
		try:
			rag_res = client.responses.parse(
				model="gpt-5.4-mini",
				input=[
					{"role": "developer", "content": blending_judge_instructions},
					{"role": "user", "content": rag_prompt}
				],
				text_format=BlendingEvaluation
			).output_parsed
			rag_has_legacy = rag_res.contains_legacy_syntax
			rag_reasoning = rag_res.reasoning
		except Exception as e:
			rag_has_legacy = True
			rag_reasoning = f"Error: {e}"

		evaluations.append({
			"question": rec["question"],
			"baseline_has_legacy_syntax": baseline_has_legacy,
			"baseline_reasoning": baseline_reasoning,
			"rag_has_legacy_syntax": rag_has_legacy,
			"rag_reasoning": rag_reasoning
		})

	df_eval = pd.DataFrame(evaluations)

	print("\n--- VERSION CONTAMINATION METRICS ---")
	baseline_contamination = df_eval['baseline_has_legacy_syntax'].mean() * 100
	rag_contamination = df_eval['rag_has_legacy_syntax'].mean() * 100

	print(f"Baseline Contamination Rate: {baseline_contamination:.1f}%")
	print(f"RAG Contamination Rate:      {rag_contamination:.1f}%")

if __name__ == "__main__":
	judge_version_blending()
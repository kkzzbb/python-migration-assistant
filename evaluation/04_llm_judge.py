import pandas as pd
from tqdm.auto import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field
from src.config import RAG_ANSWERS_PATH

class BlendingEvaluation(BaseModel):
	reasoning: str = Field(description="Analysis of the syntax versions used in the answer.")
	contains_legacy_syntax: bool = Field(description="True if the answer recommends legacy or outdated syntax (e.g. Pydantic v1, SQLAlchemy 1.x), False otherwise.")

blending_judge_instructions = """
You are an expert Python framework auditor evaluating an AI assistant's response to a developer's migration question.

Determine if the RECOMMENDED solution in the answer relies on legacy or outdated syntax.

CRITICAL RULES:
1. "Before / After" code comparisons are ALLOWED and expected. If legacy syntax appears in a section clearly labeled "Before", "Old", or "v1/1.x", but the final RECOMMENDED solution uses modern syntax, mark `contains_legacy_syntax = False`.
2. Mark `contains_legacy_syntax = True` ONLY if the actual proposed solution recommends outdated methods (e.g. recommending `@validator` for Pydantic v2, or `session.query()` as the primary answer for SQLAlchemy 2.0).
""".strip()

blending_judge_prompt = """
Question: {question}
Answer to Evaluate: {answer}
""".strip()

def evaluate_single_answer(client, prompt_text):
	try:
		res = client.responses.parse(
            		model="gpt-5.4-mini",
			input=[
				{"role": "developer", "content": blending_judge_instructions},
				{"role": "user", "content": prompt_text}
			],
			text_format=BlendingEvaluation
        	).output_parsed
		return res.contains_legacy_syntax, res.reasoning
	except Exception as e:
        	return True, f"Error: {e}"

def process_record(rec, client):
	baseline_prompt = blending_judge_prompt.format(question=rec["question"], answer=rec["answer_baseline"])
	baseline_has_legacy, baseline_reasoning = evaluate_single_answer(client, baseline_prompt)

	rag_prompt = blending_judge_prompt.format(question=rec["question"], answer=rec["answer_llm"])
	rag_has_legacy, rag_reasoning = evaluate_single_answer(client, rag_prompt)

	return {
		"question": rec["question"],
        	"baseline_has_legacy_syntax": baseline_has_legacy,
        	"baseline_reasoning": baseline_reasoning,
       		"rag_has_legacy_syntax": rag_has_legacy,
        	"rag_reasoning": rag_reasoning
	}

def judge_version_blending():
	load_dotenv()
	client = OpenAI()

	df_answers = pd.read_csv(RAG_ANSWERS_PATH)
	answers = df_answers.to_dict(orient="records")
	evaluations = []

	print("Evaluating Version Compliance (Baseline vs RAG) using 10 parallel threads...")
	with ThreadPoolExecutor(max_workers=10) as executor:
		futures = [executor.submit(process_record, rec, client) for rec in answers]
		for future in tqdm(as_completed(futures), total=len(answers)):
			evaluations.append(future.result())
	
	df_eval = pd.DataFrame(evaluations)
	df_eval.to_csv("data/evaluation/version_blending_evaluations.csv", index=False)
	
	print("\n--- VERSION COMPLIANCE METRICS ---")
    
	baseline_legacy_rate = df_eval['baseline_has_legacy_syntax'].mean() * 100
	rag_legacy_rate = df_eval['rag_has_legacy_syntax'].mean() * 100

	baseline_compliance = 100 - baseline_legacy_rate
	rag_compliance = 100 - rag_legacy_rate

	print(f"Baseline (No RAG)  --> Modern Compliance: {baseline_compliance:.1f}% | Outdated Syntax Rate: {baseline_legacy_rate:.1f}%")
	print(f"RAG-Assisted       --> Modern Compliance: {rag_compliance:.1f}% | Outdated Syntax Rate: {rag_legacy_rate:.1f}%")
	print(f"\nConclusion: RAG improved modern syntax compliance by +{(rag_compliance - baseline_compliance):.1f}%!")

if __name__ == "__main__":
	judge_version_blending()

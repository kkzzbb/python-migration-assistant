import pandas as pd
from tqdm.auto import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field
from src.config import RAG_ANSWERS_PATH

class VersionComplianceEvaluation(BaseModel):
	reasoning: str = Field(
        	description="Analysis of whether the recommended migration consistently uses the target framework version."
    	)
	contains_legacy_syntax: bool = Field(
        	description="True if the recommended solution relies on deprecated APIs."
    	)
	contains_version_blending: bool = Field(
        	description="True if the recommended solution mixes APIs from different major framework versions."
    	)

blending_judge_instructions = """
You are an expert Python framework auditor evaluating an AI assistant's response to a migration question.

Determine whether the RECOMMENDED solution consistently follows the requested target framework version.
CRITICAL RULES:
1. Ignore "Before", "Old", "v1", or "1.x" examples. They are expected.
2. Evaluate ONLY the final recommended migration.
3. contains_legacy_syntax = True if the recommendation uses deprecated APIs as the solution.
4. contains_version_blending = True if the recommendation mixes APIs from different major versions in the final solution.
Examples:
Pydantic:
- @validator + model_config
- @validator + field_validator
- Config + ConfigDict
SQLAlchemy:
- session.query() together with select()
- Query.filter() together with Session.execute(select())
FastAPI:
- old Depends() parameter style mixed with Annotated dependency injection
5. If the recommendation consistently uses the target version, both fields should be False.
""".strip()

version_judge_prompt = """
Question: {question}
Answer to Evaluate: {answer}
""".strip()

def evaluate_single_answer(client: OpenAI, prompt_text: str):
	try:
		res = client.responses.parse(
            		model="gpt-5.4-mini",
			input=[
				{"role": "developer", "content": blending_judge_instructions},
				{"role": "user", "content": prompt_text}
			],
			text_format=VersionComplianceEvaluation
        	).output_parsed
		return (
			res.contains_legacy_syntax,
			res.contains_version_blending,
			res.reasoning,
		)
	except Exception as e:
        	return (
			True,
			True,
			f"Error during evaluation: {e}",
		)

def process_record(record, client):
	baseline_prompt = version_judge_prompt.format(
		question=record["question"],
		answer=record["answer_baseline"],
	)
	(
		baseline_legacy,
		baseline_blending,
		baseline_reasoning,
	) = evaluate_single_answer(client, baseline_prompt)

	rag_prompt = version_judge_prompt.format(
		question=record["question"],
		answer=record["answer_llm"],
	)
	(
		rag_legacy,
		rag_blending,
		rag_reasoning,
	) = evaluate_single_answer(client, rag_prompt)

	return {
		"question": record["question"],
        	"baseline_contains_legacy_syntax": baseline_legacy,
		"baseline_contains_version_blending": baseline_blending,
		"baseline_reasoning": baseline_reasoning,

		"rag_contains_legacy_syntax": rag_legacy,
		"rag_contains_version_blending": rag_blending,
		"rag_reasoning": rag_reasoning,
	}

def judge_version_compliance():
	load_dotenv()
	client = OpenAI()

	df_answers = pd.read_csv(RAG_ANSWERS_PATH)
	answers = df_answers.to_dict(orient="records")
	evaluations = []

	print("Evaluating answers using 10 parallel workers...")
	with ThreadPoolExecutor(max_workers=10) as executor:
		futures = [
			executor.submit(process_record, record, client)
			for record in answers
		]
		for future in tqdm(as_completed(futures), total=len(futures)):
			evaluations.append(future.result())

	df_eval = pd.DataFrame(evaluations)
	output_path = "data/evaluation/version_compliance_evaluations.csv"
	df_eval.to_csv(output_path, index=False)

	print(f"\nSaved evaluation to {output_path}")

	baseline_legacy_rate = df_eval["baseline_contains_legacy_syntax"].mean() * 100
	rag_legacy_rate = df_eval["rag_contains_legacy_syntax"].mean() * 100
	baseline_blending_rate = df_eval["baseline_contains_version_blending"].mean() * 100
	rag_blending_rate = df_eval["rag_contains_version_blending"].mean() * 100


	print("\n--- VERSION COMPLIANCE METRICS ---")

	print(f"Outdated Syntax Rate | Baseline: {baseline_legacy_rate:.1f}% | RAG: {rag_legacy_rate:.1f}%")
	print(f"Version Blending Rate | Baseline: {baseline_blending_rate:.1f}% | RAG: {rag_blending_rate:.1f}%")
	print(f"Reduction in outdated syntax: {baseline_legacy_rate - rag_legacy_rate:.1f}%")
	print(f"Reduction in version blending: {baseline_blending_rate - rag_blending_rate:.1f}%")
		
if __name__ == "__main__":
	judge_version_compliance()

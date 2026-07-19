from src.config import RAG_ANSWERS_PATH, RAG_EVALUATIONS_PATH


def judge_answers():

	df_answers = pd.read_csv(RAG_ANSWERS_PATH)

	df_eval = pd.DataFrame(evaluations)
   	df_eval.to_csv(RAG_EVALUATIONS_PATH, index=False)
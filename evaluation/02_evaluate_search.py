from src.config import GROUND_TRUTH_PATH




def evaluate_search():
    df_ground_truth = pd.read_csv(GROUND_TRUTH_PATH)
from pathlib import Path

DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
INDEX_DIR = DATA_DIR / "indexes"

CHUNKS_PATH = PROCESSED_DIR / "chunks.json"
EMBEDDINGS_PATH = PROCESSED_DIR / "embeddings.npy"
EMBEDDINGS_META_PATH = PROCESSED_DIR / "embedding_metadata.json"
KEYWORD_DB_PATH = INDEX_DIR / "keyword.db"

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

EVAL_DIR = DATA_DIR / "evaluation"
GROUND_TRUTH_PATH = EVAL_DIR / "ground_truth.csv"
RAG_ANSWERS_PATH = EVAL_DIR / "rag_answers.csv"
RAG_EVALUATIONS_PATH = EVAL_DIR / "rag_evaluations.csv"

LLM_MODEL_NAME = "gpt-5.4-mini"
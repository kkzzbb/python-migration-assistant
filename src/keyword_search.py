import json
import sqlite3

from src.config import CHUNKS_PATH, KEYWORD_DB_PATH

def build_keyword_database():
	KEYWORD_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
	if KEYWORD_DB_PATH.exists():
		KEYWORD_DB_PATH.unlink()
	
	con = sqlite3.connect(KEYWORD_DB_PATH)

	con.execute("""
	     CREATE VIRTUAL TABLE chunks USING fts5(
	     	id UNINDEXED, library UNINDEXED, version UNINDEXED, filename UNINDEXED,
	     	heading, content
	     )
	""")

	if not CHUNKS_PATH.exists():
		raise FileNotFoundError(f"{CHUNKS_PATH} not found.")
	with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
		chunks = json.load(f)
	con.executemany(
		"""INSERT INTO chunks (id, library, version, filename, heading, content)
		VALUES (:id, :library, :version, :filename, :heading, :content)""",
		chunks
	)
	con.commit()
	con.close()

	print(f"Built exact-match database with {len(chunks)} chunks!")
	print(f"Saved to {KEYWORD_DB_PATH}")

class KeywordSearcher:
	def __init__(self):
		self.con = sqlite3.connect(KEYWORD_DB_PATH)
		self.con.row_factory = sqlite3.Row

	def search(self, query:str, library: str=None, limit: int =5):
		words = query.split()
		if not words:
			return []
		
		fts_query = " OR ".join(f'"{w}' for w in words)
		sql = """SELECT id, library, version, filename, heading, content, bm25(chunks) AS score
			FROM chunks WHERE chunks MATCH ?"""
		params = [fts_query]

		if library:
			sql += " AND library = ?"
			params.append(library)
		sql += " ORDER BY score ASC LIMIT ?"
		params.append(limit)

		return [dict(r) for r in self.con.execute(sql, params).fetchall()]
	
if __name__ == "__main__":
	build_keyword_database()

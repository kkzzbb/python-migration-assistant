import sqlite3
import time
from datetime import datetime
from dataclasses import dataclass
from src.config import DATA_DIR

MONITOR_DB_PATH = DATA_DIR / "processed" / "monitoring.db"

@dataclass
class Stats:
	total: int
	avg_response_time: float
	total_cost: float
	avg_tokens: float

def get_db_connection():
	MONITOR_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
	conn = sqlite3.connect(MONITOR_DB_PATH, check_same_thread=False)
	# Return rows as dictionaries for easy parsing
	conn.row_factory = sqlite3.Row 
	return conn

def init_monitoring_db():
	conn = get_db_connection()
	conn.execute("""
		CREATE TABLE IF NOT EXISTS conversations (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		question TEXT,
		answer TEXT,
		library TEXT,
		model TEXT,
		prompt_tokens INTEGER,
		completion_tokens INTEGER,
		total_tokens INTEGER,
		response_time REAL,
		cost REAL,
		timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
		)
	""")
	conn.execute("""
		CREATE TABLE IF NOT EXISTS feedback (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		conversation_id INTEGER,
		score INTEGER,
		timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
		)
	""")
	conn.commit()
	conn.close()

def save_conversation(question: str, answer: str, library: str, model: str, usage, response_time: float, cost: float) -> int:
	conn = get_db_connection()
	cursor = conn.cursor()
	cursor.execute("""
		INSERT INTO conversations (
		question, answer, library, model, prompt_tokens, completion_tokens, total_tokens, response_time, cost
		) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
	""", (
		question, answer, library, model, 
		usage.prompt_tokens if usage else 0, 
		usage.completion_tokens if usage else 0, 
		usage.total_tokens if usage else 0, 
		response_time, cost
	))
	conversation_id = cursor.lastrowid
	conn.commit()
	conn.close()
	return conversation_id

def save_feedback(conversation_id: int, score: int):
	conn = get_db_connection()
	conn.execute(
		"INSERT INTO feedback (conversation_id, score) VALUES (?, ?)",
		(conversation_id, score)
	)
	conn.commit()
	conn.close()

def get_stats() -> Stats:
	conn = get_db_connection()
	row = conn.execute("""
		SELECT 
		COUNT(*) as total, 
		AVG(response_time) as avg_response_time, 
		SUM(cost) as total_cost, 
		AVG(total_tokens) as avg_tokens 
		FROM conversations
	""").fetchone()
	conn.close()
    
	return Stats(
		total=row["total"] or 0,
		avg_response_time=row["avg_response_time"] or 0.0,
		total_cost=row["total_cost"] or 0.0,
		avg_tokens=row["avg_tokens"] or 0.0
	)

def get_recent_conversations(limit=20):
	conn = get_db_connection()
	rows = conn.execute("""
		SELECT * FROM conversations 
		ORDER BY timestamp DESC 
		LIMIT ?
	""", (limit,)).fetchall()
	conn.close()
	return [dict(row) for row in rows]
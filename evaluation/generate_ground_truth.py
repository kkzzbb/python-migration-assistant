import json
from pathlib import Path

GROUND_TRUTH_DATA = [
	{
       		"query": "How do I migrate my old @validator and the inner Config class to Pydantic v2?",
        	"library": "pydantic",
        	"target_version": "v2",
		"forbidden_tokens": ["class Config:", "@validator"],
		"required_tokens": ["model_validator", "field_validator", "model_config"]
   	},
	{
		"query": "How do I upgrade session.query to the new SQLAlchemy 2.0 select syntax?",
		"library": "sqlalchemy",
		"target_version": "v2.0",
		"forbidden_tokens": ["db.query(", "session.query("],
		"required_tokens": ["select(", "db.execute("]
   	},
	{
		"query": "How do I declare route dependencies in FastAPI using modern Type annotations instead of inline Depends?",
		"library": "fastapi",
		"target_version": "latest",
		"forbidden_tokens": ["db: Session = Depends("],
		"required_tokens": ["Annotated[", "Depends("]
	}
]

def generate_set():
	output_path = Path("evaluation/labeled_qa.json")
	output_path.parent.mkdir(parents=True, exist_ok=True)

	with open(output_path, "w", encoding="utf-8") as f:
		json.dump(GROUND_TRUTH_DATA, f, indent=4)
	
	print(f"Generated test set with {len(GROUND_TRUTH_DATA)} specialized contamination test cases.")

if __name__ == "__main__":
	generate_set()
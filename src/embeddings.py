import json
import numpy as np
from sentence_transformers import SentenceTransformer

from src.config import (
    CHUNKS_PATH, 
    EMBEDDINGS_PATH, 
    EMBEDDINGS_META_PATH, 
    EMBEDDING_MODEL_NAME
)

def create_embeddings():
	if not CHUNKS_PATH.exists():
		raise FileNotFoundError(
			f"{CHUNKS_PATH} not found." 
		)
	with open(CHUNKS_PATH, 'r', encoding='utf-8') as f:
		chunks = json.load(f)

	texts_to_embed = []
	for chunk in chunks:
		text = (
           		f"Library: {chunk['library']}\n"
            		f"File: {chunk['filename']}\n"
            		f"Heading: {chunk['heading']}\n\n"
            		f"{chunk['content']}"
       		)
		texts_to_embed.append(text)
	
	print("Loaded {len(chunks)} chunks.")
	print(f"Embedding model: {EMBEDDING_MODEL_NAME}")

	model = SentenceTransformer(EMBEDDING_MODEL_NAME)

	print("Generating vectors...")
	vectors = model.encode(
       		texts_to_embed,
        	batch_size=64,
        	show_progress_bar=True,
        	normalize_embeddings=True,
        	convert_to_numpy=True,
   	)
	
	assert len(chunks) == vectors.shape[0], f"Mismatch! Chunks: {len(chunks)}, Vectors: {vectors.shape[0]}"
	np.save(EMBEDDINGS_PATH, vectors)

	metadata = {
        	"model": EMBEDDING_MODEL_NAME,
        	"dimensions": vectors.shape[1],
        	"num_chunks": len(chunks)
    	}
	with open(EMBEDDINGS_META_PATH, "w", encoding="utf-8") as f:
		json.dump(metadata, f, indent=2)
	
	print(f"Embedding dimension: {vectors.shape[1]}")
	print(f"Saved vectors: {EMBEDDINGS_PATH}")
	print(f"Saved metadata: {EMBEDDINGS_META_PATH}")
	
if __name__ == "__main__":
	create_embeddings()
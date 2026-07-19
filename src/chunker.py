import os
import re
import json
from pathlib import Path

from src.config import RAW_DIR, PROCESSED_DIR, CHUNKS_PATH

IGNORE_DIRS = {"images", "assets", "media", "static", ".github"}
IGNORE_FILES = {"readme", "license", "changelog", "contributing", "authors"}

def clean_markdown_noise(text: str) -> str:
	text = re.sub(r'<[^>]+>', '', text)
	noisy_terms = ["dependabot", "bump dependency", "typo", "ci update", "pre-commit", "merge pull request"]

	cleaned_lines = []
	for line in text.split('\n'):
		if not any(noise in line.lower() for noise in noisy_terms):
			cleaned_lines.append(line)

	return "\n".join(cleaned_lines)

def chunk_section(section_text, max_words=300, overlap_words=50):
	paragraphs = section_text.split('\n\n')
	chunks = []
	current_chunk = []
	current_length = 0

	for p in paragraphs:
		p_len = len(p.split())
		if current_length + p_len > max_words and current_chunk:
			chunks.append("\n\n".join(current_chunk))
			overlap_length = 0
			overlap_chunk = []
			
			for op in reversed(current_chunk):
				op_len = len(op.split())
				if overlap_length + op_len > overlap_words:
					break
				overlap_chunk.insert(0, op)
				overlap_length += op_len
			
			current_chunk = overlap_chunk
			current_length = overlap_length
		current_chunk.append(p)
		current_length += p_len
	if current_chunk:
		chunks.append("\n\n".join(current_chunk))
	return chunks

def process_all_files():
	base_dir = RAW_DIR
	all_chunks = []
	chunk_counter = 1

	for root, dirs, files in os.walk(base_dir):
		dirs[:] = [d for d in dirs if d.lower() not in IGNORE_DIRS]
		for file in files:
			if not file.endswith((".md", ".rst")):
				continue
			
			file_path = Path(root) / file
			if file_path.stem.lower() in IGNORE_FILES:
				continue
			
			rel_path = file_path.relative_to(base_dir)
			library = rel_path.parts[0]
			version = rel_path.parts[1]
			
			with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
				text = f.read()

			text = clean_markdown_noise(text)
			raw_sections = re.split(r'\n(?=#{1,3}\s)', text)

			for section in raw_sections:
				section = section.strip()
				if len(section) < 30:
					continue
				lines = section.split('\n')
				heading = lines[0].strip('# ').strip() if lines[0].startswith('#') else file_path.stem

				sub_chunks = chunk_section(section, max_words=450, overlap_words=80)	
				for sub_chunk in sub_chunks:
					word_count = len(sub_chunk.split())
					if word_count < 10:
						continue
					chunk_dict = {
                        			"id": f"{library}-{version}-{file_path.stem}-{chunk_counter:04d}",
                       		 		"library": library,
                      				"version": version,
                       				"filename": file_path.stem,
                        			"filepath": str(rel_path),
                       				"heading": heading,
                        			"content": sub_chunk,
                        			"word_count": word_count
                    			}
					all_chunks.append(chunk_dict)
					chunk_counter += 1
	PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

	with open(CHUNKS_PATH, "w", encoding="utf-8") as f:
		json.dump(all_chunks, f, indent=2)
	print(f"Processed {len(all_chunks)} chunks.")
	print(f"Saved to {CHUNKS_PATH}")

if __name__ == "__main__":
	process_all_files()
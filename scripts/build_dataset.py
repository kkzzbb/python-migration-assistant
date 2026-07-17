import subprocess
import sys

def run_script(script_path):
	print(f"\nRunning {script_path}...")
	subprocess.run([sys.executable, script_path], check=True)

def run_module(module_name):
	print(f"\nRunning module {module_name}")
	subprocess.run([sys.executable, "-m", module_name], check=True)

def main():
	print("Starting the automated ingestion pipeline...")
	
	run_script("scripts/download_docs.py")
	run_module("src.chunker")
	run_module("src.embeddings")
	run_module("src.keyword_search")
	
	print("\nDataset completely built! The RAG system is ready to use.")

if __name__ == "__main__":
	main()
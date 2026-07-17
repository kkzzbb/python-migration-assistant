import subprocess

def run_script(script_path):
	print(f"\nRunning {script_path}...")
	subprocess.run(["python", script_path], check=True)

def main():
	print("Starting the automated ingestion pipeline...")
	
	run_script("scripts/download_docs.py")
	run_script("src/chunker.py")
	run_script("src/embedder.py")
	
	print("\nDataset completely built! The RAG system is ready to use.")

if __name__ == "__main__":
	main()
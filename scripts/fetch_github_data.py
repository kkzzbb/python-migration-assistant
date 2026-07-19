import os
import requests
from pathlib import Path

REPOS = {
    "fastapi": "tiangolo/fastapi",
    "pydantic": "pydantic/pydantic",
    "sqlalchemy": "sqlalchemy/sqlalchemy"
}

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

def fetch_recent_releases(limit_per_repo=15):
	headers = {"Accept": "application/vnd.github.v3+json"}
	if GITHUB_TOKEN:
		headers["Authorization"] = f"token {GITHUB_TOKEN}"
	
	for library, repo in REPOS.items():
		print(f"Fetching recent releases for {library}...")

		url = f"https://api.github.com/repos/{repo}/releases?per_page={limit_per_repo}"
		response = requests.get(url, headers=headers)

		if response.status_code != 200:
			print(f"Failed to fetch {library}: {response.json().get('message')}")
			continue

		releases = response.json()

		output_dir = Path(f"data/raw/{library}/releases")
		output_dir.mkdir(parents=True, exist_ok=True)
		file_path = output_dir / f"{library}_releases.md"

		with open(file_path, "w", encoding="utf-8") as f:
			f.write(f"# {library.capitalize()} Release Notes\n\n")

			for release in releases:
				tag_name = release.get("tag_name", "Unknown Version")
				date = release.get("published_at", "")[:10]
				body = release.get("body", "No release notes provided.")

				f.write(f"## {library.capitalize()} {tag_name} ({date})\n\n")
				f.write(f"{body}\n\n")
				f.write("---\n\n")
			
			print(f"Saved {len(releases)} releases to {file_path}")

if __name__ == "__main__":
	fetch_recent_releases()
import subprocess
from pathlib import Path

LIBRARIES = {
    "pydantic": [
        {"version": "v1", "branch": "v1.10.13", "docs_folder": "docs"},
        {"version": "v2", "branch": "main", "docs_folder": "docs"},
    ],
    "sqlalchemy": [
        {"version": "v1.4", "branch": "rel_1_4", "docs_folder": "doc/build"},
        {"version": "v2.0", "branch": "main", "docs_folder": "doc/build"},
    ],
    "fastapi": [
        {"version": "latest", "branch": "master", "docs_folder": "docs/en/docs"},
    ]
}

REPO_URLS = {
    "pydantic": "https://github.com/pydantic/pydantic.git",
    "sqlalchemy": "https://github.com/sqlalchemy/sqlalchemy.git",
    "fastapi": "https://github.com/fastapi/fastapi.git",
}

def download_docs():
    base_dir = Path("data/raw")
    base_dir.mkdir(parents=True, exist_ok=True)

    for library, versions in LIBRARIES.items():
        for v in versions:
            target_dir = base_dir / library / v["version"]
            if target_dir.exists():
                print(f"{library} {v['version']} docs already downloaded. Skipping.")
                continue
            print(f"Downloading {library} {v['version']} docs...")
            url = REPO_URLS[library]

            subprocess.run(
                ["git", "clone", "--depth", "1", "--branch", v["branch"], url, str(target_dir)],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print(f"Downloaded {library} {v['version']} docs to {target_dir}")

if __name__ == "__main__":
    download_docs()

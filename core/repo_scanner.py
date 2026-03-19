import tempfile
import os
from git import Repo

# Directories that should NEVER be sent to the AI
IGNORE_DIRS = {".git", "venv", ".venv", "env", "__pycache__", "node_modules", "tests", ".pytest_cache"}

def scan_github_repo(repo_url):
    python_files = {}

    # TemporaryDirectory guarantees cleanup automatically when the block exits
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            print(f"📦 Cloning {repo_url} into temporary secure space...")
            Repo.clone_from(repo_url, temp_dir)

            for root, dirs, files in os.walk(temp_dir):
                # Modify dirs in-place to skip ignored directories
                dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

                for file in files:
                    if file.endswith(".py"):
                        file_path = os.path.join(root, file)
                        
                        try:
                            # Added error='ignore' to prevent crashing on weird encodings
                            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                                content = f.read()
                                # Only keep files that actually have content
                                if content.strip():
                                    python_files[file] = content
                        except Exception as e:
                            print(f"⚠️ Skipping file {file} due to read error: {e}")
                            
        except Exception as e:
            print(f"❌ Failed to clone repository: {e}")
            raise Exception(f"Repository clone failed. Ensure the URL is public and valid. Details: {e}")

    return python_files
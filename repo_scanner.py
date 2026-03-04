import os
import shutil
import tempfile
from git import Repo


def scan_github_repo(repo_url):

    temp_dir = tempfile.mkdtemp()

    try:
        Repo.clone_from(repo_url, temp_dir)

        python_files = []

        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                if file.endswith(".py"):
                    path = os.path.join(root, file)

                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        python_files.append(f.read())

        combined_code = "\n\n".join(python_files)

        return combined_code

    finally:
        shutil.rmtree(temp_dir)
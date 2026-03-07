import tempfile
import os
from git import Repo

def scan_github_repo(repo_url):

    temp_dir = tempfile.mkdtemp()

    Repo.clone_from(repo_url, temp_dir)

    python_files = {}

    for root, dirs, files in os.walk(temp_dir):

        for file in files:

            if file.endswith(".py"):

                file_path = os.path.join(root, file)

                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        python_files[file] = f.read()
                except:
                    pass

    return python_files
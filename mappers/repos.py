import github
import logging
import logging.config
from database import Database
from tqdm import tqdm as progress_bar
from . import folders
from . import files

# Get the logger specified in the file
logger = logging.getLogger("mappers")


def map_repo_files(repo: github.Repository.Repository, base: Database):
    repo_properties = {
        "key": f"repo_{repo.full_name}",
        "name": repo.name
    }

    base.create_node_generic(["Repo"], repo_properties)

    for content in progress_bar(repo.get_contents(""), desc="Mapping repo files"):
        if content.type == "dir":
            folders.process_folder(content, base, repo)
        elif content.type == "file":
            files.process_file(content, base, repo)
        else:
            print(f"unkown file type {content.type}")
            raise TypeError(content)

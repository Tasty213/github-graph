import github
import logging
import logging.config
from database import Database
from . import folders
from . import files
from wrapper import rate_handler

# Get the logger specified in the file
logger = logging.getLogger("mappers")


def map_repo_files(repo: github.Repository.Repository, base: Database):
    properties = {
        "key": f"repo_{repo.full_name}",
        "name": repo.name
    }
    logger.info(f"processing repo {properties['name']}")
    base.create_node_generic(["Repo"], properties)

    for content in rate_handler(repo.get_contents, ""):
        if content.type == "dir":
            folders.process_folder(content, base, repo)
        elif content.type == "file":
            files.process_file(content, base, repo)
        else:
            print(f"unkown file type {content.type}")
            raise TypeError(content)

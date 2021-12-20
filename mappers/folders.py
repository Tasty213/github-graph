import github
import logging
import logging.config
from time import sleep
from database import Database
from tqdm import tqdm as progress_bar
import re as regex
from . import files
# Get the logger specified in the file
logger = logging.getLogger(__name__)


def process_folder(folder: github.ContentFile.ContentFile, base: Database, repo: github.Repository.Repository, parent_key: str):
    sleep(0.1)
    folder_properties = {
        "name": folder.name,
        "url": folder.html_url,
        "sha": folder.sha,
        "key": f"folder_{folder.path}"
    }

    base.create_node_generic(["Folder"], folder_properties)

    base.create_relationship(parent_key, folder_properties["key"], "CONTAINS")

    folder_contents = repo.get_contents(folder.path)
    for content in progress_bar(folder_contents, desc=f"{folder_properties['name']}", leave=False):
        if content.type == "dir":
            process_folder(content, base, repo, folder_properties["key"])
        elif content.type == "file":
            files.process_file(content, base, repo)
        elif content.type == "symlink":
            pass
        else:
            logging.critical(f"unkown file type {folder.type}")
            raise TypeError(content)


def process_deleted_folder(path: str, base: Database, repo: github.Repository.Repository):
    if "/" in path:
        parent_folder = regex.search('.*(?=\/.*$)', path).group(0)
        parent_key = f"folder_{parent_folder}"
    else:
        parent_key = f"repo_{repo.full_name}"
    folder_properties = {
        "name": path.split("/")[-1],
        "key": f"folder_{path}"
    }
    base.create_node_generic(
        ["Folder", "Deleted"], folder_properties)

    if not base.check_node_exists(parent_key):
        process_deleted_folder(parent_folder, base, repo)

    base.create_relationship(
        parent_key, folder_properties["key"], "CONTAINS", {})

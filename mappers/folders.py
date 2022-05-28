import github
import logging
import logging.config
from time import sleep
from database import Database
import re as regex
from . import files
from typing import Union
from wrapper import rate_handler

# Get the logger specified in the file
logger = logging.getLogger("mappers")


def process_folder(folder: Union[github.ContentFile.ContentFile, str], base: Database, repo: github.Repository.Repository, deleted=False):
    if deleted:
        _process_deleted_folder(folder, base, repo)
    else:
        if "/" in folder.path:
            parent_folder = regex.search('.*(?=\/.*$)', folder.path).group(0)
            parent_key = f"folder_{parent_folder}"
        else:
            parent_key = f"repo_{repo.full_name}"
        folder_properties = {
            "name": folder.name,
            "url": folder.html_url,
            "sha": folder.sha,
            "key": f"folder_{folder.path}"
        }

        base.create_node_generic(["Folder"], folder_properties)

        base.create_relationship(
            parent_key, folder_properties["key"], "CHILD")

        folder_contents = rate_handler(repo.get_contents, folder.path)
        for content in folder_contents:
            if content.type == "dir":
                process_folder(content, base, repo)
            elif content.type == "file":
                files.process_file(content, base, repo)
            elif content.type == "symlink":
                pass
            else:
                logging.critical(f"unkown file type {folder.type}")
                raise TypeError(content)


def _process_deleted_folder(path: str, base: Database, repo: github.Repository.Repository):
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
        _process_deleted_folder(parent_folder, base, repo)

    base.create_relationship(
        parent_key, folder_properties["key"], "CHILD", {})

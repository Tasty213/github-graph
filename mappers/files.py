import github
import logging
import logging.config
from database import Database
import re as regex
from . import folders
from typing import Union

# Get the logger specified in the file
logger = logging.getLogger("mappers")

files_to_complete = []


def process_file(file: Union[github.ContentFile.ContentFile, github.File.File], base: Database,
                 repo: github.Repository.Repository, deleted: bool = False, update_placeholder: bool = False):
    if deleted:
        _process_deleted_file(file, base, repo)
    elif update_placeholder:
        _update_placeholder_file_node(file, base, repo)
    else:
        if "/" in file.path:
            parent_folder = regex.search('.*(?=\/.*$)', file.path).group(0)
            parent_key = f"folder_{parent_folder}"
        else:
            parent_key = f"repo_{repo.full_name}"
        file_properties = {
            "name": file.name,
            "url": file.html_url,
            "sha": file.sha,
            "size": file.size,
            "key": f"file_{file.path}"
        }
        base.create_node_generic(["File"], file_properties)
        base.create_relationship(
            parent_key, file_properties["key"], "CHILD")


def _process_deleted_file(file: github.File.File, base: Database, repo: github.Repository.Repository):
    if "/" in file.filename:
        parent_folder = regex.search('.*(?=\/.*$)', file.filename).group(0)
        parent_key = f"folder_{parent_folder}"
    else:
        parent_key = f"repo_{repo.full_name}"
    file_properties = {
        "name": file.filename.split("/")[-1],
        "url": file.raw_url,
        "sha": file.sha,
        "key": f"file_{file.filename}"
    }
    base.create_node_generic(["File", "Deleted"], file_properties)

    if not base.check_node_exists(parent_key):
        folders.process_folder(parent_folder, base, repo, deleted=True)

    base.create_relationship(
        parent_key, file_properties["key"], "CHILD", {})


def _update_placeholder_file_node(file: github.File.File, base: Database, repo: github.Repository.Repository):
    if "/" in file.filename:
        parent_folder = regex.search('.*(?=\/.*$)', file.filename).group(0)
        parent_key = f"folder_{parent_folder}"
    else:
        parent_key = f"repo_{repo.full_name}"
    file_properties = {
        "name": file.filename.split("/")[-1],
        "url": file.raw_url,
        "sha": file.sha,
        "key": f"file_{file.filename}"
    }
    base.update_node(["File", "Deleted"], file_properties)
    base.create_relationship(
        parent_key, file_properties["key"], "CHILD", {})

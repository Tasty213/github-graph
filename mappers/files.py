import github
import logging
import logging.config
from database import Database
import re as regex
from . import folders
# Get the logger specified in the file
logger = logging.getLogger(__name__)

files_to_complete = []


def process_file(file: github.ContentFile.ContentFile, base: Database, parent_key: str):
    file_properties = {
        "name": file.name,
        "url": file.html_url,
        "sha": file.sha,
        "size": file.size,
        "key": f"file_{file.path}"
    }
    base.create_node_generic(["File"], file_properties)
    base.create_relationship(
        parent_key, file_properties["key"], "CONTAINS")


def process_deleted_file(file: github.File.File, base: Database, repo: github.Repository.Repository):
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
        folders.process_deleted_folder(parent_folder, base, repo)

    base.create_relationship(
        parent_key, file_properties["key"], "CONTAINS", {})


def update_placeholder_file_node(file: github.File.File, base: Database, repo: github.Repository.Repository):
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
        parent_key, file_properties["key"], "CONTAINS", {})

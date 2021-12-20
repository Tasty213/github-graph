import github
import logging
import logging.config
from time import sleep
from database import Database
import neo4j
from tqdm import tqdm as progress_bar
import re as regex
# Get the logger specified in the file
logger = logging.getLogger(__name__)

files_to_complete = []


def connect_to_database(bolt_url: str, username: str, password: str) -> Database:
    logging.info(
        f"Connecting to neo4j database at {bolt_url} with username {username} and password {password}")
    base = Database(bolt_url, username, password)
    return base


def close_database(base: Database):
    base.close()


def map_repo_files(repo: github.Repository.Repository, base: Database):
    repo_properties = {
        "key": f"repo_{repo.full_name}",
        "name": repo.name
    }

    base.create_node_generic(["Repo"], repo_properties)

    for content in progress_bar(repo.get_contents(""), desc="Mapping repo files"):
        if content.type == "dir":
            process_folder(content, base, repo, repo_properties["key"])
        elif content.type == "file":
            process_file(content, base, repo_properties["key"])
        else:
            print(f"unkown file type {content.type}")
            raise TypeError(content)


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
            process_file(content, base, folder_properties["key"])
        elif content.type == "symlink":
            pass
        else:
            logging.critical(f"unkown file type {folder.type}")
            raise TypeError(content)


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
        process_deleted_folder(parent_folder, base, repo)

    base.create_relationship(
        parent_key, file_properties["key"], "CONTAINS", {})


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


def process_commit(commit: github.Commit.Commit, base: Database, repo: github.Repository.Repository):
    commit_properties = {
        "author": commit.author.login,
        "name": f"{commit.author.login} - {commit.sha}",
        "url": commit.html_url,
        "sha": commit.sha,
        "key": f"commit_{commit.sha}",
        "message": f"{commit.commit.message}",
        "additions": commit.stats.additions,
        "deletions": commit.stats.deletions,
        "totalChanges": commit.stats.total
    }
    if "Merge pull request #" in commit_properties["message"]:
        return
    base.create_node_generic(["Commit"], commit_properties)

    for file in progress_bar(commit.files, desc="Commit", total=len(commit.files), leave=False):
        file_key = f"file_{file.filename}"
        if not base.check_node_exists(file_key):
            process_deleted_file(file, base, repo)
        elif file_key in files_to_complete:
            update_placeholder_file_node(file, base, repo)
            files_to_complete.remove(file_key)

        if file.status == "renamed":
            logger.critical("file renamed")
            old_file_properties = {
                "key": f"file_{file.previous_filename}"
            }
            if not base.check_node_exists(old_file_properties["key"]):
                files_to_complete.append(old_file_properties["key"])
                base.create_node_generic(
                    ["File", "Deleted"], old_file_properties)

            base.create_relationship(
                old_file_properties["key"], file_key, "RENAMED", {})

        relationship_properties = {
            "additions": file.additions,
            "changes": file.changes,
            "deletions": file.deletions,
            "patch": file.patch
        }

        base.create_relationship(
            commit_properties["key"], file_key, "CHANGED", relationship_properties)


def map_commits(repo, base):
    commits = repo.get_commits()
    for commit in progress_bar(commits, total=commits.totalCount, desc="Processing commits"):
        process_commit(commit, base, repo)


def isResultRecord(results):
    try:
        results.peek()
    except neo4j.ResultError:
        return False
    else:
        return True

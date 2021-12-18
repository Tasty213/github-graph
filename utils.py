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


def enable_log():
    logger.debug('This is a debug message')
    logger.info("Logging enabled for root")


def connect_to_database() -> Database:
    bolt_url = "neo4j+s://449e806d.databases.neo4j.io"
    user = "neo4j"
    password = "sg6UCnsNoh6NswmueCvUexEgaTcN04SXCU2gjEi9zCE"
    logging.info(
        f"Connecting to neo4j database at {bolt_url} with username {user} and password {password}")
    base = Database(bolt_url, user, password)
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
        else:
            logging.info(f"unkown file type {folder.type}")
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
    base.create_relationship(parent_key, file_properties["key"], "CONTAINS")


def process_deleted_file(file: github.File.File, base: Database, repo: github.Repository.Repository):
    if "/" in file.filename:
        parent_key = regex.search('.*(?=\/.*$)', file.filename).group(0)
    else:
        parent_key = f"repo_{repo.full_name}"

    file_properties = {
        "name": file.filename,
        "url": file.raw_url,
        "sha": file.sha,
        "key": f"file_{file.filename}"
    }
    base.create_node_generic(["File"], file_properties)
    base.create_relationship(parent_key, file_properties["key"], "CONTAINS")


def process_commit(commit: github.Commit.Commit, base: Database, repo: github.Repository.Repository):
    commit_properties = {
        "author": commit.author.login,
        "name": f"{commit.author.login} - {commit.sha}",
        "url": commit.html_url,
        "sha": commit.sha,
        "key": f"commit_{commit.sha}",
        "message": f"{commit.commit.message}"
    }

    base.create_node_generic(["Commit"], commit_properties)

    for file in progress_bar(commit.files, desc="Commit", total=len(commit.files), leave=False):
        file_key = f"file_{file.filename}"
        if not base.check_node_exists(file_key):
            process_deleted_file(file, base, repo)

        base.create_relationship(
            commit_properties["key"], file_key, "CHANGED")


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

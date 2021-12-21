import github
import logging
import logging.config
from database import Database
from tqdm import tqdm as progress_bar
from . import files, authors

# Get the logger specified in the file
logger = logging.getLogger(__name__)


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

    if base.check_node_exists(commit_properties["key"]):
        base.update_node(["Commit"], commit_properties)
    else:
        base.create_node_generic(["Commit"], commit_properties)

    for file in progress_bar(commit.files, desc="Commit", total=len(commit.files), leave=False):
        file_key = f"file_{file.filename}"
        if not base.check_node_exists(file_key):
            files.process_file(file, base, repo, deleted=True)
        elif file_key in files.files_to_complete:
            files.process_file(file, base, repo, update_placeholder=True)
            files.files_to_complete.remove(file_key)

        if file.status == "renamed":
            logger.critical("file renamed")
            old_file_properties = {
                "key": f"file_{file.previous_filename}"
            }
            if not base.check_node_exists(old_file_properties["key"]):
                files.files_to_complete.append(old_file_properties["key"])
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

    author_key = authors.process_author(commit.author, base)
    base.create_relationship(
        author_key, commit_properties["key"], "CREATED", {})

    for parent in commit.parents:
        set_parent_relationship(parent, commit_properties["key"], base)


def set_parent_relationship(parent: github.GitCommit.GitCommit, current_key: str, base: Database):
    parent_key = f"commit_{parent.sha}"
    if not base.check_node_exists(parent_key):
        base.create_node_generic(["Commit"], {"key": parent_key})
    base.create_relationship(parent_key, current_key, "CHILD")


def map_commits(repo, base):
    commits = repo.get_commits()
    for commit in progress_bar(commits, total=commits.totalCount, desc="Processing commits"):
        process_commit(commit, base, repo)

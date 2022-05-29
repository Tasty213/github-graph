import github
import logging
from wrapper import rate_handler

import logging.config
from database import Database
from . import files, authors

# Get the logger specified in the file
logger = logging.getLogger("mappers")


def process_commit(commit: github.Commit.Commit,
                   base: Database,
                   repo: github.Repository.Repository):
    properties = {
        "author": commit.author.name,
        "name": f"{commit.author.name} - {commit.sha}",
        "url": commit.html_url,
        "sha": commit.sha,
        "key": f"commit_{commit.commit.sha}",
        "message": f"{commit.commit.message}",
        "additions": commit.stats.additions,
        "deletions": commit.stats.deletions,
        "totalChanges": commit.stats.total
    }

    logger.info(f"Processing commit {properties['sha']}")

    if base.check_node_exists(properties["key"]):
        logger.debug("Commit node already exists updating with new properties")
        base.update_node(["Commit"], properties)
    else:
        logger.debug("Commit node does not exist creating")
        base.create_node_generic(["Commit"], properties)

    for file in commit.files:
        file_key = f"file_{file.filename}"
        if not base.check_node_exists(file_key):
            files.process_file(file, base, repo, deleted=True)
        elif file_key in files.files_to_complete:
            files.process_file(file, base, repo, update_placeholder=True)
            files.files_to_complete.remove(file_key)

        if file.status == "renamed":
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
            properties["key"], file_key, "CHANGED", relationship_properties)

    if commit.author is not None:
        author_key = authors.process_author(commit.author, base)
        base.create_relationship(
            author_key, properties["key"], "CREATED", {})
    else:
        logger.critical(f"Commit {commit.sha} does not have author")

    for parent in commit.parents:
        set_parent_relationship(parent, properties["key"], base)


def set_parent_relationship(parent: github.GitCommit.GitCommit,
                            current_key: str,
                            base: Database):
    parent_key = f"commit_{parent.sha}"
    if not base.check_node_exists(parent_key):
        base.create_node_generic(["Commit"], {"key": parent_key})
    base.create_relationship(parent_key, current_key, "CHILD")


def map_commits(repo, base):
    commits = rate_handler(repo.get_commits)
    for commit in commits:
        process_commit(commit, base, repo)

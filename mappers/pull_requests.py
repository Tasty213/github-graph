from typing import Dict
import github
import logging
import logging.config
from database import Database
from tqdm import tqdm as progress_bar

from mappers.commits import process_commit
from . import files, authors

# Get the logger specified in the file
logger = logging.getLogger(__name__)


def process_pull_request(pull_request: github.PullRequest.PullRequest, base: Database):
    properties = _pull_request_to_dict(pull_request)
    labels = ["pullRequest", pull_request.state]
    if pull_request.draft:
        labels.append("Draft")
    base.create_node_generic(labels, properties)
    _process_pull_request_commits(pull_request.get_commits(), base, properties)
    _process_pull_request_assignees(
        properties["key"], pull_request.assignees, base)
    base.create_relationship(
        properties["key"], f"user_{pull_request.merged_by.login}", "MERGED_BY")
    base.create_relationship(
        properties["key"], f"user_{pull_request.user.login}", "CREATED")


def _process_pull_request_assignees(pull_request_key: str, assignees: list[github.NamedUser.NamedUser], base: Database):
    for assignee in assignees:
        base.create_relationship(
            pull_request_key, f"user_{assignee.login}", "ASSIGNED")


def _pull_request_to_dict(pull_request) -> dict:
    return {
        "name": pull_request.title,
        "additions": pull_request.additions,
        "deletions": pull_request.deletions,
        "message": pull_request.body,
        "changedFiles": pull_request.changed_files,
        "commentsCount": pull_request.comments,
        "commitsCount": pull_request.commits,
        "url": pull_request.html_url,
        "gitLabel": pull_request.labels,
        "reviewCommentCount": pull_request.review_comments,
        "state": pull_request.state,
        "key": f"pullRequest_{pull_request.id}"
    }


def _process_pull_request_commits(commits: list[github.Commit.Commit], base: Database, properties: Dict):
    for commit in progress_bar(commits, desc="Processing commits in Pull Request"):
        base.create_relationship(
            properties["key"], f"commit_{commit.sha}", "CHILD")


def map_pull_requests(repo: github.Repository.Repository, base: Database):
    pull_requests = repo.get_pulls("all")
    for pull_request in progress_bar(pull_requests, desc="Processing pull requests"):
        process_pull_request(pull_request, base)

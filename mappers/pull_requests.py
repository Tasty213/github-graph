from typing import List
import github
import logging
import logging.config
from database import Database
from . import authors
from wrapper import rate_handler

# Get the logger specified in the file
logger = logging.getLogger("mappers")


def map_pull_requests(repo: github.Repository.Repository, base: Database):
    pull_requests = rate_handler(repo.get_pulls, "closed")
    for pull_request in pull_requests:
        process_pull_request(pull_request, base)


def process_pull_request(
    pull_request: github.PullRequest.PullRequest, base: Database
):
    properties = _pull_request_to_dict(pull_request)
    logger.info(f"Processing pull request {properties['name']}")
    labels = ["pullRequest", pull_request.state]
    if pull_request.draft:
        labels.append("Draft")
    base.create_node_generic(labels, properties)

    _process_pull_request_commits(
        rate_handler(pull_request.get_commits), base, properties["key"]
    )
    _process_pull_request_labels(pull_request.labels, base, properties["key"])
    _process_pull_request_assignees(
        pull_request.assignees, base, properties["key"]
    )

    authors.process_author(pull_request.merged_by, base)
    base.create_relationship(
        properties["key"], f"user_{pull_request.merged_by.login}", "MERGED_BY"
    )
    authors.process_author(pull_request.user, base)
    base.create_relationship(
        properties["key"], f"user_{pull_request.user.login}", "CREATED"
    )

    if pull_request.milestone is not None:
        base.create_relationship(
            properties["key"],
            f"milestone_{pull_request.milestone.title}",
            "HAS_MILESTONE",
        )


def _process_pull_request_assignees(
    assignees: List[github.NamedUser.NamedUser],
    base: Database,
    pull_request_key: str,
):
    for assignee in assignees:
        authors.process_author(assignee, base)
        base.create_relationship(
            pull_request_key, f"user_{assignee.login}", "ASSIGNED"
        )


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
        "reviewCommentCount": pull_request.review_comments,
        "state": pull_request.state,
        "key": f"pullRequest_{pull_request.id}",
    }


def _process_pull_request_labels(
    labels: List[github.Label.Label], base: Database, pull_request_key: str
):
    for label in labels:
        base.create_relationship(
            pull_request_key, f"label_{label.name}", "HAS_LABEL"
        )


def _process_pull_request_commits(
    commits: List[github.Commit.Commit], base: Database, pull_request_key: str
):
    for commit in commits:
        base.create_relationship(
            pull_request_key, f"commit_{commit.sha}", "CHILD"
        )

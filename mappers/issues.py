from typing import List
import github
import logging
import logging.config
from database import Database
from . import authors
from wrapper import rate_handler

# Get the logger specified in the file
logger = logging.getLogger("mappers")


def map_issues(repo: github.Repository.Repository, base: Database):
    issues = rate_handler(repo.get_issues, state="all")
    for issue in issues:
        process_issue(issue, base)


def process_issue(issue: github.Issue.Issue, base: Database):
    properties = {
        "key": f"issue_{issue.id}",
        "name": issue.title,
        "body": issue.body,
        "commentsCount": issue.comments,
        "url": issue.html_url,
    }
    logger.info(f"Processing issue {properties['url']}")
    base.create_node_generic(["Issue", issue.state], properties)
    _process_issue_assignees(issue.assignees, base, properties["key"])
    _process_issue_assignee(issue.assignee, base, properties["key"])
    _process_issue_labels(issue.labels, base, properties["key"])
    _process_issue_milestone(issue.milestone, base, properties["key"])


def _process_issue_assignees(
    assignees: List[github.NamedUser.NamedUser], base: Database, issue_key: str
):
    for assignee in assignees:
        _process_issue_assignee(assignee, base, issue_key)


def _process_issue_assignee(
    assignee: github.NamedUser.NamedUser, base: Database, issue_key: str
):
    if assignee is not None:
        authors.process_author(assignee, base)
        base.create_relationship(
            issue_key, f"user_{assignee.login}", "ASSIGNED"
        )


def _process_issue_labels(
    labels: List[github.Label.Label], base: Database, issue_key: str
):
    for label in labels:
        _process_issue_label(label, base, issue_key)


def _process_issue_label(
    label: github.Label.Label, base: Database, issue_key: str
):
    base.create_relationship(f"label_{label.name}", issue_key, "CHILD")


def _process_issue_milestone(
    milestone: github.Milestone.Milestone, base: Database, issue_key: str
):
    if milestone is not None:
        base.create_relationship(
            f"milestone_{milestone.title}", issue_key, "CHILD"
        )


def _process_issue_pull_request(
    assignees: github.NamedUser.NamedUser, base: Database, issue_key: str
):
    for assignee in assignees:
        _process_issue_assignee(assignee, base, issue_key)

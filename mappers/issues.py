from typing import Dict
import github
import logging
import logging.config
from database import Database
from tqdm import tqdm as progress_bar
from mappers.commits import process_commit
from . import files, authors

# Get the logger specified in the file
logger = logging.getLogger("mappers")


def map_issues(repo: github.Repository.Repository, base: Database):
    issues = repo.get_issues(state="all")
    for issue in progress_bar(issues, desc="Processing issues", total=issues.totalCount):
        process_issue(issue, base)


def process_issue(issue: github.Issue.Issue, base: Database):
    properties = {
        "key": f"issue_{issue.id}",
        "name": issue.title,
        "body": issue.body,
        "commentsCount": issue.comments,
        "url": issue.html_url
    }
    base.create_node_generic(["Issue", issue.state], properties)
    _process_issue_assignees(issue.assignees, base, properties["key"])
    _process_issue_assignee(issue.assignee, base, properties["key"])
    _process_issue_labels(issue.labels, base, properties["key"])
    _process_issue_milestone(issue.milestone, base, properties["key"])


def _process_issue_assignees(assignees: list[github.NamedUser.NamedUser], base: Database, issue_key: str):
    for assignee in assignees:
        _process_issue_assignee(assignee, base, issue_key)


def _process_issue_assignee(assignee: github.NamedUser.NamedUser, base: Database, issue_key: str):
    if assignee is not None:
        authors.process_author(assignee, base)
        base.create_relationship(
            issue_key, f"user_{assignee.login}", "ASSIGNED")


def _process_issue_labels(labels: list[github.Label.Label], base: Database, issue_key: str):
    for label in labels:
        _process_issue_label(label, base, issue_key)


def _process_issue_label(label: github.Label.Label, base: Database, issue_key: str):
    base.create_relationship(f"label_{label.name}", issue_key, "CHILD")


def _process_issue_milestone(milestone: github.Milestone.Milestone, base: Database, issue_key: str):
    if milestone is not None:
        base.create_relationship(
            f"milestone_{milestone.title}", issue_key, "CHILD")


def _process_issue_pull_request(assignees: github.NamedUser.NamedUser, base: Database, issue_key: str):
    for assignee in assignees:
        _process_issue_assignee(assignee, base, issue_key)

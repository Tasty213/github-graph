import github
import logging
import logging.config
from database import Database

# Get the logger specified in the file
logger = logging.getLogger("mappers")


def map_milestones(repo: github.Repository.Repository, base: Database):
    milestones = repo.get_milestones(state="all")
    for milestone in milestones:
        _process_milestone(milestone, base)


def _process_milestone(milestone: github.Milestone.Milestone, base: Database):
    properties = {
        "closedIssuesCount": milestone.closed_issues,
        "openIssuesCount": milestone.closed_issues,
        "description": milestone.description,
        "name": milestone.title,
        "url": milestone.url,
        "key": f"milestone_{milestone.title}"
    }
    base.create_node_generic(["Milestone", milestone.state], properties)
    _process_milestone_labels(milestone.get_labels(), base, properties["key"])


def _process_milestone_labels(labels: list[github.Label.Label], base: Database, milestone_key: str):
    for label in labels:
        base.create_relationship(
            milestone_key, f"label_{label.name}", "HAS_LABEL")

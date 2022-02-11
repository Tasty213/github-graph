import github
import logging
import logging.config
from database import Database

# Get the logger specified in the file
logger = logging.getLogger("mappers")


def map_labels(repo: github.Repository.Repository, base: Database):
    for label in repo.get_labels():
        _process_label(label, base)


def _process_label(label: github.Label.Label, base: Database):
    properties = {
        "color": label.color,
        "description": label.description,
        "name": label.name,
        "url": label.url,
        "key": f"label_{label.name}"
    }
    base.create_node_generic(["Label"], properties)

import github
import logging
import logging.config
from database import Database
from tqdm import tqdm as progress_bar


def map_labels(repo: github.Repository.Repository, base: Database):
    for label in progress_bar(repo.get_labels(), desc="Processing labels"):
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

import re
from github import Github
from database import Database
import sys
import utils
from time import time
import logging
from tqdm import tqdm as progress_bar

if __name__ == "__main__":
    logging.config.fileConfig(
        fname='logging.conf', disable_existing_loggers=False)

    utils.enable_log()

    # exit()
    base = utils.connect_to_database()

    base.clear_database()

    github = Github("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")
    repo = github.get_repo("numpy/numpy")
    logging.info(f"Building graph database for {repo.full_name}")

    #utils.map_repo_files(repo, base)
    utils.map_commits(repo, base)

    utils.close_database(base)

from wrapper import rate_handler
import utils
import mappers.repos
import mappers.commits
import mappers.labels
import mappers.pull_requests
import mappers.milestones
import mappers.issues
import logging
import os
from github import Github

if __name__ == "__main__":
    logging.config.fileConfig(
        fname='logging.conf', disable_existing_loggers=False)
    neo4j_bolt = os.getenv("NEO4J_BOLT")
    neo4j_username = os.getenv("NEO4J_USER")
    neo4j_password = os.getenv("NEO4J_PASSWORD")
    github_key = os.getenv("GITHUB_API_KEY")
    github_repo = os.getenv("GITHUB_REPO")

    base = utils.connect_to_database(
        neo4j_bolt, neo4j_username, neo4j_password)
    try:
        base.clear_database()

        github = Github(github_key)
        repo = rate_handler(github.get_repo, github_repo)
        logging.info(f"Building graph database for {repo.full_name}")

        mappers.repos.map_repo_files(repo, base)
        mappers.commits.map_commits(repo, base)
        mappers.labels.map_labels(repo, base)
        mappers.milestones.map_milestones(repo, base)
        mappers.pull_requests.map_pull_requests(repo, base)
        mappers.issues.map_issues(repo, base)
    finally:
        utils.close_database(base)

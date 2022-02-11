from github import Github
import argparse
from database import Database
import utils
import mappers.repos
import mappers.commits
import mappers.labels
import mappers.pull_requests
import mappers.milestones
import mappers.issues
import logging

if __name__ == "__main__":
    logging.config.fileConfig(
        fname='logging.conf', disable_existing_loggers=False)
    parser = argparse.ArgumentParser()
    parser.add_argument("-gh", "--github_key")
    parser.add_argument("-gr", "--github_repo")
    parser.add_argument("-nb", "--neo4j_bolt")
    parser.add_argument("-nu", "--neo4j_username")
    parser.add_argument("-np", "--neo4j_password")
    args = parser.parse_args()
    base = utils.connect_to_database(
        args.neo4j_bolt, args.neo4j_username, args.neo4j_password)

    base.clear_database()

    github = Github(args.github_key)
    repo = github.get_repo(args.github_repo)
    logging.info(f"Building graph database for {repo.full_name}")

    mappers.repos.map_repo_files(repo, base)
    mappers.commits.map_commits(repo, base)
    mappers.labels.map_labels(repo, base)
    mappers.milestones.map_milestones(repo, base)
    mappers.pull_requests.map_pull_requests(repo, base)
    mappers.issues.map_issues(repo, base)
    utils.close_database(base)

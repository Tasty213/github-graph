from github import Github
import argparse
import utils
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

    utils.map_repo_files(repo, base)
    utils.map_commits(repo, base)

    utils.close_database(base)

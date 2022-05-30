from github import Github
import os
from .. import utils
from ..mappers import commits

neo4j_bolt = os.getenv("NEO4J_BOLT")
neo4j_username = os.getenv("NEO4J_USER")
neo4j_password = os.getenv("NEO4J_PASSWORD")
github_key = os.getenv("GITHUB_API_KEY")
github_repo = os.getenv("GITHUB_REPO")


def test_commit_with_none_type():
    problematic_sha = "41cf10dcb6ab46064d73f2c054e618c76c3cfabc"
    base = utils.connect_to_database(
        neo4j_bolt, neo4j_username, neo4j_password
    )
    github = Github(github_key)
    repo = github.get_repo(github_repo)
    commits.process_commit(repo.get_commit(problematic_sha), base, repo)

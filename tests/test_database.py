from .. import database
import os

neo4j_bolt = os.getenv("NEO4J_BOLT")
neo4j_username = os.getenv("NEO4J_USER")
neo4j_password = os.getenv("NEO4J_PASSWORD")
github_key = os.getenv("GITHUB_API_KEY")
github_repo = os.getenv("GITHUB_REPO")


def test_dict_to_cypher_properties():
    properties = {"key_1": "value_1", "key_2": 2}
    expected = ""
    assert database.dict_to_cypher_properties(properties) == expected

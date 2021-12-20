import logging
from typing import Any
from neo4j import GraphDatabase
import neo4j
from neo4j.exceptions import ServiceUnavailable

logger = logging.getLogger(__name__)


def dict_to_cypher_properties(properties: dict[str, Any]):
    cypher = "{"
    for property_name in properties:
        property = properties[property_name]
        if isinstance(property, str):
            property = property.replace("\\", "\\\\")
            property = property.replace("\"", "\\\"")
        cypher = cypher + property_name + ": \"" + \
            str(property) + "\","
    cypher = cypher.removesuffix(",") + "}"
    return cypher


class Database:
    def __init__(self, uri, user, password):
        logger.critical(__name__)
        logger.info("Initialising neo4j driver")
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        logger.debug("neo4j driver initialised")

    def close(self):
        # Don't forget to close the driver connection when you are finished with it
        self.driver.close()

    def create_node_generic(self, labels: list[str], properties: dict[str, str]):
        logger.info(f"Creating a generic node")
        labels_string = ":".join(labels)
        properties_string = dict_to_cypher_properties(properties)
        query = (
            f"CREATE (node:{labels_string} {properties_string}) "
            f"RETURN node"
        )

        with self.driver.session() as session:
            # Write transactions allow the driver to handle retries and transient errors
            result = session.write_transaction(
                self._execute_cypher, query)
            return result

    def create_relationship(self, key_1: str, key_2: str, relationship_type: str, properties: dict = {}):
        logger.info(
            f"Creating a relationship between {key_1} and {key_2} of type {relationship_type} and properties {properties}")
        properties_string = dict_to_cypher_properties(properties)
        query = (
            f"MATCH(node_1), (node_2)"
            f"WHERE node_1.key = '{key_1}' AND node_2.key = '{key_2}'"
            f"CREATE(node_1) - [r:{relationship_type} {properties_string}] -> (node_2)"
            f"RETURN node_1, r, node_2"
        )

        with self.driver.session() as session:
            # Write transactions allow the driver to handle retries and transient errors
            result = session.write_transaction(
                self._execute_cypher, query)
            return result

    def check_node_exists(self, key: str) -> neo4j.Result:
        query = (
            f"MATCH(node) WHERE node.key = '{key}' RETURN COUNT(node)"
        )

        with self.driver.session() as session:
            # Write transactions allow the driver to handle retries and transient errors
            results = session.read_transaction(
                self._execute_cypher, query)
            if results[0][0] == 0:
                return False
            else:
                return True

    def update_node(self, labels: list[str], properties: dict[str, str]) -> neo4j.Result:
        logger.info(f"Updating node with key {properties['key']}")
        labels_string = ":".join(labels)
        properties_string = dict_to_cypher_properties(properties)

        query = (
            f"MATCH(node) WHERE node.key = '{properties['key']}'"
            f"SET node:{labels_string} "
            f"SET node = {properties_string}"
        )

        with self.driver.session() as session:
            # Write transactions allow the driver to handle retries and transient errors
            result = session.write_transaction(
                self._execute_cypher, query)
            return result

    def clear_database(self):
        with self.driver.session() as session:
            logger.warning("Clearing all existing nodes and relationships")
            # Write transactions allow the driver to handle retries and transient errors
            query = (
                f"MATCH(n)"
                f"DETACH DELETE n"
            )
            result = session.write_transaction(
                self._execute_cypher, query)
            return result

    def _execute_cypher(self, tx, query: str):
        logger.info("Executing cypher query")
        logger.info(query)
        results = tx.run(query)
        results_list = []
        for result in results:
            results_list.append(result)
        try:
            return results_list
        # Capture any errors along with the query and data for traceability
        except ServiceUnavailable as exception:
            logger.error("{query} raised an error: \n {exception}".format(
                query=query, exception=exception))
            raise

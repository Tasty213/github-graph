import logging
import logging.config
from database import Database
import neo4j
# Get the logger specified in the file
logger = logging.getLogger(__name__)

files_to_complete = []


def connect_to_database(bolt_url: str, username: str, password: str) -> Database:
    logging.info(
        f"Connecting to neo4j database at {bolt_url} with username {username} and password {password}")
    base = Database(bolt_url, username, password)
    return base


def close_database(base: Database):
    base.close()


def isResultRecord(results):
    try:
        results.peek()
    except neo4j.ResultError:
        return False
    else:
        return True

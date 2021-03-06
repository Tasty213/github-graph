import github
import logging
import logging.config
from database import Database

# Get the logger specified in the file
logger = logging.getLogger("mappers")


def process_author(author: github.NamedUser.NamedUser, base: Database):
    properties = {
        "avatar": author.avatar_url,
        "bio": author.bio,
        "blog": author.blog,
        "followerCount": author.followers,
        "followingCount": author.following,
        "profile": author.html_url,
        "name": author.login,
        "privateRepos": author.owned_private_repos,
        "privateGists": author.private_gists,
        "publicRepos": author.public_repos,
        "publicGists": author.public_gists,
        "key": f"user_{author.login}",
    }
    logger.info(f"Processing author {properties.get('key')}")
    if not base.check_node_exists(properties["key"]):
        logger.debug("Author does not exist creating in graph")
        base.create_node_generic(["User"], properties)
    return properties["key"]

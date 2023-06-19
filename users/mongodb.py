"""MongoDB connection and queries."""
import logging
from typing import List, Tuple

from bson import SON
from pymongo import MongoClient, GEO2D

from users.config import AppConfig

LOCATION_KEY = "location"
USER_ID_KEY = "user_id"


def get_mongo_url(config: AppConfig) -> str:
    """Build MongoDB URI."""
    return f"{config.mongo.driver}://{config.mongo.user}:" +\
        f"{config.mongo.password}@{config.mongo.host}/{config.mongo.database}"


def initialize(connection: MongoClient):
    """Create geolocation index."""
    connection.fiufit.user_location.create_index([(LOCATION_KEY, GEO2D)])


def get_mongodb_connection(connection_string: str) -> MongoClient:
    """Create a MongoDB connection."""
    client = MongoClient(connection_string)
    return client


def add_location(
    connection: MongoClient,
    user_id: int,
    location: Tuple[float, float]
):
    """Create location for a user."""
    document = {USER_ID_KEY: user_id, LOCATION_KEY: location}
    logging.info("Creating location %s", document)
    connection.fiufit.user_location.insert_one(document)


def edit_location(
    connection: MongoClient, user_id: int, location: Tuple[float, float]
):
    """Edit location for a user. Creates if does not exist."""
    user_filter = {USER_ID_KEY: user_id}
    document = {USER_ID_KEY: user_id, LOCATION_KEY: location}
    logging.info("Updating location %s", document)
    connection.fiufit.user_location.replace_one(user_filter, document, True)


def get_users_within(
    connection: MongoClient, location: Tuple[float, float], radius: int
) -> List[int]:
    """Search for users within radius from location."""
    query = {"loc": SON([("$near", location), ("$maxDistance", radius)])}
    logging.info("Searching for users %s", query)
    connection.fiufit.user_location.find(query)

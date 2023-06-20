"""Helper methods for users."""
import logging
from typing import Tuple
from users.config import AppConfig
from users.mongodb import (
    edit_location,
    get_mongodb_connection
)


def save_location(
    mongo_url: str,
    is_athlete: bool,
    user_id: int,
    coordinates: Tuple[float, float],
    config: AppConfig
):
    """Save location if user is trainer."""
    if not config.mongo.enabled:
        logging.debug("Geolocation disabled, not saving coordinates.")
        return
    if is_athlete:
        logging.debug("Not saving location in MongoDB for athlete")
        return
    logging.debug("Saving location in MongoDB...")
    edit_location(get_mongodb_connection(mongo_url), user_id, coordinates)

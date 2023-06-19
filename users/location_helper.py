"""Helper methods for users."""
import logging
from typing import Tuple
from users.mongodb import (
    add_location,
    get_mongodb_connection
)


def save_location(
    mongo_url: str,
    is_athlete: bool,
    user_id: int,
    coordinates: Tuple[float, float],
):
    """Save location if user is trainer."""
    if is_athlete:
        logging.debug("Not saving location in MongoDB for athlete")
    else:
        logging.debug("Saving location in MongoDB...")
        add_location(get_mongodb_connection(mongo_url), user_id, coordinates)

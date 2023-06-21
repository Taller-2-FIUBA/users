"""Helper methods for users."""
import logging
from typing import List, Tuple, Optional

from fastapi import HTTPException, status
from users.config import AppConfig
from users.mongodb import (
    edit_location,
    get_mongodb_connection
)


def get_coordinates(
    longitude: Optional[float], latitude: Optional[float]
) -> Optional[Tuple]:
    """Parameter validation."""
    if not latitude and not longitude:
        return None
    if latitude and not longitude:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="Longitude MUST BE defined when searching by location."
        )
    if longitude and not latitude:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="Latitude MUST BE defined when searching by location."
        )
    return (longitude, latitude)


def get_user_ids(documents: List) -> List:
    """Build a list of user IDs from MongoDB documents."""
    ids = []
    for document in documents:
        ids.append(document["user_id"])
    return ids


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

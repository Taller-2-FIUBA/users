"""Write application metrics to Reddis queue."""

import logging
from datetime import datetime
from typing import Optional
from redis import Redis, BlockingConnectionPool
from users.config import AppConfig


def get_redis_connection(config: AppConfig) -> Redis:
    """Create a redis connection."""
    logging.info("Connecting to Redis...")
    pool = BlockingConnectionPool(
        host=config.redis.host,
        port=config.redis.port,
        db=0,
        timeout=10,
    )
    return Redis(connection_pool=pool)


# pylint: disable=broad-exception-caught
def queue(config: AppConfig, name: str, label: Optional[str] = None) -> None:
    """Queue a metric with name and label."""
    message = {
        "metric": name,
        "value": 1,  # How much to increase
        "date": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
    }
    if label:
        message["label"] = label
    try:
        client = get_redis_connection(config)
        logging.exception("Queuing message %s", message)
        client.rpush("metrics", str(message))
    except Exception:
        logging.exception("Error when trying to save metrics.")

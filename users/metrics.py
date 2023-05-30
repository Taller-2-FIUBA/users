"""Metric definition."""
from prometheus_client import Counter

REQUEST_COUNTER = Counter(
    "requests", "Amount of requests.", ["endpoint", "http_verb"]
)

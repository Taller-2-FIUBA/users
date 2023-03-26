"""Requests handlers."""
from fastapi import FastAPI
from environ import to_config
from prometheus_client import start_http_server, Counter
from users.config import AppConfig


REQUEST_COUNTER = Counter(
    "my_failures", "Description of counter", ["endpoint", "http_verb"]
)
CONFIGURATION = to_config(AppConfig)
start_http_server(8000)
app = FastAPI()


@app.get("/")
async def root():
    """Greet."""
    REQUEST_COUNTER.labels("/", "get").inc()
    return {"message": "Hello World"}

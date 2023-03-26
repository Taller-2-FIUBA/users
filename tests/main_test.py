# pylint: disable= missing-module-docstring, missing-function-docstring
from fastapi.testclient import TestClient
from users.main import app

client = TestClient(app)


def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}

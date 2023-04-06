# pylint: disable= missing-module-docstring, missing-function-docstring
# pylint: disable= unused-argument, redefined-outer-name
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from users.main import app, get_db
from users.database import Base

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        database = TestingSessionLocal()
        yield database
    finally:
        database.close()


# to build and tear down test database
@pytest.fixture()
def test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def test_read_main(test_db):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


def test_database_empty_at_start(test_db):
    response = client.get("users/")
    assert response.status_code == 200
    assert response.json() == []


new_user_1 = {
        "id": "jorgito_id",
        "username": "jorgitogroso",
        "email": "jorgito@abcd.com",
        "name": "Jorge",
        "surname": "Perales",
        "height": 1.9,
        "weight": 100,
        "birth_date": "23-4-1990",
        "location": "Buenos Aires, Argentina",
        "registration_date": "23-4-2023"
}

new_user_2 = {
    "id": "pepito_id",
    "username": "pepitobasura",
    "email": "pepito@abcd.com",
    "name": "Pepo",
    "surname": "Gutierrez",
    "height": 1.8,
    "weight": 60,
    "birth_date": "23-4-1987",
    "location": "Rosario, Santa Fe",
    "registration_date": "23-3-2023"
}

new_user_3 = {
    "id": "anita_id",
    "username": "anitazoomer",
    "email": "anita@abcd.com",
    "name": "Ana",
    "surname": "Rodriguez",
    "height": 1.3,
    "weight": 80,
    "birth_date": "23-4-1999",
    "location": "Cordoba, Cordoba",
    "registration_date": "23-3-2022"
}


def test_user_stored_correctly(test_db):
    response = client.post("users", json=new_user_1)
    assert response.status_code == 200
    assert response.json() == new_user_1


def test_several_users_stored_correctly(test_db):
    client.post("users", json=new_user_1)
    client.post("users", json=new_user_2)
    response = client.get("users/")
    assert response.status_code == 200
    assert {
        new_user_1 and new_user_2 in response.json()
}


def test_user_that_wasnt_stored_isnt_retrieved(test_db):
    client.post("users", json=new_user_1)
    client.post("users", json=new_user_2)
    response = client.get("users/")
    assert response.status_code == 200
    assert {
        new_user_3 not in response.json()
    }


def test_can_retrieve_user_with_his_id(test_db):
    client.post("users", json=new_user_1)
    response = client.get("users/jorgito_id")
    assert response.status_code == 200
    assert response.json() == new_user_1


def test_cannot_retrieve_user_with_wrong_id(test_db):
    client.post("users", json=new_user_1)
    response = client.get("users/francisco_id")
    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}

# TODO: data validation tests

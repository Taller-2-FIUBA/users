# pylint: disable= missing-module-docstring, missing-function-docstring
# pylint: disable= unused-argument, redefined-outer-name
import pytest
import jwt
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from users.main import app, get_db
from users.database import Base

SQLALCHEMY_DATABASE_URL = "sqlite:///./tests/test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False,
                                   autoflush=False,
                                   bind=engine)


def override_get_db():
    try:
        database = TestingSessionLocal()
        yield database
    finally:
        database.close()


# to build and tear down test database and firebase authentication
@pytest.fixture
def test_db():
    Base.metadata.create_all(bind=engine)
    yield
    for email in user_emails:
        client.delete("users" + "?email=" + email)
    Base.metadata.drop_all(bind=engine)
    user_emails.clear()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

user_emails = []


def test_database_empty_at_start(test_db):
    response = client.get("users/")
    assert response.status_code == 200
    assert response.json() == []


user_1 = {
    "password": "jorgito_pw",
    "username": "jorgitogroso",
    "email": "jorgditodd@asddbcdd.com",
    "name": "Jorge",
    "surname": "Perales",
    "height": 1.9,
    "weight": 100,
    "birth_date": "23-4-1990",
    "location": "Buenos Aires, Argentina",
    "registration_date": "23-4-2023",
}

user_2 = {
    "password": "pepito_pw",
    "username": "pepitobasura",
    "email": "pepitod@abcd.com",
    "name": "Pepo",
    "surname": "Gutierrez",
    "height": 1.8,
    "weight": 60,
    "birth_date": "23-4-1987",
    "location": "Rosario, Santa Fe",
    "registration_date": "23-3-2023",
}

user_3 = {
    "password": "anita_pw",
    "username": "anitazoomer",
    "email": "anita@abcd.com",
    "name": "Ana",
    "surname": "Rodriguez",
    "height": 1.3,
    "weight": 80,
    "birth_date": "23-4-1999",
    "location": "Cordoba, Cordoba",
    "registration_date": "23-3-2022",
}


def equal_dicts(dict1, dict2, ignore_keys):
    d1_filtered = {k: v for k, v in dict1.items() if k not in ignore_keys}
    d2_filtered = {k: v for k, v in dict2.items() if k not in ignore_keys}
    return d1_filtered == d2_filtered


def test_user_stored_correctly(test_db):
    response = client.post("users", json=user_1)
    user_emails.append(user_1["email"])
    assert response.status_code == 200
    assert equal_dicts(response.json(), user_1, {"id", "password"})


def test_several_users_stored_correctly(test_db):
    response1 = client.post("users", json=user_1)
    response2 = client.post("users", json=user_2)
    user_emails.append(user_1["email"])
    user_emails.append(user_2["email"])
    assert response1.status_code == 200
    assert response2.status_code == 200
    assert equal_dicts(response1.json(), user_1, {"id", "password"})
    assert equal_dicts(response2.json(), user_2, {"id", "password"})


def test_user_that_wasnt_stored_isnt_retrieved(test_db):
    client.post("users", json=user_1)
    client.post("users", json=user_2)
    user_emails.append(user_1["email"])
    user_emails.append(user_2["email"])
    response = client.get("users/")
    keys = {"id", "password"}
    assert (equal_dicts(response.json()[0], user_3, keys)) is False
    assert (equal_dicts(response.json()[1], user_3, keys)) is False


# shouldn't assume an order for results
def test_can_get_several_user_details(test_db):
    client.post("users", json=user_1)
    client.post("users", json=user_2)
    client.post("users", json=user_3)
    user_emails.append(user_1["email"])
    user_emails.append(user_2["email"])
    user_emails.append(user_3["email"])
    response = client.get("users/")
    assert equal_dicts(response.json()[0], user_1, {"id", "password"})
    assert equal_dicts(response.json()[1], user_2, {"id", "password"})
    assert equal_dicts(response.json()[2], user_3, {"id", "password"})


def test_can_retrieve_user_with_his_id(test_db):
    response1 = client.post("users", json=user_1)
    user_emails.append(user_1["email"])
    response2 = client.get("users/" + response1.json()["id"])
    assert response2.status_code == 200
    assert equal_dicts(response2.json(), user_1, {"id", "password"})


def test_cannot_retrieve_user_with_wrong_id(test_db):
    client.post("users", json=user_1)
    user_emails.append(user_1["email"])
    response = client.get("users/" + "fake_id")
    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}


def test_existing_user_logs_in_correctly(test_db):
    client.post("users", json=user_2)
    user_emails.append(user_2["email"])
    request = {"email": user_2["email"], "password": user_2["password"]}
    response = client.post("users/login", json=request)
    assert response.status_code == 200


def test_non_existing_user_raises_exception_at_log_in(test_db):
    client.post("users", json=user_2)
    user_emails.append(user_2["email"])
    request = {"email": user_1["email"], "password": user_1["password"]}
    response = client.post("users/login", json=request)
    assert response.status_code == 400
    assert response.json() == {"detail": "Error logging in"}


def test_token_has_expected_data(test_db):
    create_response = client.post("users", json=user_3)
    user_emails.append(user_3["email"])
    request = {"email": user_3["email"], "password": user_3["password"]}
    login_response = client.post("users/login", json=request)
    ret_token = login_response.json()["token"]
    dec_token = jwt.decode(ret_token, "secret", algorithms="HS256")
    assert dec_token == {"id": create_response.json()["id"], "role": "admin"}

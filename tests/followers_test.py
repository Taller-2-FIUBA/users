# pylint: disable= missing-module-docstring, missing-function-docstring
# pylint: disable= unused-argument, redefined-outer-name
# pylint: disable= duplicate-code
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from tests.testing_util import test_wallet_1, user_1, \
    user_2, user_3, equal_dicts
from users.main import app, get_db
from users.models import Base

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
    Base.metadata.drop_all(bind=engine)


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def test_cant_follow_users_with_nonexistent_user(test_db):
    response = client.post("users/1/followed/2")
    assert response.status_code == 404
    error_msg = {'detail': 'User not found'}
    assert response.json() == error_msg


@patch('users.main.get_credentials')
@patch('users.main.create_wallet')
@patch('users.main.add_user_firebase')
@patch('users.main.save_location')
def test_followed_users_get_updated_correctly(save_mock,
                                              add_mock,
                                              create_wallet_mock,
                                              get_creds_mock,
                                              test_db):
    add_mock.return_value = None
    save_mock.return_value = None
    create_wallet_mock.return_value = test_wallet_1
    client.post("users", json=user_1)
    client.post("users", json=user_2)
    client.post("users", json=user_3)
    get_creds_mock.return_value = {"id": 1, "role": "user"}
    client.post("users/1/followed/2")
    post_response = client.post("users/1/followed/3")
    get_response = client.get("users/1/followed")
    assert post_response.json() == get_response.json()


@patch('users.main.get_credentials')
@patch('users.main.create_wallet')
@patch('users.main.add_user_firebase')
@patch('users.main.save_location')
def test_followers_get_updated_correctly(save_mock,
                                         add_mock,
                                         create_wallet_mock,
                                         get_creds_mock,
                                         test_db):
    add_mock.return_value = None
    save_mock.return_value = None
    create_wallet_mock.return_value = test_wallet_1
    client.post("users", json=user_1)
    client.post("users", json=user_2)
    client.post("users", json=user_3)
    get_creds_mock.return_value = {"id": 1, "role": "user"}
    client.post("users/1/followed/2")
    get_creds_mock.return_value = {"id": 3, "role": "user"}
    client.post("users/3/followed/2")
    get_response = client.get("users/2/followers")
    assert equal_dicts(get_response.json()[0],
                       user_1, {"id", "password", "is_blocked"})
    assert equal_dicts(get_response.json()[1],
                       user_3, {"id", "password", "is_blocked"})


@patch('users.main.get_credentials')
@patch('users.main.create_wallet')
@patch('users.main.add_user_firebase')
@patch('users.main.save_location')
def test_deleted_followers_get_updated_correctly(save_mock,
                                                 add_mock,
                                                 create_wallet_mock,
                                                 get_creds_mock,
                                                 test_db):
    add_mock.return_value = None
    save_mock.return_value = None
    create_wallet_mock.return_value = test_wallet_1
    client.post("users", json=user_1)
    client.post("users", json=user_2)
    client.post("users", json=user_3)
    get_creds_mock.return_value = {"id": 1, "role": "user"}
    client.post("users/1/followed/2")
    get_creds_mock.return_value = {"id": 2, "role": "user"}
    client.post("users/3/followed/1")
    get_creds_mock.return_value = {"id": 3, "role": "user"}
    post_response = client.post("users/2/followed/3")
    get_creds_mock.return_value = {"id": 2, "role": "user"}
    assert len(post_response.json()) == 1
    client.delete("users/2/followed/3")
    get_creds_mock.return_value = {"id": 3, "role": "user"}
    response = client.get("users/3/followers")
    assert len(response.json()) == 0
    get_creds_mock.return_value = {"id": 2, "role": "user"}
    response = client.get("users/2/followed")
    assert len(response.json()) == 0

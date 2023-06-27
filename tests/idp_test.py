# pylint: disable= missing-module-docstring, missing-function-docstring
# pylint: disable= unused-argument, redefined-outer-name
# pylint: disable= duplicate-code
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from tests.testing_util import test_wallet, idp_user_1, idp_user_2, equal_dicts

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

ignored_keys = {"id", "is_blocked"}


@patch('users.main.create_wallet')
@patch('users.main.validate_idp_token')
def test_can_create_idp_user(validate_idp_mock,
                             create_wallet_mock, test_db):
    user = idp_user_1
    validate_idp_mock.return_value = None
    create_wallet_mock.return_value = test_wallet
    response = client.post("users/usersIDP", json=user)
    assert response.status_code == 200
    assert equal_dicts(response.json(), user, ignored_keys)


@patch('users.main.create_wallet')
@patch('users.main.validate_idp_token')
def test_cant_create_two_users_with_same_username(validate_idp_mock,
                                                  create_wallet_mock, test_db):
    user1 = idp_user_1
    validate_idp_mock.return_value = None
    create_wallet_mock.return_value = test_wallet
    client.post("users/usersIDP", json=user1)
    user2 = idp_user_2
    user2["username"] = "jorgitogroso"
    response = client.post("users/usersIDP", json=user2)
    assert response.status_code == 400
    error_msg = {'detail': 'User with that username already present'}
    assert response.json() == error_msg


@patch('users.main.create_wallet')
@patch('users.main.validate_idp_token')
def test_cant_create_two_users_with_same_email(validate_idp_mock,
                                               create_wallet_mock, test_db):
    user1 = idp_user_1
    validate_idp_mock.return_value = None
    create_wallet_mock.return_value = test_wallet
    client.post("users/usersIDP", json=user1)
    user2 = idp_user_2
    user2["email"] = "jorgitodd@asddbcdd.com"
    response = client.post("users/usersIDP", json=user2)
    assert response.status_code == 400
    error_msg = {'detail': 'User with that email already present'}
    assert response.json() == error_msg


@patch('users.main.validate_idp_token')
def test_cant_log_in_if_theres_no_user_with_that_email(validate_idp_mock,
                                                       test_db):
    validate_idp_mock.return_value = None
    body = {"email": "nosuchuser@gmail.com"}
    response = client.post("users/login/usersIDP", json=body)
    assert response.status_code == 404
    error_msg = {'detail': {'message': 'No IDP user with such an email'}}
    assert response.json() == error_msg


@patch('users.main.get_token')
@patch('users.main.create_wallet')
@patch('users.main.validate_idp_token')
def test_log_in_returns_token_if_user_exists_and_had_valid_token(
        validate_idp_mock,
        create_wallet_mock,
        get_token_mock,
        test_db):
    user1 = idp_user_1
    validate_idp_mock.return_value = None
    create_wallet_mock.return_value = test_wallet
    client.post("users/usersIDP", json=user1)
    body = {"email": "jorgitodd@asddbcdd.com"}
    get_token_mock.return_value = "token"
    response = client.post("users/login/usersIDP", json=body)
    assert response.status_code == 200
    value = {"token": "token", "id": 1}
    assert response.json() == value

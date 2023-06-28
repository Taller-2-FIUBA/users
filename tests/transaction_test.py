# pylint: disable= missing-module-docstring, missing-function-docstring
# pylint: disable= unused-argument, redefined-outer-name
# pylint: disable= duplicate-code
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from tests.testing_util import test_wallet_1, user_1, \
    test_wallet_2, user_2, equal_dicts
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


@patch('users.main.get_auth_header')
def test_cant_get_transactions_with_no_token(get_header,
                                             test_db):
    get_header.return_value = None
    response = client.get("users/transactions")
    assert response.status_code == 403
    error_msg = {'detail': 'No token'}
    assert response.json() == error_msg


@patch('users.main.get_credentials')
def test_cant_get_transactions_with_user_token(get_creds_mock, test_db):
    get_creds_mock.return_value = {"id": 1, "role": "user"}
    response = client.get("users/transactions")
    assert response.status_code == 403
    error_msg = {'detail': 'Invalid credentials'}
    assert response.json() == error_msg


@patch('users.main.get_credentials')
def test_can_get_transactions_with_admin_token(get_creds_mock, test_db):
    get_creds_mock.return_value = {"id": 1, "role": "admin"}
    response = client.get("users/transactions")
    assert response.status_code == 200
    transactions = {'items': [], 'page': 1, 'pages': 0,
                    'size': 0, 'total': 0}
    assert response.json() == transactions


@patch('users.main.get_credentials')
def test_cant_transfer_money_between_users_with_wrong_creds(get_creds_mock,
                                                            test_db):
    get_creds_mock.return_value = {"id": 1, "role": "user"}
    body = {
        "receiver_id": 1,
        "sender_id": 2,
        "amount": 0.01,
    }
    response = client.post("users/deposit", json=body)
    assert response.status_code == 403
    error_msg = {'detail': 'Invalid credentials'}
    assert response.json() == error_msg


@patch('users.main.get_credentials')
def test_cant_transfer_money_between_users_with_admin_token(get_creds_mock,
                                                            test_db):
    get_creds_mock.return_value = {"id": 1, "role": "admin"}
    body = {
        "receiver_id": 2,
        "sender_id": 1,
        "amount": 0.01,
    }
    response = client.post("users/deposit", json=body)
    assert response.status_code == 403
    error_msg = {'detail': 'Invalid credentials'}
    assert response.json() == error_msg


# pylint: disable=too-many-arguments
@patch('users.main.get_credentials')
@patch('users.main.deposit_money')
@patch('users.main.create_wallet')
@patch('users.main.add_user_firebase')
@patch('users.main.save_location')
def test_can_transfer_money_between_users_with_proper_user_token(
        save_mock,
        add_mock,
        create_wallet_mock,
        deposit_mock,
        get_creds_mock,
        test_db):
    deposit_mock.return_value = None
    add_mock.return_value = None
    save_mock.return_value = None
    create_wallet_mock.return_value = test_wallet_1
    client.post("users", json=user_1)
    create_wallet_mock.return_value = test_wallet_2
    client.post("users", json=user_2)
    get_creds_mock.return_value = {"id": 1, "role": "user"}
    body = {
        "receiver_id": 2,
        "sender_id": 1,
        "amount": 0.01,
    }
    response = client.post("users/deposit", json=body)
    assert response.status_code == 200


@patch('users.main.get_credentials')
@patch('users.main.deposit_money')
@patch('users.main.create_wallet')
@patch('users.main.add_user_firebase')
@patch('users.main.save_location')
def test_cant_transfer_money_between_athletes(
        save_mock,
        add_mock,
        create_wallet_mock,
        deposit_mock,
        get_creds_mock,
        test_db):
    deposit_mock.return_value = None
    add_mock.return_value = None
    save_mock.return_value = None
    create_wallet_mock.return_value = test_wallet_1
    client.post("users", json=user_1)
    create_wallet_mock.return_value = test_wallet_2
    client.post("users", json=user_2)
    get_creds_mock.return_value = {"id": 1, "role": "user"}
    body = {
        "receiver_id": 1,
        "sender_id": 2,
        "amount": 0.01,
    }
    response = client.post("users/deposit", json=body)
    assert response.status_code == 403


@patch('users.main.get_credentials')
@patch('users.main.create_wallet')
@patch('users.main.add_user_firebase')
@patch('users.main.save_location')
def test_can_get_wallet_with_proper_user_token(save_mock,
                                               add_mock,
                                               create_wallet_mock,
                                               get_creds_mock,
                                               test_db):
    add_mock.return_value = None
    save_mock.return_value = None
    create_wallet_mock.return_value = test_wallet_1
    client.post("users", json=user_1)
    get_creds_mock.return_value = {"id": 1, "role": "user"}
    response = client.get("users/1/wallet")
    assert response.status_code == 200
    assert equal_dicts(response.json(), test_wallet_1, {"privateKey",
                                                        "private_key"})


@patch('users.main.get_credentials')
@patch('users.main.create_wallet')
@patch('users.main.add_user_firebase')
@patch('users.main.save_location')
def test_cant_get_wallet_with_admin_token(save_mock,
                                          add_mock,
                                          create_wallet_mock,
                                          get_creds_mock,
                                          test_db):
    add_mock.return_value = None
    save_mock.return_value = None
    create_wallet_mock.return_value = test_wallet_1
    client.post("users", json=user_1)
    get_creds_mock.return_value = {"id": 1, "role": "admin"}
    response = client.get("users/1/wallet")
    assert response.status_code == 403
    error_msg = {'detail': 'Invalid credentials'}
    assert response.json() == error_msg


@patch('users.main.get_credentials')
@patch('users.main.create_wallet')
@patch('users.main.add_user_firebase')
@patch('users.main.save_location')
def test_cant_get_wallet_with_wrong_id_user_token(save_mock,
                                                  add_mock,
                                                  create_wallet_mock,
                                                  get_creds_mock,
                                                  test_db):
    add_mock.return_value = None
    save_mock.return_value = None
    create_wallet_mock.return_value = test_wallet_1
    client.post("users", json=user_1)
    get_creds_mock.return_value = {"id": 2, "role": "user"}
    response = client.get("users/1/wallet")
    assert response.status_code == 403
    error_msg = {'detail': 'Invalid credentials'}
    assert response.json() == error_msg


@patch('users.main.get_credentials')
def test_cant_get_balance_for_nonexistent_wallet(get_creds_mock,
                                                 test_db):
    get_creds_mock.return_value = {"id": 1, "role": "admin"}
    response = client.get("users/1/wallet/balance")
    assert response.status_code == 404
    error_msg = {'detail': 'Non existent wallet'}
    assert response.json() == error_msg


@patch('users.main.get_credentials')
@patch('users.main.create_wallet')
@patch('users.main.add_user_firebase')
@patch('users.main.save_location')
def test_cant_get_balance_with_invalid_user_token(save_mock,
                                                  add_mock,
                                                  create_wallet_mock,
                                                  get_creds_mock,
                                                  test_db):
    add_mock.return_value = None
    save_mock.return_value = None
    create_wallet_mock.return_value = test_wallet_1
    client.post("users", json=user_1)
    get_creds_mock.return_value = {"id": 2, "role": "user"}
    response = client.get("users/1/wallet/balance")
    assert response.status_code == 403
    error_msg = {'detail': 'Invalid credentials'}
    assert response.json() == error_msg


# pylint: disable=too-many-arguments
@patch('users.main.get_balance')
@patch('users.main.get_credentials')
@patch('users.main.create_wallet')
@patch('users.main.add_user_firebase')
@patch('users.main.save_location')
def test_cant_get_balance_with_valid_user_token(save_mock,
                                                add_mock,
                                                create_wallet_mock,
                                                get_creds_mock,
                                                get_balance_mock,
                                                test_db):
    add_mock.return_value = None
    save_mock.return_value = None
    get_balance_mock.return_value = 0
    create_wallet_mock.return_value = test_wallet_1
    client.post("users", json=user_1)
    get_creds_mock.return_value = {"id": 1, "role": "user"}
    response = client.get("users/1/wallet/balance")
    assert response.status_code == 200
    assert response.json() == {"balance": 0}


@patch('users.main.get_credentials')
def test_cant_make_extraction_with_invalid_user_token(get_creds_mock,
                                                      test_db):
    body = {
        "receiver_address": "fakeaddress",
        "sender_id": 1,
        "amount": 0.02
    }
    get_creds_mock.return_value = {"id": 2, "role": "user"}
    response = client.post("users/extraction", json=body)
    assert response.status_code == 403
    error_msg = {'detail': 'Invalid credentials'}
    assert response.json() == error_msg


# pylint: disable=too-many-arguments
@patch('users.main.transfer_money_outside')
@patch('users.main.get_credentials')
@patch('users.main.create_wallet')
@patch('users.main.add_user_firebase')
@patch('users.main.save_location')
def test_can_extract_money_with_valid_user_token(save_mock,
                                                 add_mock,
                                                 create_wallet_mock,
                                                 get_creds_mock,
                                                 transfer_mock,
                                                 test_db):
    transfer_mock.return_value = None
    add_mock.return_value = None
    save_mock.return_value = None
    create_wallet_mock.return_value = test_wallet_1
    client.post("users", json=user_1)
    get_creds_mock.return_value = {"id": 1, "role": "user"}
    body = {
        "receiver_address": "fakeaddress",
        "sender_id": 1,
        "amount": 0.02
    }
    response = client.post("users/extraction", json=body)
    assert response.status_code == 200


# pylint: disable=too-many-arguments
@patch('users.main.add_to_balance')
@patch('users.main.get_credentials')
@patch('users.main.create_wallet')
@patch('users.main.add_user_firebase')
@patch('users.main.save_location')
def test_cant_add_money_to_balance_with_user_token(save_mock,
                                                   add_mock,
                                                   create_wallet_mock,
                                                   get_creds_mock,
                                                   add_balance_mock,
                                                   test_db):
    add_balance_mock.return_value = None
    add_mock.return_value = None
    save_mock.return_value = None
    create_wallet_mock.return_value = test_wallet_1
    client.post("users", json=user_1)
    get_creds_mock.return_value = {"id": 1, "role": "user"}
    body = {
        "amount": 0.02
    }
    response = client.patch("users/1/wallet/balance", json=body)
    assert response.status_code == 403


# pylint: disable=too-many-arguments
@patch('users.main.add_to_balance')
@patch('users.main.get_credentials')
@patch('users.main.create_wallet')
@patch('users.main.add_user_firebase')
@patch('users.main.save_location')
def test_can_add_money_to_balance_with_admin_token(save_mock,
                                                   add_mock,
                                                   create_wallet_mock,
                                                   get_creds_mock,
                                                   add_balance_mock,
                                                   test_db):
    add_balance_mock.return_value = None
    add_mock.return_value = None
    save_mock.return_value = None
    create_wallet_mock.return_value = test_wallet_1
    client.post("users", json=user_1)
    get_creds_mock.return_value = {"id": 1, "role": "admin"}
    body = {
        "amount": 0.02
    }
    response = client.patch("users/1/wallet/balance", json=body)
    assert response.status_code == 200

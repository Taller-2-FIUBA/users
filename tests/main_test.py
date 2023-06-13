# pylint: disable= missing-module-docstring, missing-function-docstring
# pylint: disable= unused-argument, redefined-outer-name
from unittest.mock import patch
from hamcrest import assert_that, greater_than

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from tests.testing_constants import user_1, user_2, user_3, \
    user_to_update, user_template_no_email, private_keys, test_wallet
from users.main import DOCUMENTATION_URI, app, get_db
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

ignored_keys = {"id", "password", "is_blocked"}


def test_database_empty_at_start(test_db):
    response = client.get("users")
    assert response.status_code == 200
    assert response.json()["items"] == []


def equal_dicts(dict1, dict2, ignore_keys):
    d1_filtered = {k: v for k, v in dict1.items() if k not in ignore_keys}
    d2_filtered = {k: v for k, v in dict2.items() if k not in ignore_keys}
    return d1_filtered == d2_filtered


@patch('users.main.create_wallet')
@patch('users.main.add_user_firebase')
def test_user_stored_correctly(add_mock, create_wallet, test_db):
    add_mock.return_value = None
    create_wallet.return_value = test_wallet
    response = client.post("users", json=user_1)
    assert response.status_code == 200
    assert equal_dicts(response.json(), user_1, ignored_keys)


@patch('users.main.create_wallet')
@patch('users.main.add_user_firebase')
def test_several_users_stored_correctly(add_mock, create_wallet, test_db):
    add_mock.return_value = None
    create_wallet.return_value = test_wallet
    response1 = client.post("users", json=user_1)
    response2 = client.post("users", json=user_2)
    assert response1.status_code == 200
    assert response2.status_code == 200
    assert equal_dicts(response1.json(), user_1, ignored_keys)
    assert equal_dicts(response2.json(), user_2, ignored_keys)


@patch('users.main.create_wallet')
@patch('users.main.add_user_firebase')
def test_user_that_wasnt_stored_isnt_retrieved(add_mock,
                                               create_wallet,
                                               test_db):
    add_mock.return_value = None
    create_wallet.return_value = test_wallet
    client.post("users", json=user_1)
    client.post("users", json=user_2)
    response = client.get("users/")
    assert response.status_code == 200
    user1 = response.json()["items"][0]
    user2 = response.json()["items"][1]
    assert (equal_dicts(user1, user_3, ignored_keys)) is False
    assert (equal_dicts(user2, user_3, ignored_keys)) is False


@patch('users.main.create_wallet')
@patch('users.main.add_user_firebase')
def test_can_get_several_user_details(add_mock, create_wallet, test_db):
    add_mock.return_value = None
    create_wallet.return_value = test_wallet
    client.post("users", json=user_1)
    client.post("users", json=user_2)
    client.post("users", json=user_3)
    response = client.get("users/")
    assert equal_dicts(response.json()["items"][0], user_1, ignored_keys)
    assert equal_dicts(response.json()["items"][1], user_2, ignored_keys)
    assert equal_dicts(response.json()["items"][2], user_3, ignored_keys)


@patch('users.main.create_wallet')
@patch('users.main.get_credentials')
@patch('users.main.add_user_firebase')
def test_can_retrieve_user_with_his_id(add_mock, creds_mock,
                                       create_wallet, test_db):
    add_mock.return_value = None
    create_wallet.return_value = test_wallet
    response1 = client.post("users", json=user_1)
    creds_mock.return_value = {"id": 1,
                               "role": "admin"}
    response2 = client.get("users/" + str(response1.json()["id"]))
    assert response2.status_code == 200
    assert equal_dicts(response2.json(), user_1, ignored_keys)


@patch('users.main.get_credentials')
@patch('users.main.create_wallet')
@patch('users.main.add_user_firebase')
def test_cannot_retrieve_user_with_wrong_id(add_mock, create_wallet,
                                            creds_mock, test_db):
    add_mock.return_value = None
    create_wallet.return_value = test_wallet
    client.post("users", json=user_1)
    creds_mock.return_value = {"id": 2,
                               "role": "admin"}
    response = client.get("users/" + "2")
    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}


@patch('users.main.token_login_firebase')
@patch('users.main.create_wallet')
@patch('users.main.add_user_firebase')
def test_existing_user_logs_in_correctly(add_mock, create_wallet,
                                         login_mock, test_db):
    add_mock.return_value = None
    create_wallet.return_value = test_wallet
    client.post("users", json=user_2)
    request = {"email": user_2["email"], "password": user_2["password"]}
    login_mock.return_value = {
        "token": "test_token",
        "id": 1
    }
    response = client.post("users/login", json=request)
    assert response.status_code == 200


@patch('users.util.get_user_by_email')
@patch('users.main.create_wallet')
@patch('users.main.add_user_firebase')
def test_non_existing_user_raises_exception_at_login(add_mock, create_wallet,
                                                     search_mock, test_db):
    add_mock.return_value = None
    create_wallet.return_value = test_wallet
    client.post("users", json=user_2)
    request = {"email": user_1["email"], "password": user_1["password"]}
    search_mock.return_value = None
    response = client.post("users/login", json=request)
    assert response.status_code == 404
    assert response.json() == {"detail": "No such user"}


@patch('users.main.download_image')
@patch('users.main.create_wallet')
@patch('users.main.add_user_firebase')
def test_can_retrieve_user_with_his_username(add_mock, create_wallet,
                                             download_mock, test_db):
    add_mock.return_value = None
    create_wallet.return_value = test_wallet
    download_mock.return_value = None
    create_response = client.post("users", json=user_2)
    user_string = "users?username=" + create_response.json()["username"]
    get_response = client.get(user_string)
    assert get_response.status_code == 200
    assert equal_dicts(get_response.json(), user_2, private_keys)


@patch('users.main.create_wallet')
@patch('users.main.add_user_firebase')
def test_cannot_retrieve_user_with_incorrect_username(add_mock, create_wallet,
                                                      test_db):
    add_mock.return_value = None
    create_wallet.return_value = test_wallet
    client.post("users", json=user_2)
    user_string = "users?username=" + "wrong_username"
    get_response = client.get(user_string)
    assert get_response.status_code == 404


@patch('users.main.download_image')
@patch('users.main.create_wallet')
@patch('users.main.add_user_firebase')
def test_can_retrieve_several_users_with_their_usernames(add_mock,
                                                         create_wallet,
                                                         download_mock,
                                                         test_db):
    users = [user_1, user_2, user_3]
    add_mock.return_value = None
    create_wallet.return_value = test_wallet
    download_mock.return_value = None
    for idx in range(0, 3):
        create_response = client.post("users", json=users[idx])
        user_string = "users?username=" + create_response.json()["username"]
        get_response = client.get(user_string)
        assert get_response.status_code == 200
        user = get_response.json()
        assert equal_dicts(user, users[idx], private_keys)


@patch('users.main.get_credentials')
@patch('users.main.create_wallet')
@patch('users.main.add_user_firebase')
def test_when_updating_user_data_expect_data(add_mock, create_wallet,
                                             creds_mock, test_db):
    add_mock.return_value = None
    create_wallet.return_value = test_wallet
    response_post = client.post("users", json=user_to_update)
    assert response_post.status_code == 200
    creds_mock.return_value = {"id": 1,
                               "role": "user"}
    response_patch = client.patch(
        "users/" + str(response_post.json()["id"]),
        json={
            "username": "new_username",
            "name": "new_name",
            "surname": "new_surname",
            "height": 2.0,
            "weight": 100,
            "birth_date": "23-6-2000",
            "location": "Place, AnotherPlace",
        }
    )
    assert response_patch.status_code == 200
    assert response_patch.json() == {}
    user = "users/" + str(response_post.json()["id"])
    response_get = client.get(user)
    assert response_get.status_code == 200
    assert equal_dicts(
        response_get.json(),
        {
            "surname": "new_surname",
            "username": "new_username",
            "weight": 100,
            "location": "Place, AnotherPlace",
            "name": "new_name",
            "email": "ema1il12@abcd.com",
            "height": 2.0,
            "birth_date": "23-6-2000",
            "registration_date": "23-3-2022",
            "is_athlete": True
        },
        {"id", "is_blocked"}
    )


@patch('users.main.create_wallet')
@patch('users.main.get_credentials')
@patch('users.main.add_user_firebase')
def test_when_update_height_and_weight_expect_height_and_weight(add_mock,
                                                                cred_mock,
                                                                create_wallet,
                                                                test_db):
    add_mock.return_value = None
    create_wallet.return_value = test_wallet
    response_post = client.post("users", json=user_to_update)
    assert response_post.status_code == 200
    cred_mock.return_value = {"id": 1,
                              "role": "user"}
    response_patch = client.patch(
        "users/" + str(response_post.json()["id"]),
        json={
            "height": 2.0,
            "weight": 100,
        }
    )
    assert response_patch.status_code == 200
    assert response_patch.json() == {}
    user = "users/" + str(response_post.json()["id"])
    response_get = client.get(user)
    assert response_get.status_code == 200
    assert equal_dicts(
        response_get.json(),
        {
            "surname": "old_surname",
            "username": "old_username",
            "weight": 100,
            "location": "Cordoba, Cordoba",
            "name": "old_name",
            "email": "ema1il12@abcd.com",
            "height": 2.0,
            "birth_date": "23-4-1999",
            "registration_date": "23-3-2022",
            "is_athlete": True
        },
        {"id", "is_blocked"}
    )


@patch('users.main.get_credentials')
def test_when_updating_non_existent_user_id_expect_not_found(creds_mock,
                                                             test_db):
    creds_mock.return_value = {"id": 1,
                               "role": "user"}
    response_patch = client.patch("users/1", json={"height": 2.0})
    assert response_patch.status_code == 404


@patch('users.main.create_wallet')
@patch('users.util.get_auth_header')
@patch('users.main.add_user_firebase')
def test_cant_change_status_without_token(add_mock, auth_mock,
                                          create_wallet, test_db):
    add_mock.return_value = None
    create_wallet.return_value = test_wallet
    create_response = client.post("users", json=user_2)
    auth_mock.return_value = None
    user = "users/status/" + str(create_response.json()["id"])
    patch_response = client.patch(user)
    assert patch_response.status_code == 403


@patch('users.main.create_wallet')
@patch('users.main.get_credentials')
@patch('users.main.add_user_firebase')
def test_cant_change_status_as_user(add_mock, creds_mock,
                                    create_wallet, test_db):
    add_mock.return_value = None
    create_wallet.return_value = test_wallet
    create_response = client.post("users", json=user_2)
    assert create_response.status_code == 200
    url = "users/status/" + str(create_response.json()["id"])
    creds_mock.return_value = {"id": 1,
                               "role": "user"}
    patch_response = client.patch(url)
    assert patch_response.status_code == 403


@patch('users.main.create_wallet')
@patch('users.main.get_credentials')
@patch('users.main.add_user_firebase')
def test_can_change_status_to_blocked_and_back_again_as_admin(add_mock,
                                                              creds_mock,
                                                              create_wallet,
                                                              test_db):
    blocked_user = user_1 | {"is_blocked": True}
    unblocked_user = user_1 | {"is_blocked": False}
    add_mock.return_value = None
    create_wallet.return_value = test_wallet
    create_response = client.post("users", json=user_1)
    patch_url = "users/status/" + str(create_response.json()["id"])
    get_url = "users/" + str(create_response.json()["id"])
    creds_mock.return_value = {"id": 1,
                               "role": "admin"}
    patch_response = client.patch(patch_url)
    get_response = client.get(get_url)
    assert patch_response.status_code == 200
    assert equal_dicts(get_response.json(), blocked_user, {"id", "password"})
    client.patch(patch_url)
    get_response = client.get(get_url)
    assert patch_response.status_code == 200
    assert equal_dicts(get_response.json(), unblocked_user, {"id", "password"})


@patch('users.main.create_wallet')
@patch('users.main.token_login_firebase')
@patch('users.main.add_user_firebase')
def test_pagination_with_ten_users_returns_correct_values(add_mock,
                                                          creds_mock,
                                                          create_wallet,
                                                          test_db):
    add_mock.return_value = None
    create_wallet.return_value = test_wallet
    for idx in range(10):
        email = {"email": "user_" + str(idx)}
        username = {"username": "user_" + str(idx)}
        new_user = user_template_no_email | email | username
        res = client.post("users", json=new_user)
        assert res.status_code == 200
    creds_mock.return_value = {"id": 1,
                               "role": "user"}
    response = client.get("users")
    correct_values = {"total": 10, "page": 1, "size": 10, "pages": 1}
    assert equal_dicts(response.json(), correct_values, {"items"})


@patch('users.main.create_wallet')
@patch('users.main.token_login_firebase')
@patch('users.main.add_user_firebase')
def test_pagination_with_ten_users_and_two_pages_correct_values(add_mock,
                                                                creds_mock,
                                                                create_wallet,
                                                                test_db):
    add_mock.return_value = None
    create_wallet.return_value = test_wallet
    for idx in range(10):
        email = {"email": "user_" + str(idx)}
        username = {"username": "user_" + str(idx)}
        new_user = user_template_no_email | email | username
        client.post("users", json=new_user)
    creds_mock.return_value = {"id": 1,
                               "role": "user"}
    response = client.get("users?limit=5")
    correct_values = {"total": 10, "page": 1, "size": 5, "pages": 2}
    assert equal_dicts(response.json(), correct_values, {"items"})
    response = client.get("users?limit=5&offset=5")
    correct_values = {"total": 10, "page": 2, "size": 5, "pages": 2}
    assert equal_dicts(response.json(), correct_values, {"items"})


@patch('users.main.create_wallet')
@patch('users.main.token_login_firebase')
@patch('users.main.add_user_firebase')
def test_pagination_with_ten_users_and_three_pages(add_mock,
                                                   creds_mock,
                                                   create_wallet,
                                                   test_db):
    add_mock.return_value = None
    create_wallet.return_value = test_wallet
    for idx in range(10):
        email = {"email": "user_" + str(idx)}
        username = {"username": "user_" + str(idx)}
        new_user = user_template_no_email | email | username
        client.post("users", json=new_user)
    creds_mock.return_value = {"id": 1,
                               "role": "user"}
    for idx in range(4):
        response = client.get("users?limit=" + str(3)
                              + "&offset=" + str(3 * idx))
        correct_values = {"total": 10, "page": 1 + idx, "size": 3, "pages": 4}
        if idx == 3:
            correct_values = {"total": 10, "page": 1 + idx,
                              "size": 10 % 3, "pages": 4}
        assert equal_dicts(response.json(), correct_values, {"items"})


def test_when_checking_healthcheck_expect_uptime_greater_than_zero():
    response = client.get("/users/healthcheck/")
    assert response.status_code == 200, response.json()
    assert_that(response.json()["uptime"], greater_than(0))


def test_when_getting_swagger_ui_expect_200():
    response = client.get(DOCUMENTATION_URI)
    assert response.status_code == 200, response.json()


def test_when_getting_openapi_doc_expect_200():
    response = client.get(DOCUMENTATION_URI + "openapi.json")
    assert response.status_code == 200, response.json()

# pylint: disable= missing-module-docstring, missing-function-docstring
# pylint: disable= unused-argument, redefined-outer-name
import pytest
import jwt
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from users.auth.auth_operations import encode_token
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


TOKEN = encode_token("admin", "magicword")
headers = {"Authorization": f"Bearer {TOKEN}"}


# to build and tear down test database and firebase authentication
@pytest.fixture
def test_db():
    Base.metadata.create_all(bind=engine)
    yield
    for email in user_emails:
        client.delete("users" + "?email=" + email, headers=headers)
    Base.metadata.drop_all(bind=engine)
    user_emails.clear()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

user_emails = []

ignored_keys = {"id", "password", "is_blocked"}


def test_database_empty_at_start(test_db):
    response = client.get("users")
    assert response.status_code == 200
    assert response.json()["items"] == []


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
    "is_athlete": True
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
    "is_athlete": False
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
    "is_athlete": True
}

user_to_update = {
    "password": "pass22word1",
    "username": "old_username",
    "email": "ema1il12@abcd.com",
    "name": "old_name",
    "surname": "old_surname",
    "height": 1.1,
    "weight": 800,
    "birth_date": "23-4-1999",
    "location": "Cordoba, Cordoba",
    "registration_date": "23-3-2022",
    "is_athlete": True
}


def equal_dicts(dict1, dict2, ignore_keys):
    d1_filtered = {k: v for k, v in dict1.items() if k not in ignore_keys}
    d2_filtered = {k: v for k, v in dict2.items() if k not in ignore_keys}
    return d1_filtered == d2_filtered


def test_user_stored_correctly(test_db):
    response = client.post("users", json=user_1)
    user_emails.append(user_1["email"])
    assert response.status_code == 200
    assert equal_dicts(response.json(), user_1, ignored_keys)


def test_several_users_stored_correctly(test_db):
    response1 = client.post("users", json=user_1)
    response2 = client.post("users", json=user_2)
    user_emails.append(user_1["email"])
    user_emails.append(user_2["email"])
    assert response1.status_code == 200
    assert response2.status_code == 200
    assert equal_dicts(response1.json(), user_1, ignored_keys)
    assert equal_dicts(response2.json(), user_2, ignored_keys)


def test_user_that_wasnt_stored_isnt_retrieved(test_db):
    client.post("users", json=user_1)
    client.post("users", json=user_2)
    user_emails.append(user_1["email"])
    user_emails.append(user_2["email"])
    response = client.get("users/", headers=headers)
    assert response.status_code == 200
    user1 = response.json()["items"][0]
    user2 = response.json()["items"][1]
    assert (equal_dicts(user1, user_3, ignored_keys)) is False
    assert (equal_dicts(user2, user_3, ignored_keys)) is False


# shouldn't assume an order for results
def test_can_get_several_user_details(test_db):
    client.post("users", json=user_1)
    client.post("users", json=user_2)
    client.post("users", json=user_3)
    user_emails.append(user_1["email"])
    user_emails.append(user_2["email"])
    user_emails.append(user_3["email"])
    response = client.get("users/", headers=headers)
    assert equal_dicts(response.json()["items"][0], user_1, ignored_keys)
    assert equal_dicts(response.json()["items"][1], user_2, ignored_keys)
    assert equal_dicts(response.json()["items"][2], user_3, ignored_keys)


def test_can_retrieve_user_with_his_id(test_db):
    response1 = client.post("users", json=user_1)
    user_emails.append(user_1["email"])
    response2 = client.get("users/" + response1.json()["id"], headers=headers)
    assert response2.status_code == 200
    assert equal_dicts(response2.json(), user_1, ignored_keys)


def test_cannot_retrieve_user_with_wrong_id(test_db):
    client.post("users", json=user_1)
    user_emails.append(user_1["email"])
    response = client.get("users/" + "fake_id", headers=headers)
    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}


def test_existing_user_logs_in_correctly(test_db):
    client.post("users", json=user_2)
    user_emails.append(user_2["email"])
    request = {"email": user_2["email"], "password": user_2["password"]}
    response = client.post("users/login", json=request)
    assert response.status_code == 200


def test_non_existing_user_raises_exception_at_login(test_db):
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
    assert login_response.status_code == 200
    assert dec_token == {"role": "user", "id": create_response.json()["id"]}


def test_can_retrieve_user_with_his_username(test_db):
    create_response = client.post("users", json=user_2)
    user_emails.append(user_2["email"])
    user_string = "users?username=" + create_response.json()["username"]
    get_response = client.get(user_string, headers=headers)
    assert get_response.status_code == 200
    assert equal_dicts(get_response.json()["items"][0], user_2, ignored_keys)


def test_cannot_retrieve_user_with_incorrect_username(test_db):
    client.post("users", json=user_2)
    user_emails.append(user_2["email"])
    user_string = "users?username=" + "wrong_username"
    get_response = client.get(user_string, headers=headers)
    assert get_response.status_code == 404


def test_can_retrieve_several_users_with_their_usernames(test_db):
    users = [user_1, user_2, user_3]
    for idx in range(3):
        create_response = client.post("users", json=users[idx])
        user_emails.append(users[idx]["email"])
        user_string = "users?username=" + create_response.json()["username"]
        get_response = client.get(user_string, headers=headers)
        assert get_response.status_code == 200
        user = get_response.json()["items"][0]
        assert equal_dicts(user, users[idx], ignored_keys)


def test_when_updating_user_data_expect_data(test_db):
    response_post = client.post("users", json=user_to_update)
    user_emails.append(user_to_update["email"])
    assert response_post.status_code == 200
    response_patch = client.patch(
        "users/" + response_post.json()["id"],
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
    assert response_patch.status_code == 204
    assert response_patch.json() == {}
    user = "users/" + response_post.json()["id"]
    response_get = client.get(user, headers=headers)
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


def test_when_update_user_height_and_weight_expect_height_and_weight(test_db):
    response_post = client.post("users", json=user_to_update)
    user_emails.append(user_to_update["email"])
    assert response_post.status_code == 200
    response_patch = client.patch(
        "users/" + response_post.json()["id"],
        json={
            "height": 2.0,
            "weight": 100,
        }
    )
    assert response_patch.status_code == 204
    assert response_patch.json() == {}
    user = "users/" + response_post.json()["id"]
    response_get = client.get(user, headers=headers)
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


def test_when_update_user_id_banana_expect_not_found(test_db):
    response_patch = client.patch("users/banana", json={"height": 2.0})
    assert response_patch.status_code == 404


def test_cant_change_status_without_token(test_db):
    create_response = client.post("users", json=user_2)
    user_emails.append(user_2["email"])
    user = "users/status/" + create_response.json()["id"]
    patch_response = client.patch(user)
    assert patch_response.status_code == 403


def test_cant_change_status_as_user(test_db):
    _token = encode_token("user", "magicword")
    user_token = {"Authorization": f"Bearer {_token}"}
    create_response = client.post("users", json=user_2)
    user_emails.append(user_2["email"])
    url = "users/status/" + create_response.json()["id"]
    patch_response = client.patch(url, headers=user_token)
    assert patch_response.status_code == 403


def test_can_change_status_to_blocked_and_back_again_as_admin(test_db):
    blocked_user = user_1 | {"is_blocked": True}
    unblocked_user = user_1 | {"is_blocked": False}
    create_response = client.post("users", json=user_1)
    user_emails.append(user_1["email"])
    patch_url = "users/status/" + create_response.json()["id"]
    get_url = "users/" + create_response.json()["id"]
    patch_response = client.patch(patch_url, headers=headers)
    get_response = client.get(get_url, headers=headers)
    assert patch_response.status_code == 200
    assert equal_dicts(get_response.json(), blocked_user, {"id", "password"})
    client.patch(patch_url, headers=headers)
    get_response = client.get(get_url, headers=headers)
    assert patch_response.status_code == 200
    assert equal_dicts(get_response.json(), unblocked_user, {"id", "password"})

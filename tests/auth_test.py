# pylint: disable= missing-module-docstring, missing-function-docstring
from fastapi.testclient import TestClient

from users.auth.auth_operations import encode_token
from users.main import app

client = TestClient(app)


def test_not_authenticated_if_theres_no_token():
    post_response = client.post("validation-test/")
    assert post_response.status_code == 403
    assert post_response.json() == {"detail": "Not authenticated"}


def test_not_authenticated_if_token_uses_wrong_scheme():
    token = encode_token("user", "wont-work")
    headers = {"Authorization": token}
    post_response = client.post("validation-test/", headers=headers)
    assert post_response.status_code == 403
    assert post_response.json() == {"detail": "Not authenticated"}


def test_incorrect_role_and_incorrect_id_raises_exception():
    token = encode_token("user", "wont-work")
    headers = {"Authorization": f"Bearer {token}"}
    post_response = client.post("validation-test/", headers=headers)
    assert post_response.status_code == 403
    assert post_response.json() == {"detail": "Invalid credentials"}


def test_incorrect_role_correct_id_raises_exception():
    token = encode_token("user", "magicword")
    headers = {"Authorization": f"Bearer {token}"}
    post_response = client.post("validation-test/", headers=headers)
    assert post_response.status_code == 403
    assert post_response.json() == {"detail": "Invalid credentials"}


def test_correct_role_but_incorrect_id_raises_exception():
    token = encode_token("admin", "wont-work")
    headers = {"Authorization": f"Bearer {token}"}
    post_response = client.post("validation-test/", headers=headers)
    assert post_response.status_code == 403
    assert post_response.json() == {"detail": "Invalid credentials"}


def test_correct_role_and_id_allows_access():
    token = encode_token("admin", "magicword")
    headers = {"Authorization": f"Bearer {token}"}
    post_response = client.post("validation-test/", headers=headers)
    assert post_response.status_code == 200

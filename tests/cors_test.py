# pylint: disable= missing-module-docstring, missing-function-docstring
import re
from fastapi.testclient import TestClient

from users.main import ORIGIN_REGEX
from users.main import app

COMPILED_REGEX = re.compile(ORIGIN_REGEX)

client = TestClient(app)

HEADERS = {
    "authority": "users-ingress-taller2-marianocinalli.cloud.okteto.net",
    "accept": "/",
    "accept-language": "en-US,en;q=0.9,es;q=0.8,pt;q=0.7,la;q=0.6",
    "access-control-request-headers": "authorization",
    "access-control-request-method": "patch",
    "cache-control": "no-cache",
    "origin": "https://fiufit-backoffice-6kwbytb6g-fiufitgrupo5-gmailcom"
    ".vercel.app",
    "pragma": "no-cache",
    "referer": "http://localhost:3000/",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "cross-site",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    "(KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
}


def test_when_asking_cors_is_available_for_patch_expect_200():
    response = client.options("users", headers=HEADERS)
    assert response.status_code == 200


def test_when_asking_cors_is_available_for_patch_uppercase_expect_200():
    method_override = {"access-control-request-method": "PATCH"}
    response = client.options("users", headers=HEADERS | method_override)
    assert response.status_code == 200


def test_when_asking_cors_is_available_for_post_expect_200():
    method_override = {"access-control-request-method": "post"}
    response = client.options("users", headers=HEADERS | method_override)
    assert response.status_code == 200


def test_when_asking_cors_is_available_for_post_uppercase_expect_200():
    method_override = {"access-control-request-method": "POST"}
    response = client.options("users", headers=HEADERS | method_override)
    assert response.status_code == 200


def test_when_asking_cors_is_available_for_banana_expect_400():
    method_override = {"access-control-request-method": "banana"}
    response = client.options("users", headers=HEADERS | method_override)
    assert response.status_code == 400


def test_when_asking_cors_is_available_origin_localhost_expect_200():
    method_override = {"origin": "localhost"}
    response = client.options("users", headers=HEADERS | method_override)
    assert response.status_code == 200


def test_when_asking_cors_is_available_origin_local_expect_200():
    method_override = {"origin": "localhost"}
    response = client.options("users", headers=HEADERS | method_override)
    assert response.status_code == 200


def test_when_asking_cors_is_available_origin_apple_expect_200():
    method_override = {"origin": "apple"}
    response = client.options("users", headers=HEADERS | method_override)
    assert response.status_code == 400


def test_origin_regex_should_match_vercel_url():
    assert COMPILED_REGEX.fullmatch(
        "https://fiufit-backoffice-6kwbytb6g-fiufitgrupo5-gmailcom.vercel.app"
    )


def test_origin_regex_should_match_vercel_url_with_path():
    assert COMPILED_REGEX.fullmatch(
        "https://fiufit-backoffice-6kwbytb6g-fiufitgrupo5-gmailcom.vercel.app"
        "/users/1/trainings"
    )


def test_origin_regex_should_match_vercel_dev_url():
    assert COMPILED_REGEX.fullmatch(
        "https://fiufit-backoffice.vercel.app/"
    )


def test_origin_regex_should_match_localhost_url():
    assert COMPILED_REGEX.fullmatch("http://localhost:3000")


def test_origin_regex_should_match_localhost_url_with_path():
    assert COMPILED_REGEX.fullmatch("http://localhost:3000/goals/1")


def test_origin_regex_should_match_local_url():
    assert COMPILED_REGEX.fullmatch("http://local:3000")

# pylint: disable= missing-module-docstring, missing-function-docstring
from re import compile
from users.main import ORIGIN_REGEX

COMPILED_REGEX = compile(ORIGIN_REGEX)


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

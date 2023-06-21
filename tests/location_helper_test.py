# pylint: disable= missing-module-docstring, missing-function-docstring
from unittest.mock import ANY, MagicMock, patch
from fastapi import HTTPException

from pytest import raises
from users.location_helper import get_coordinates, get_user_ids, save_location


@patch("users.location_helper.edit_location")
@patch("users.location_helper.get_mongodb_connection")
def test_when_saving_location_for_athlete_expect_no_call(
    mock_get_mongodb_connection: MagicMock,
    mock_edit_location: MagicMock,
):
    config = MagicMock(**{"mongo.enabled": True})
    save_location("url", True, 1, (1.1, 1.2), config)
    mock_get_mongodb_connection.assert_not_called()
    mock_edit_location.assert_not_called()


@patch("users.location_helper.edit_location")
@patch("users.location_helper.get_mongodb_connection")
def test_when_saving_location_for_trainer_expect_call(
    mock_get_mongodb_connection: MagicMock,
    mock_edit_location: MagicMock,
):
    config = MagicMock(**{"mongo.enabled": True})
    save_location("url", False, 1, (1.1, 1.2), config)
    mock_get_mongodb_connection.assert_called_once_with("url")
    mock_edit_location.assert_called_once_with(ANY, 1, (1.1, 1.2))


@patch("users.location_helper.edit_location")
@patch("users.location_helper.get_mongodb_connection")
def test_when_coordinates_disabled_expect_false(
    mock_get_mongodb_connection: MagicMock,
    mock_edit_location: MagicMock,
):
    config = MagicMock(**{"mongo.enabled": False})
    save_location("url", False, 1, (1.1, 1.2), config)
    mock_get_mongodb_connection.assert_not_called()
    mock_edit_location.assert_not_called()


def test_when_coordinates_are_none_expect_none():
    assert get_coordinates(None, None) is None


def test_when_latitude_is_none_expect_error():
    with raises(HTTPException):
        get_coordinates(None, 1.2)


def test_when_longitude_is_none_expect_error():
    with raises(HTTPException):
        get_coordinates(1.1, None)


def test_when_coordinates_are_numbers_expect_tuple():
    assert get_coordinates(1.1, 1.2) == (1.1, 1.2)


def test_when_list_has_documents_expect_list_of_ids():
    assert get_user_ids([{'user_id': 1}, {'user_id': 2}]) == [1, 2]


def test_when_list_is_empty_expect_empty_list():
    assert not get_user_ids([])

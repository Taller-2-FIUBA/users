# pylint: disable= missing-module-docstring, missing-function-docstring
from unittest.mock import ANY, MagicMock, patch
from users.location_helper import save_location


@patch("users.location_helper.add_location")
@patch("users.location_helper.get_mongodb_connection")
def test_when_saving_location_for_athlete_expect_no_call(
    mock_get_mongodb_connection: MagicMock,
    mock_add_location: MagicMock,
):
    config = MagicMock(**{"coordinates.enabled": True})
    save_location("url", True, 1, (1.1, 1.2), config)
    mock_get_mongodb_connection.assert_not_called()
    mock_add_location.assert_not_called()


@patch("users.location_helper.add_location")
@patch("users.location_helper.get_mongodb_connection")
def test_when_saving_location_for_trainer_expect_call(
    mock_get_mongodb_connection: MagicMock,
    mock_add_location: MagicMock,
):
    config = MagicMock(**{"coordinates.enabled": True})
    save_location("url", False, 1, (1.1, 1.2), config)
    mock_get_mongodb_connection.assert_called_once_with("url")
    mock_add_location.assert_called_once_with(ANY, 1, (1.1, 1.2))


@patch("users.location_helper.add_location")
@patch("users.location_helper.get_mongodb_connection")
def test_when_coordinates_disabled_expect_false(
    mock_get_mongodb_connection: MagicMock,
    mock_add_location: MagicMock,
):
    config = MagicMock(**{"coordinates.enabled": False})
    save_location("url", False, 1, (1.1, 1.2), config)
    mock_get_mongodb_connection.assert_not_called()
    mock_add_location.assert_not_called()

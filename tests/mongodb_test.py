# pylint: disable= missing-module-docstring, missing-function-docstring
from unittest.mock import MagicMock, patch

from pymongo import GEOSPHERE

from users.mongodb import (
    edit_location,
    get_mongo_url,
    get_mongodb_connection,
    get_users_within,
    initialize,
)


def test_building_url_with_config():
    config = MagicMock(**{
        "mongo.driver": "mongodb",
        "mongo.user": "fiufit",
        "mongo.password": "fiufit",
        "mongo.host": "cluster.mongodb.net",
        "mongo.database": "fiufit",
    })
    assert get_mongo_url(config) ==\
        "mongodb://fiufit:fiufit@cluster.mongodb.net/fiufit"


def test_when_calling_initialize_expect_calls():
    create_index = MagicMock()
    connection = MagicMock(**{
        "fiufit.user_location.create_index": create_index
    })
    initialize(connection)
    create_index.assert_called_once_with([("location", GEOSPHERE)])


@patch("users.mongodb.MongoClient")
def test_when_creating_connection_expect_call(expected_connection: MagicMock):
    get_mongodb_connection("connection_string")
    expected_connection.assert_called_once_with("connection_string")


def test_when_editing_location_expect_calls():
    replace_one = MagicMock()
    connection = MagicMock(**{
        "fiufit.user_location.replace_one": replace_one
    })
    expected_filter = {"user_id": 1}
    expected_document = {"user_id": 1, "location": (1.1, 1.2)}
    edit_location(connection, 1, (1.1, 1.2))
    replace_one.assert_called_once_with(
        expected_filter, expected_document, upsert=True
    )


def test_when_getting_users_within_expect_calls():
    expected_documents = [{'user_id': 1}, {'user_id': 2}]
    find = MagicMock(return_value=expected_documents)
    connection = MagicMock(**{
        "fiufit.user_location.find": find
    })
    expected_query = {
        "location": {
            "$near": {
                "$geometry": {
                    "type": "Point",
                    "coordinates": (1.1, 1.2)
                },
                "$maxDistance": 1000
            }
        }
    }
    assert get_users_within(connection, (1.1, 1.2), 1000) == expected_documents
    find.assert_called_once_with(
        expected_query, projection={'_id': False, 'user_id': True}
    )


def test_when_getting_users_within_returns_none_expect_empty_list():
    find = MagicMock(return_value=[])
    connection = MagicMock(**{
        "fiufit.user_location.find": find
    })
    expected_query = {
        "location": {
            "$near": {
                "$geometry": {
                    "type": "Point",
                    "coordinates": (1.3, 1.4)
                },
                "$maxDistance": 10
            }
        }
    }
    assert not get_users_within(connection, (1.3, 1.4), 10)
    find.assert_called_once_with(
        expected_query, projection={'_id': False, 'user_id': True}
    )

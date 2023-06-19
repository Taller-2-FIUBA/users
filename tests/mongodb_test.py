# pylint: disable= missing-module-docstring, missing-function-docstring
from unittest.mock import MagicMock, patch
from bson import SON

from pymongo import GEO2D

from users.mongodb import (
    add_location,
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
    return get_mongo_url(config) ==\
        "mongodb://fiufit:fiufit@mongodb-release/fiufit"


def test_when_calling_initialize_expect_calls():
    create_index = MagicMock()
    connection = MagicMock(**{
        "fiufit.user_location.create_index": create_index
    })
    initialize(connection)
    create_index.assert_called_once_with([("location", GEO2D)])


@patch("users.mongodb.MongoClient")
def test_when_creating_connection_expect_call(expected_connection: MagicMock):
    get_mongodb_connection("connection_string")
    expected_connection.assert_called_once_with("connection_string")


def test_when_adding_location_expect_calls():
    insert_one = MagicMock()
    connection = MagicMock(**{
        "fiufit.user_location.insert_one": insert_one
    })
    add_location(connection, 1, (1.1, 1.2))
    insert_one.assert_called_once_with({"user_id": 1, "location": (1.1, 1.2)})


def test_when_editing_location_expect_calls():
    replace_one = MagicMock()
    connection = MagicMock(**{
        "fiufit.user_location.replace_one": replace_one
    })
    expected_filter = {"user_id": 1}
    expected_document = {"user_id": 1, "location": (1.1, 1.2)}
    edit_location(connection, 1, (1.1, 1.2))
    replace_one.assert_called_once_with(
        expected_filter, expected_document, True
    )


def test_when_getting_users_within_expect_calls():
    find = MagicMock()
    connection = MagicMock(**{
        "fiufit.user_location.find": find
    })
    expected_query = {
        "loc": SON([("$near", (1.1, 1.2)), ("$maxDistance", 1000)])
    }
    get_users_within(connection, (1.1, 1.2), 1000)
    find.assert_called_once_with(expected_query)

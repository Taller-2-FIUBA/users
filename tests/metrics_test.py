# pylint: disable= missing-module-docstring, missing-function-docstring
from unittest.mock import ANY, MagicMock, patch
from users.metrics import get_redis_connection, queue


@patch("users.metrics.BlockingConnectionPool")
@patch("users.metrics.Redis")
def test_when_creating_connection_expect_parameters(
    redis_mock: MagicMock,
    blocking_connection_pool_mock: MagicMock,
):
    expected_pool = MagicMock()
    blocking_connection_pool_mock.return_value = expected_pool
    expected_client = MagicMock()
    redis_mock.return_value = expected_client
    assert get_redis_connection(
        MagicMock(**{"redis.host": "localhost", "redis.port": 6379})
    ) == expected_client
    blocking_connection_pool_mock.assert_called_once_with(
        host='localhost', port=6379, db=0, timeout=10
    )
    redis_mock.assert_called_once_with(connection_pool=expected_pool)


@patch("users.metrics.get_redis_connection")
def test_when_name_and_label_are_defined_expect_them_in_message(
    get_redis_connection_mock: MagicMock,
):
    expected_config = MagicMock()
    expected_client = MagicMock()
    expected_client.rpush = MagicMock()
    get_redis_connection_mock.return_value = expected_client
    queue(expected_config, "banana", "tomato")
    get_redis_connection_mock.assert_called_once_with(expected_config)
    expected_client.rpush.assert_called_once_with(
        "metrics",
        {
            "metric": "banana",
            "value": 1,
            "label": "tomato",
            "date": ANY,
        }
    )


@patch("users.metrics.get_redis_connection")
def test_when_label_is_none_expect_no_key(
    get_redis_connection_mock: MagicMock,
):
    expected_config = MagicMock()
    expected_client = MagicMock()
    expected_client.rpush = MagicMock()
    get_redis_connection_mock.return_value = expected_client
    queue(expected_config, "banana", None)
    get_redis_connection_mock.assert_called_once_with(expected_config)
    expected_client.rpush.assert_called_once_with(
        "metrics",
        {
            "metric": "banana",
            "value": 1,
            "date": ANY,
        }
    )


@patch("users.metrics.get_redis_connection")
def test_when_redis_raises_expect_no_error(
    get_redis_connection_mock: MagicMock,
):
    get_redis_connection_mock.side_effect = Exception
    queue(MagicMock(), "banana", None)

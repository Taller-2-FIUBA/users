# pylint: disable= missing-module-docstring, missing-function-docstring
from os import environ
from unittest.mock import patch
from environ import to_config
from users.config import AppConfig


@patch.dict(environ, {}, clear=True)
def test_when_environment_is_empty_expect_9001_prometheus_port():
    cnf = to_config(AppConfig)
    assert cnf.prometheus_port == 9001


@patch.dict(environ, {}, clear=True)
def test_when_environment_is_empty_expect_warning_log_level():
    cnf = to_config(AppConfig)
    assert cnf.log_level == "WARNING"


@patch.dict(environ, {"USERS_PROMETHEUS_PORT": "9004"}, clear=True)
def test_when_environment_has_prometheus_port_9004_expect_9004():
    cnf = to_config(AppConfig)
    assert cnf.prometheus_port == 9004


@patch.dict(environ, {"USERS_LOG_LEVEL": "DEBUG"}, clear=True)
def test_when_environment_debug_log_level_expect_debug():
    cnf = to_config(AppConfig)
    assert cnf.log_level == "DEBUG"


@patch.dict(environ, {"USERS_DB_DRIVER": "postgresql"}, clear=True)
def test_when_environment_db_driver_expect_postgresql():
    cnf = to_config(AppConfig)
    assert cnf.db.driver == "postgresql"


@patch.dict(environ, {"USERS_DB_PASSWORD": "secret"}, clear=True)
def test_when_environment_db_password_expect_secret():
    cnf = to_config(AppConfig)
    assert cnf.db.password == "secret"


@patch.dict(environ, {"USERS_DB_USER": "backend"}, clear=True)
def test_when_environment_db_user_expect_backend():
    cnf = to_config(AppConfig)
    assert cnf.db.user == "backend"


@patch.dict(environ, {"USERS_DB_HOST": "localhost"}, clear=True)
def test_when_environment_db_host_expect_localhost():
    cnf = to_config(AppConfig)
    assert cnf.db.host == "localhost"


@patch.dict(environ, {"USERS_DB_PORT": "5432"}, clear=True)
def test_when_environment_db_port_expect_5432():
    cnf = to_config(AppConfig)
    assert cnf.db.port == 5432


@patch.dict(environ, {"USERS_DB_DATABASE": "fiufit"}, clear=True)
def test_when_environment_db_database_expect_fiufit():
    cnf = to_config(AppConfig)
    assert cnf.db.database == "fiufit"


@patch.dict(environ, {"USERS_AUTH_HOST": "auth-svc"}, clear=True)
def test_when_environment_auth_host_expect_auth_svc():
    cnf = to_config(AppConfig)
    assert cnf.auth.host == "auth-svc"


@patch.dict(environ, clear=True)
def test_when_environment_payments_host_expect_localhost():
    cnf = to_config(AppConfig)
    assert cnf.payments.host == "localhost:8020"


@patch.dict(environ, {"USERS_PAYMENTS_HOST": "payment-svc"}, clear=True)
def test_when_environment_payments_host_expect_payments_svc():
    cnf = to_config(AppConfig)
    assert cnf.payments.host == "payment-svc"


@patch.dict(environ, clear=True)
def test_when_mongo_enabled_env_variable_is_not_set_expect_true():
    cnf = to_config(AppConfig)
    assert cnf.mongo.enabled


@patch.dict(environ, {"USERS_MONGO_ENABLED": "False"}, clear=True)
def test_when_mongo_enabled_env_variable_is_false_expect_false():
    cnf = to_config(AppConfig)
    assert not cnf.mongo.enabled


@patch.dict(environ, clear=True)
def test_when_environment_mongo_driver_expect_mongodb():
    cnf = to_config(AppConfig)
    assert cnf.mongo.driver == "mongodb"


@patch.dict(environ, {"USERS_MONGO_DRIVER": "mongodb+srv"}, clear=True)
def test_when_environment_mongo_driver_expect_mongodb_srv():
    cnf = to_config(AppConfig)
    assert cnf.mongo.driver == "mongodb+srv"


@patch.dict(environ, clear=True)
def test_when_environment_mongo_user_expect_fiufit():
    cnf = to_config(AppConfig)
    assert cnf.mongo.user == "fiufit"


@patch.dict(environ, {"USERS_MONGO_USER": "fiufitmongo"}, clear=True)
def test_when_environment_mongo_user_expect_fiufitmongo():
    cnf = to_config(AppConfig)
    assert cnf.mongo.user == "fiufitmongo"


@patch.dict(environ, clear=True)
def test_when_environment_mongo_password_expect_fiufit():
    cnf = to_config(AppConfig)
    assert cnf.mongo.password == "fiufit"


@patch.dict(environ, {"USERS_MONGO_PASSWORD": "secure"}, clear=True)
def test_when_environment_mongo_password_expect_secure():
    cnf = to_config(AppConfig)
    assert cnf.mongo.password == "secure"


@patch.dict(environ, clear=True)
def test_when_environment_mongo_host_expect_cluster_mongodb_net():
    cnf = to_config(AppConfig)
    assert cnf.mongo.host == "cluster.mongodb.net"


@patch.dict(environ, {"USERS_MONGO_HOST": "mongodb-release"}, clear=True)
def test_when_environment_mongo_host_expect_mongodb_release():
    cnf = to_config(AppConfig)
    assert cnf.mongo.host == "mongodb-release"


@patch.dict(environ, clear=True)
def test_when_environment_mongo_database_expect_fiufit():
    cnf = to_config(AppConfig)
    assert cnf.mongo.database == "fiufit"


@patch.dict(environ, {"USERS_MONGO_DATABASE": "locations"}, clear=True)
def test_when_environment_mongo_database_expect_locations():
    cnf = to_config(AppConfig)
    assert cnf.mongo.database == "locations"


@patch.dict(environ, {}, clear=True)
def test_when_environment_is_empty_expect_redis_host_localhost():
    cnf = to_config(AppConfig)
    assert cnf.redis.host == "localhost"


@patch.dict(environ, {"USERS_REDIS_HOST": "banana"}, clear=True)
def test_when_environment_redis_host_is_banana_expect_banana():
    cnf = to_config(AppConfig)
    assert cnf.redis.host == "banana"


@patch.dict(environ, {}, clear=True)
def test_when_environment_is_empty_expect_redis_port_6379():
    cnf = to_config(AppConfig)
    assert cnf.redis.port == 6379


@patch.dict(environ, {"USERS_REDIS_PORT": "6677"}, clear=True)
def test_when_environment_redis_port_is_6677_expect_6677():
    cnf = to_config(AppConfig)
    assert cnf.redis.port == 6677

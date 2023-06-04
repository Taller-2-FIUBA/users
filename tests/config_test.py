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


@patch.dict(environ, {}, clear=True)
def test_when_environment_sentry_enabled_is_not_set_expect_false():
    cnf = to_config(AppConfig)
    assert not cnf.sentry.enabled


@patch.dict(
    environ, {"USERS_SENTRY_ENABLED": "true"}, clear=True
)
def test_when_environment_sentry_enabled_is_true_expect_true():
    cnf = to_config(AppConfig)
    assert cnf.sentry.enabled


@patch.dict(environ, {}, clear=True)
def test_when_sentry_dsn_is_empty_expect_localhost():
    cnf = to_config(AppConfig)
    assert cnf.sentry.dsn == "https://token@sentry.ingest.localhost"


@patch.dict(
    environ,
    {"USERS_SENTRY_DSN": "https://wf313c@24t2tg2g.ingest.sentry.io/33433"},
    clear=True
)
def test_when_sentry_dsn_has_sentry_url_expect_it():
    cnf = to_config(AppConfig)
    assert cnf.sentry.dsn == "https://wf313c@24t2tg2g.ingest.sentry.io/33433"


@patch.dict(environ, clear=True)
def test_when_environment_payments_host_expect_localhost():
    cnf = to_config(AppConfig)
    assert cnf.payments.host == "localhost:8020"


@patch.dict(environ, {"USERS_PAYMENTS_HOST": "payment-svc"}, clear=True)
def test_when_environment_payments_host_expect_payments_svc():
    cnf = to_config(AppConfig)
    assert cnf.payments.host == "payment-svc"

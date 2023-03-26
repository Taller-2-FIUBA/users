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

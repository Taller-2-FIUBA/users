#!/usr/bin/env python
# pylint: disable= missing-module-docstring
from setuptools import setup

setup(
    name='users',
    version='1.0',
    description='Service to interact with users.',
    author='Grupo 5',
    packages=[''],
    include_package_data=True,
    exclude_package_data={'': ['tests', 'kubernetes']},
)

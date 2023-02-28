# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 CERN.
#
# inspirehep is free software; you can redistribute it and/or modify it under
# the terms of the MIT License; see LICENSE file for more details.

import mock
import orjson

from inspirehep.records.marshmallow.literature.common import AuthorSchemaV1
from inspirehep.records.marshmallow.literature.common.author import (
    FirstAuthorSchemaV1,
    SupervisorSchema,
)


@mock.patch("inspirehep.records.marshmallow.literature.common.author.current_app")
def test_author(current_app_mock):
    current_app_mock.config = {"FEATURE_FLAG_ENABLE_POPULATE_BAI_FROM_LIT_AUTHOR": True}
    schema = AuthorSchemaV1()

    dump = {"full_name": "Castle, Frank"}
    expected = {
        "full_name": "Castle, Frank",
        "first_name": "Frank",
        "last_name": "Castle",
    }
    result = schema.dumps(dump).data

    assert expected == orjson.loads(result)


@mock.patch("inspirehep.records.marshmallow.literature.common.author.current_app")
def test_author_without_last_name(current_app_mock):
    current_app_mock.config = {"FEATURE_FLAG_ENABLE_POPULATE_BAI_FROM_LIT_AUTHOR": True}
    schema = AuthorSchemaV1()

    dump = {"full_name": "Frank Castle"}
    expected = {"full_name": "Frank Castle", "first_name": "Frank Castle"}
    result = schema.dumps(dump).data

    assert expected == orjson.loads(result)


@mock.patch(
    "inspirehep.records.api.authors.AuthorsRecord.get_record_by_pid_value",
    return_value={"ids": [{"schema": "INSPIRE BAI", "value": "Frank.Castle.1"}]},
)
@mock.patch("inspirehep.records.marshmallow.literature.common.author.current_app")
def test_author_with_bai(current_app_mock, mock_get_record):
    current_app_mock.config = {"FEATURE_FLAG_ENABLE_POPULATE_BAI_FROM_LIT_AUTHOR": True}
    schema = AuthorSchemaV1()

    dump = {
        "full_name": "Frank Castle",
        "record": {"$ref": "https://inspirebeta.net/api/authors/2094356"},
    }
    expected = {
        "first_name": "Frank Castle",
        "full_name": "Frank Castle",
        "record": {"$ref": "https://inspirebeta.net/api/authors/2094356"},
        "recid": 2094356,
        "ids": [{"schema": "INSPIRE BAI", "value": "Frank.Castle.1"}],
    }
    result = schema.dumps(dump).data

    assert expected == orjson.loads(result)


@mock.patch("inspirehep.records.marshmallow.literature.common.author.current_app")
def test_author_with_with_inspire_roles(current_app_mock):
    current_app_mock.config = {"FEATURE_FLAG_ENABLE_POPULATE_BAI_FROM_LIT_AUTHOR": True}
    schema = AuthorSchemaV1()
    dump = {"full_name": "Smith, John", "inspire_roles": ["author"]}
    expected = {
        "full_name": "Smith, John",
        "first_name": "John",
        "last_name": "Smith",
        "inspire_roles": ["author"],
    }
    result = schema.dumps(dump).data

    assert expected == orjson.loads(result)


@mock.patch("inspirehep.records.marshmallow.literature.common.author.current_app")
def test_author_schema_returns_empty_for_supervisor(current_app_mock):
    current_app_mock.config = {"FEATURE_FLAG_ENABLE_POPULATE_BAI_FROM_LIT_AUTHOR": True}
    schema = AuthorSchemaV1()
    dump = {"full_name": "Smith, John", "inspire_roles": ["supervisor"]}
    result = schema.dumps(dump).data

    assert orjson.loads(result) == {}


@mock.patch("inspirehep.records.marshmallow.literature.common.author.current_app")
def test_supervisor_schema(current_app_mock):
    current_app_mock.config = {"FEATURE_FLAG_ENABLE_POPULATE_BAI_FROM_LIT_AUTHOR": True}
    schema = SupervisorSchema()
    dump = {"full_name": "Smith, John", "inspire_roles": ["supervisor"]}
    expected = {
        "full_name": "Smith, John",
        "first_name": "John",
        "last_name": "Smith",
        "inspire_roles": ["supervisor"],
    }
    result = schema.dumps(dump).data

    assert expected == orjson.loads(result)


@mock.patch("inspirehep.records.marshmallow.literature.common.author.current_app")
def test_supervisor_schema_returns_empty_for_non_supervisor(current_app_mock):
    current_app_mock.config = {"FEATURE_FLAG_ENABLE_POPULATE_BAI_FROM_LIT_AUTHOR": True}
    schema = SupervisorSchema()
    dump = {"full_name": "Smith, John", "inspire_roles": ["author"]}
    result = schema.dumps(dump).data

    assert orjson.loads(result) == {}


@mock.patch("inspirehep.records.marshmallow.literature.common.author.current_app")
def test_first_author(current_app_mock):
    current_app_mock.config = {"FEATURE_FLAG_ENABLE_POPULATE_BAI_FROM_LIT_AUTHOR": True}
    schema = FirstAuthorSchemaV1()

    dump = {
        "ids": [{"schema": "INSPIRE BAI", "value": "Benjamin.P.Abbott.1"}],
        "record": {"$ref": "http://labs.inspirehep.net/api/authors/1032336"},
        "recid": 1032336,
        "raw_affiliations": [
            {
                "value": "LIGO - California Institute of Technology - Pasadena - CA 91125 - USA"
            }
        ],
        "affiliations": [
            {
                "record": {
                    "$ref": "http://labs.inspirehep.net/api/institutions/908529"
                },
                "value": "LIGO Lab., Caltech",
            }
        ],
        "signature_block": "ABATb",
        "uuid": "7662251b-47d4-4083-b44b-ce8a0112fd7b",
        "full_name": "Abbott, B.P.",
    }
    expected = {
        "last_name": "Abbott",
        "full_name": "Abbott, B.P.",
        "first_name": "B.P.",
        "recid": 1032336,
        "ids": [{"schema": "INSPIRE BAI", "value": "Benjamin.P.Abbott.1"}],
    }
    result = schema.dumps(dump).data

    assert expected == orjson.loads(result)

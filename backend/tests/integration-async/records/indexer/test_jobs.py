# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
#
# inspirehep is free software; you can redistribute it and/or modify it under
# the terms of the MIT License; see LICENSE file for more details.
from helpers.providers.faker import faker
from invenio_db import db
from invenio_search import current_search
from tenacity import retry, stop_after_delay, wait_fixed

from inspirehep.records.api import JobsRecord
from inspirehep.search.api import JobsSearch


def test_indexer_deletes_record_from_es(inspire_app):
    @retry(stop=stop_after_delay(30), wait=wait_fixed(0.3))
    def assert_record_is_deleted_from_es():
        current_search.flush_and_refresh("records-jobs")
        expected_records_count = 0
        record_lit_es = JobsSearch().get_record(str(record.id)).execute().hits
        assert expected_records_count == len(record_lit_es)

    record = JobsRecord.create(faker.record("job"))
    db.session.commit()

    record.delete()
    db.session.commit()

    assert_record_is_deleted_from_es()

# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# inspirehep is free software; you can redistribute it and/or modify it under
# the terms of the MIT License; see LICENSE file for more details.
import structlog
from flask import Blueprint, request
from invenio_db import db
from webargs import fields
from webargs.flaskparser import FlaskParser

from inspirehep.accounts.decorators import login_required_with_roles
from inspirehep.accounts.roles import Roles
from inspirehep.assign.tasks import assign_paper_to_conference, export_papers_to_cds
from inspirehep.disambiguation.utils import create_new_stub_author, update_author_names
from inspirehep.records.api import AuthorsRecord, LiteratureRecord
from inspirehep.serializers import jsonify
from inspirehep.utils import chunker, count_consumers_for_queue

from .tasks import assign_papers
from .utils import get_author_by_recid

blueprint = Blueprint("inspirehep_assign", __name__, url_prefix="/assign")
parser = FlaskParser()
LOGGER = structlog.getLogger()


def get_literature_records_by_recid(recids):
    pids = [("lit", str(recid)) for recid in recids]
    return LiteratureRecord.get_records_by_pids(pids)


def unstub_author_by_recid(author_recid):
    author = AuthorsRecord.get_record_by_pid_value(author_recid)
    if author.get("stub") is True:
        author["stub"] = False
        author.update(dict(author))


def get_author_signatures(from_author_recid, author_papers):
    signatures = [
        get_author_by_recid(record, from_author_recid) for record in author_papers
    ]
    return signatures


def assign_to_new_stub_author(from_author_recid, literature_recids):
    # TODO: differentiate from BEARD created stub author
    author_papers = list(get_literature_records_by_recid(literature_recids))
    author_signatures = get_author_signatures(from_author_recid, author_papers)
    stub_author_data = update_author_names({"name": {}}, author_signatures)
    to_author = create_new_stub_author(**stub_author_data)
    num_workers = count_consumers_for_queue("assign")
    for batch in chunker(author_papers, 10, num_workers):
        assign_papers(
            from_author_recid,
            to_author,
            batch,
            is_stub_author=True,
        )
    return to_author["control_number"]


def assign_to_author(from_author_recid, to_author_recid, literature_recids):
    author_record = AuthorsRecord.get_record_by_pid_value(to_author_recid)
    author_papers = list(get_literature_records_by_recid(literature_recids))
    num_workers = count_consumers_for_queue("assign")
    for batch in chunker(author_papers, 10, num_workers):
        assign_papers(
            from_author_recid,
            author_record,
            batch,
            is_stub_author=True,
        )
    unstub_author_by_recid(to_author_recid)


@blueprint.route("author", methods=["POST"])
@login_required_with_roles([Roles.cataloger.value])
def author_assign_view():
    body = request.get_json()
    to_author_recid = body.get("to_author_recid")
    from_author_recid = body["from_author_recid"]
    literature_recids = body["literature_recids"]
    if to_author_recid is None:
        stub_author_id = assign_to_new_stub_author(from_author_recid, literature_recids)
    else:
        assign_to_author(from_author_recid, to_author_recid, literature_recids)
    db.session.commit()
    if to_author_recid is None:
        return jsonify({"stub_author_id": stub_author_id}), 200
    return jsonify({"message": "Success"}), 200


@blueprint.route("conference", methods=["POST"])
@login_required_with_roles([Roles.cataloger.value])
@parser.use_args(
    {
        "conference_recid": fields.Integer(required=True),
        "literature_recids": fields.List(fields.Integer, required=True),
    },
    locations=("json",),
)
def literature_assign_conferences_view(args):
    conference_recid = args["conference_recid"]
    literature_recids = args["literature_recids"]

    try:
        assign_paper_to_conference.delay(literature_recids, conference_recid)
    except Exception:
        LOGGER.exception("Cannot start 'assign_paper_to_conference' task.")
        return jsonify({"message": "Internal Error"}), 500

    return jsonify({"message": "Success"}), 200


@blueprint.route("export-to-cds", methods=["POST"])
@login_required_with_roles([Roles.cataloger.value])
@parser.use_args(
    {
        "literature_recids": fields.List(fields.Integer, required=True),
    },
    locations=("json",),
)
def literature_export_to_cds(args):
    literature_recids = args["literature_recids"]
    try:
        export_papers_to_cds(literature_recids)
    except Exception:
        LOGGER.exception("Cannot start 'export_to_cds' task.")
        return jsonify({"message": "Internal Error"}), 500
    return jsonify({"message": "Success"}), 200

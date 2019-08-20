# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 CERN.
#
# inspirehep is free software; you can redistribute it and/or modify it under
# the terms of the MIT License; see LICENSE file for more details.

from .utils import humanize_date_to_natural_time


class InspireMailing:
    def __init__(self, app=None):
        if app:
            self.init_app(app)

    def init_app(self, app):
        app.jinja_env.filters[
            "humanizeDateToNaturalTime"
        ] = humanize_date_to_natural_time
        app.extensions["inspirehep-mailing"] = self
        return self

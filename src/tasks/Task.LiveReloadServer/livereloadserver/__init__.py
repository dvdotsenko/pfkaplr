# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, with_statement

from components.tornado.apptomatic import WebApplication
from .livereload_application import LIVERELOAD_PORT, HANDLERS

live_reload_application = WebApplication(
	HANDLERS
	, [('', LIVERELOAD_PORT)]
)

# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, with_statement

from components.tornado.apptomatic import WebApplication
from .config_application import PORT, HANDLERS

server = WebApplication(
	HANDLERS
	, [('', PORT)]
)

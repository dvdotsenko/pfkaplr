# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, with_statement

import logging
import weakref
from functools import partial as bind

from components.tornado.web import RequestHandler

## PubSub instance (global singleton)
from components import events
from components import APP_NAME

from . import config_messageparser as Messager
from .config_protocols import SUPPORTED_PROTOCOLS

HELLO = 'Configuration Handlers: '

class LogoRequestHandler(RequestHandler):
	def initialize(self, options):
		self.options = options

	def get(self, username):
		pass

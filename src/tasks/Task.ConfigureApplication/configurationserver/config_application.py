# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, with_statement

# glpbal modules
import os
import sys
import threading
import logging

# components module is a part of main app.
# these show up like this because the folder with all applicaitons
# modules is added to sys.path
## web server - Tornado (+ some minor tweaks)
from components.tornado.web import StaticFileHandler
## PubSub instance (global singleton)
#from components import events

# these are modules local to this task.
from . import config_handlers
from . import config_logorequesthandler

CWD = os.path.abspath(os.path.dirname(__file__))
STATIC_FOLDER = 'static'
PORT = 0 # will be autopicked by the system.
HANDLERS = [
    (
        r'/web_service/'
        , config_handlers.WebServiceHandler
    ),
    # (
    #     r'/img/logos/(.*)'
    #     , config_logorequesthandler.LogoRequestHandler
    #     , {}
    # ),
    (
        r'/?(.*)'
        , StaticFileHandler
        , {
        	'path': os.path.abspath(os.path.join(CWD, STATIC_FOLDER))
        	, 'default_filename': 'index.html'
        }
    )
]

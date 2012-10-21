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
from . import livereload_protocols as LiveRealoadProtocols
from . import livereload_handler as LiveReloadConnectionHandler

CWD = os.path.abspath(os.path.dirname(__file__))
LIVERELOAD_JS_FOLDER = 'static'
LIVERELOAD_PORT = 35729
HANDLERS = [
    (
        r'/livereload'
        , LiveReloadConnectionHandler.LiveReloadHandler
    ),
    (
        r'/(.*)'
        , StaticFileHandler
        , {
        	'path': os.path.abspath(os.path.join(CWD, LIVERELOAD_JS_FOLDER))
        	, 'default_filename': 'index.html'
        }
    )
]

# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, with_statement

LIVE_RELOAD_CLIENTSIDE_CONFIG = 'http://dvdotsenko.github.com/python-livereload/protocols/client-side-config-1/'
LIVE_REALOD_SUPPORTED_PROTOCOLS = [
    "http://livereload.com/protocols/connection-check-1"
    #,'http://livereload.com/protocols/official-6'
    ,'http://livereload.com/protocols/official-7'
    #,'http://livereload.com/protocols/2.x-remote-control'
    #,'http://livereload.com/protocols/2.x-origin-version-negotiation'
    ,LIVE_RELOAD_CLIENTSIDE_CONFIG
]
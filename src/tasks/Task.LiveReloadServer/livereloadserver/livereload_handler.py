# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, with_statement

import logging

from components.tornado.websocket import WebSocketHandler
## PubSub instance (global singleton)
from components import events

from components import APP_NAME

from . import livereload_protocols as LiveRealoadProtocols
from . import livereload_messageparser as LiveReloadMessage

HELLO = 'LiveReaload Connection Hanlder: '

class LiveReloadHandler(WebSocketHandler):
    '''
    One of these per each long websocket connection will be inited.
    ''' 
    
    def __init__(self, *args, **kw):
        logging.debug(HELLO + "__init__ socket connection.") # , dir(self))
        super(LiveReloadHandler, self).__init__(*args, **kw)

    # def allow_draft76(self):
    #     return True

    def initialize(self, **kw):
        '''
        Called when the class is initalized. 

        @param **kw {dict} Is the collection of named args passed to handler declaration upon Application construction.
        '''
        self.instance_settings = {}
        logging.debug(HELLO + "Initializing connection")

    # def open(self):
    #     logging.debug("Open running...")

    def handle_errors(self, *args, **kw):
        logging.debug(HELLO + "Connection error")
        try:
            self.close()
        except:
            pass
        # self.on_close()

    def on_close(self):
        logging.debug(HELLO + "Closing Connection")
        # TODO: remove this connection / self from rotation

    def send_message(self, message):
        logging.debug(HELLO + "Sending message %s" % message)
        try:
            self.write_message(
                LiveReloadMessage.encode( message ) 
            )
        except:
            logging.error('Error sending message', exc_info=True)
            self.handle_errors()

    def notify_of_change(self, path):
        msg = {
            'command': 'reload',
            'path': path,
            'liveCSS': True
        }
        try:
            self.send_message(msg)
        except:
            self.handle_errors()

    def on_message(self, message):
        logging.debug(HELLO + "Got message '%s'" % message)

        message = LiveReloadMessage.parse(message)
        ### HELLO
        if message['command'] == 'hello':
            supported_common = list(
                set(LiveRealoadProtocols.LIVE_REALOD_SUPPORTED_PROTOCOLS).intersection(
                    message['protocols']
                )
            )
            if len(supported_common):
                self.instance_settings['protocols'] = supported_common
                hello = {
                    'command': 'hello'
                    , 'protocols': supported_common
                    , 'serverName': APP_NAME
                }
                self.send_message(hello)
                logging.debug("Processed 'hello'")
        ### INFO and URL (update push from client)
        elif message['command'] in ('info','url'):
            
            new_url = message['url']

            # server does NOT listen to this
            # External consumer code will listen on this channel
            # if they need to do anything with new connections.
            events.publish(
                'LiveRealoadServer.NewConnection'
                , self
                , {
                    'domain': new_url
                    , 'from': self.request.remote_ip
                    , 'through': self.request.host
                    , 'protocol': 'livereload'
                }
            )

            logging.info('New LiveReload connection for URL "%s"' % new_url)

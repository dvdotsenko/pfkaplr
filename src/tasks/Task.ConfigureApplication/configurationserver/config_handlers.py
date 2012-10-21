# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, with_statement

import logging
import weakref
from functools import partial as bind

from components.tornado.websocket import WebSocketHandler

## PubSub instance (global singleton)
from components import events
from components import APP_NAME

from . import config_messageparser as Messager
from .config_protocols import SUPPORTED_PROTOCOLS

HELLO = 'Configuration Handlers: '

def process_rpc_response(connection, message_id, *args, **kw):
    con = connection() # it's actually a weak ref
    if not con:
        logging.debug(HELLO + " trying to reply to connection, but it's no longer around")
    else:
        logging.debug(HELLO + " replying back to connection...")
        '''
        Although the requests come in double-wrapped (for authentication reasons mostly)
        we reply with a plain JSON-RPC responce. This may change...
        '''
        wrapper = {
            'jsonrpc': '2.0'
            , 'id': message_id
        }

        # let's see if called code pushed an exception back
        if args and issubclass( type(args[0]), Exception):
            # yep, error condition
            wrapper['error'] = {
                'code': -32603 # Internal error
                , 'message': args[0].message
                # , 'data':  - optional. should contain something like stacktrace
            }
        else:
            # no point unpacking kw, since JavaScript does not support named args yet.
            # we are NOT unpacking the args, expecting that receiving side will 
            # unpack it into the callback.
            wrapper['result'] = args

        con.send_message(wrapper)

class WebServiceHandler(WebSocketHandler):
    '''
    One of these per each long websocket connection will be inited.
    ''' 
    
    def __init__(self, *args, **kw):
        logging.debug(HELLO + "__init__ socket connection.") # , dir(self))
        super(WebServiceHandler, self).__init__(*args, **kw)

    # def allow_draft76(self):
    #     return True

    def initialize(self, **kw):
        '''
        Called when the class is initalized. 

        @param **kw {dict} Is the collection of named args passed to handler declaration upon Application construction.
        '''
        self.instance_settings = {}
        logging.debug(HELLO + " Initializing connection")

    def open(self):
        logging.debug("Open running...")

    def handle_errors(self, *args, **kw):
        logging.debug(HELLO + " Connection error")
        try:
            self.close()
        except:
            pass
        # self.on_close()

    def on_close(self):
        logging.debug(HELLO + " Closing connection")

    def send_message(self, message):
        logging.debug(HELLO + "Sending message") # %s" % message)
        try:
            self.write_message(
                Messager.encode( message ) 
            )
        except:
            logging.error('Error sending message', exc_info=True)
            self.handle_errors()

    def on_message(self, data):
        logging.debug(HELLO + "Got message") # '%s'" % data)

        try:
            method, params, message_id = Messager.parse(data)
        except Exception as ex:
            logging.debug(HELLO + "Received the following error from message parser: %s" % ex)
            return

        ## we speak JSON-RPC (http://json-rpc.org/wiki/specification) over WebSocket

        ### RPC method
        if method == 'rpc':
            '''
            'rpc' method is a wrapper for an actual JSON-RPC packet. The reason we
            do it is to allow passing through authentication tocken for the connection,
            without polluting the arguments of the actual JSON-RPC call.

            We look like this:
            {
                method: rpc
                , id: None or number or string
                , params: {
                    method: actual_called_method's_name
                    , id: exact same as above, but irrelevant since we use the id from above
                    , params: params to be passed to the called method
                    --------------------
                    , authentication_token: something we got from server at hello stage, at inception of this websocket connection.
                    --------------------
                }
            }

            The wrapper call (when auth is good) calls one and only interface - PubSub.
                actual_called_method's_name is the channel name
                params are flattened into Python's *args, **kw boxes. 
                id is special. Presence of it means we need a callback added to *kw
                    This ID, WSConnection are packaged into the callback.
                    The called method calls callback when done.
            '''

            if not params or type(params) != dict or not params.get('method'):
                logging.debug(HELLO + " RPC call seems to have sub-call parts missing.")
                return

            actual_method = params['method']
            args = []
            kw = {}

            if 'params' in params:
                actual_params = params['params']
                if type(actual_params) == list:
                    args.extend(actual_params)
                elif type(actual_params) == dict:
                    kw.update(actual_params)
                # all other types of objects are not allowed as values for 'params' in JSON-RPC

            # presence of message ID means, it's not "Notification" 
            # (where caller does not expect a return value)
            # but is a "Call" where there is expectation of a return value.
            # since we are async, we can't return, we can only callback.
            if message_id:
                kw['callback'] = bind(
                    process_rpc_response
                    , weakref.ref(self)
                    , message_id
                )

            events.publish(
                actual_method
                , *args
                , **kw
            )

        ### HELLO
        elif method == 'hello':

            supported_common = list(
                set(SUPPORTED_PROTOCOLS).intersection(
                    params['protocols']
                )
            )

            if len(supported_common):
                hello = {
                    'method': 'hello'
                    , 'params': {
                        'protocols': supported_common
                        , 'serverName': APP_NAME
                    }
                    , 'id': message_id
                }
                self.send_message(hello)

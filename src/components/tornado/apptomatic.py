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
from components.tornado.ioloop import IOLoop
from components.tornado.web import Application
from components.tornado.httpserver import HTTPServer, HTTPConnection
from components.tornado.util import b

HELLO = "Web Applicaiton Server: "


class FlashSecretHandshakeHandler(object):
    """Handles a connection to an TCP client, executing Flash Policy File request"""

    def __init__(self, stream):
        self.stream = stream
        self.response_body = b('<cross-domain-policy><allow-access-from domain="*" to-ports="*" /></cross-domain-policy>')
        self.stream.read_until(b("<policy-file-request/>"), self._on_read_complete)

    def write(self, chunk, callback=None):
        if not self.stream.closed():
            self.stream.write(chunk, callback)

    def finish(self):
        if not self.stream.writing():
            self.stream.close()

    def _on_read_complete(self, data):
        self.write(self.response_body, self.finish)

class HTTPServerPlusFlashSecretHandshake(HTTPServer):

    def handle_stream(self, stream, address):
        
        def iAmTheDecider(fragment):
            stream.prepend(fragment)
            handler = self
            if fragment == '<policy-':# ...'file-request/>'
                logging.debug(HELLO + "Detected Flash Secret Handshake request.")
                FlashSecretHandshakeHandler(stream)
            else:
                HTTPConnection(
                    stream, address
                    , handler.request_callback
                    , handler.no_keep_alive
                    , handler.xheaders
                )

        stream.read_bytes(8, iAmTheDecider)


'''
    handlers = [
        (
            r'/livereload'
            , MyCustomHandlerBasedOnOneOfTornadoRequestHandlers
            , {'myargument': myargument_value}
        ),
        (
            r'/(somefile.js)'
            , StaticFileHandler
            , {'path': os.path.abspath(os.path.join(CWD, some_subfolder))}
        )
    ]
'''

class Base(object):

    def __init__(self, handlers = [], bindings = []):
        self.handlers = handlers
        self.bindings = list(bindings) # we will be rewriting port numbers when port 0 is used for "autoassign"
        self.loop = None

    def _server_runner(self, handlers, bindings, loop):
        raise NotImplementedError("Override _server_runner method in your sub-class.")

    def start(self):

        if not self.handlers or not self.bindings:
            raise ArgumentError("To run a web applicaiton, we need to know the port and have at least one handler.")

        if self.loop and self.loop.running():
            return

        self.loop = IOLoop()

        th = threading.Thread(
            target = self._server_runner
            , args = [
                self.handlers
                , self.bindings
                , self.loop
            ]
        )
        th.daemon = True
        th.start()

    def stop(self):
        logging.debug(HELLO + " stopping")
        # http://www.tornadoweb.org/documentation/ioloop.html
        # "It is safe to call this method from any thread at any time. 
        # Note that this is the only method in IOLoop that makes this guarantee;
        # all other interaction with the IOLoop must be done from that IOLoop’s
        # thread. add_callback() may be used to transfer control from other
        # threads to the IOLoop’s thread."
        loop = self.loop
        self.loop = None

        loop.add_callback(loop.stop)

        try:
            # it's unfortunate that Tornado people used "_" prefix for this.
            # This should be a public API property.
            loop._waker.wake()
        except:
            pass

    @property
    def is_running(self):
        return self.loop and self.loop.running()


class WebApplication(Base):

    def _server_runner(self, handlers, bindings, loop):

        http_server = HTTPServerPlusFlashSecretHandshake(
            Application( handlers = handlers )
            , io_loop = loop
        )

        rewrite = {}
        for binding in bindings:
            # for now we just start listenning on all IPs for given port.
            # will wire up domain/ip binding later.
            sockets = http_server.listen(binding[1])
            assignedport = sockets[0].getsockname()[1]
            if assignedport != binding[1]:
                rewrite[bindings.index(binding)] = (binding[0], assignedport)
            logging.debug(HELLO + "listenning on port %s" % assignedport)
        
        if rewrite:
            for i in rewrite.keys():
                bindings[i] = rewrite[i]

        logging.debug(HELLO + "started")
        loop.start()
        # "An IOLoop must be completely stopped before it can be closed. 
        # This means that IOLoop.stop() must be called and IOLoop.start()
        # must be allowed to return before attempting to call IOLoop.close().
        # Therefore the call to close will usually appear just after the call
        # to start rather than near the call to stop"
        logging.debug(HELLO + "stopped")
        loop.close()


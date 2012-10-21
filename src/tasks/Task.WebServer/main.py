from __future__ import absolute_import, division, with_statement

import os
import weakref
import threading
import logging

## PubSub instance (global singleton)
from components import events
from components.taskbase import TaskBase
from components.tornado.web import StaticFileHandler
from components.tornado.apptomatic import WebApplication

class Task(TaskBase):
	'''
	Static Web Server

	Based on Tornado's StaticHTTPServer but with some patches.
	'''

	ID = 'Core.StaticWebServer'

	METADATA = {
		'id': ID
		, 'type': 'Task'
		, 'tasktype': ID
		, 'label': 'Static Web Server'
		, 'description': 'Starts a static web server rooted at a defined folder.'
		, 'inputs': [
			[".", 'String', 'path', 'Filesystem path to serve as root.']
			, ['', 'String', 'domain', 'Domain name or IP address PLUS port number to tie the server to. Empty string for domain means "listen on all domains / IP addresses". If no port number is provided or ":0" port number is provided, system autopicks first available port. If you are providing IPv6 address, you must end it with a port number colon + number combination.']
			, ["index.html", 'String', 'defaultfile', 'File to serve when a folder is requested.']
			, [None, 'Callback', 'callback', 'Function to be called (or passed to async delegate) when done.']
		]
		, 'outputs':[
			[None, 'Message[]', 'messages', 'Array of Message objects detailing the event.']
			, [None, 'MetadataUpdate[]', 'metadataupdate', 'An list of objects with properties this task runner suggests the task handler to update the task scheduling record with. This allows runners to update the task record\'s label, arguments etc.']
		]
		, 'paused': True
	}

	# example (proposed) Message object:
	# {
	#	 'domain': some_url_about_which_listener_cares_about (or RegEx object for wildcarding)
	#	 , 'from': 'string describing origination of the message'
	#	 , 'metadata': {} Object with something.
	#	 , 'body': 'Full text of the message'
	# }
	# only 'body' is expected to be there now 2012-09-15 
	# the rest will be invented as we go.
	# ddotsenko

	# example (proposed) MetadataUpdate array:
	# [
	#  {'prop':{'deeper_prop':value}}
	#  , {'prop':{'another_prop':value}}
	# ]

	# def _get_served_address(self, server):
	# 	if server.bindings and \
	# 		server.bindings[0] and \
	# 		server.bindings[0][1]:

	# 		domain = server.bindings[0][0] or 'localhost'
	# 		port = server.bindings[0][1]

	# 		return 'http://%s:%s/' % ( domain, port )
	# 	else:
	# 		return ''

	def _open_in_browser(self, address):
		os.startfile(address)

	def init(self):
		self.callbacks = {}
		self.domains = weakref.WeakValueDictionary()

	def run(self, path, domain, defaultfile, callback):

		handlers = [(
			r'/(.*)'
			, StaticFileHandler
			, {
				'path': os.path.abspath(os.path.abspath(path))
				, 'default_filename': defaultfile
			}
		)]

		domainparts = domain.split(':')
		if len(domainparts) == 1:
			port = 0
		else:
			port = int( domainparts.pop(-1), 10 )
		# in anticipation of IPv6 addresses, jointing the parts back.
		domain = ":".join(domainparts)

		server = WebApplication(
			handlers
			, [(domain, port)]
		)

		server.start()

		self.callbacks[callback] = [
			server
			, path
			, domain
			, defaultfile
		]

		address = 'http://%s:%s/' % ( domain, port )
		self._open_in_browser(address)

		changes = [{
			'label': self.METADATA['label'] + " on '%s'" % address
		}]

		messages = [{
			'from': self.ID
			, 'body': "Now serving path '%s' as '%s'" % (path, address)
		}]

		callback(messages, changes)

	def stop(self, path, domain, defaultfile, callback, *args, **kw):
		settings = self.callbacks.get(callback)
		if settings:
			try:
				settings[0].stop()
			except:
				pass

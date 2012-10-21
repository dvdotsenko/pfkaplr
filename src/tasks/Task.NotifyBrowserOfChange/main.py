from __future__ import absolute_import, division, with_statement

import os
import weakref
import threading
import re
import logging

## PubSub instance (global singleton)
from components import events
from components.taskbase import TaskBase

HELLO = "LiveReloadNotify.main.py: "

class TaskNotifyBrowserOfChange(TaskBase):
	'''
	Notify browsers of change

	Notifies browsers that some underlying content had changed and they need to refresh.
	'''

	ID = 'LiveReload.LiveReloadNotify'

	REQUIRE = [
		'LiveReload.LiveReloadServer'
	]

	METADATA = {
		'id': ID
		, 'type': 'Task'
		, 'tasktype': ID
		, 'label': 'Notify Browser'
		, 'description': 'Notifies browsers (over LiveReload protocol) of events of changes to some underlying content.'
		, 'inputs': [
			[None, 'Change[]', 'changes', 'Array of Change objects detailing the occured changes.']
			, [None, 'Message[]', 'messages', 'Array of Message objects to be conveyed to the recepient.']
			, [[{'domain':'.+'}], 'Client[]', 'connections', 'Array of Client objects - data collections describing a connection to a remote data consumer. By default, broadcasts to all connections.']
			, [None, 'Callback', 'callback', 'Function to be called (or passed to async delegate) when done']
		]
		, 'outputs':[]
		, 'paused': True
	}

	def init(self):
		self.clients = weakref.WeakKeyDictionary()
		self.clients_lock = threading.Lock()

		# Task.AllowBrowsersToListenForChange has identical listener
		# but there it is responsible for connecting new connections
		# to interested TaskHives. Here we just log the connections
		# cause when TaskHive calls us, we need to have a handle to
		# the connection.
		events.subscribe(
			'LiveRealoadServer.NewConnection'
			, self._new_client_connected
		)

	def _new_client_connected(self, connection, metadata):
		'''
		metadata = {
			'domain': new_url
			, 'from': self.request.remote_ip
			, 'through': self.request.host
			, 'protocol': 'livereload'
		}
		'''
		logging.debug(HELLO + "New LiveReload client connected. %s " % metadata)
		with self.clients_lock:
			self.clients[connection] = metadata

	def _client_connection_fits_filters(self, metadata, filters):
		if metadata:
			for filterobj in filters:
				matchedall = True
				for key in filterobj.keys():
					if key in metadata and re.search(filterobj[key], metadata[key]):
						matchedall = matchedall & True
					else:
						matchedall = matchedall & False
				if matchedall:
					return True
		return False

	def run(self, changes, messages, connections, callback):
		'''
		@param {Change[]} changes Array of Change objects describing the changes that occured to sertain paths.
		@param {Client[]} connections Array of Client objects - data collections describing a connection to a remote data consumer.
		@param {Function} callback to be called by runner when done (or passed to async delegate)
		'''

		# example Client object:
		# {
		#     'domain': some_url_about_which_listener_cares_about (or RegEx object for wildcarding)
		#     , 'from': client's ip 
		#     , 'through': server address through which the client came in to us
		#     , 'protocol': 'livereload'
		# }

		# example Change object:
		# {
		# 	'domain': watched path
		# 	, 'path': changed path
		# 	, 'change': type of change as string ()
		# }

		# typical client metadata:
		# {
		# 	'through': '127.0.0.1:35729'
		# 	, 'domain': u'http://localhost/mywebapp/'
		# 	, 'from': '127.0.0.1'
		# 	, 'protocol': 'livereload'
		# }

		# for now we will ignore the connections filter and will just blust to all.
		logging.debug(HELLO + "See %s listenning LiveReload clients" % len(self.clients.keys()))

		for connection in self.clients.keys():
			if self._client_connection_fits_filters(self.clients.get(connection), connections) :
				for change in changes:
					connection.notify_of_change(change['path'])

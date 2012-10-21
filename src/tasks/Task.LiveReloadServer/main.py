from __future__ import absolute_import, division, with_statement

import os
import weakref
import threading
import logging

## PubSub instance (global singleton)
from components import events
from components.taskbase import TaskBase

class TaskLiveReloadServer(TaskBase):
	'''
	LiveReload Server

	Starts a (LiveReload type) server that allows browsers to connect and listen for change notifications.
	'''

	ID = 'LiveReload.LiveReloadServer'

	METADATA = {
		'id': ID
		, 'type': 'Task'
		, 'tasktype': ID
		, 'label': 'LiveReload Server'
		, 'description': 'Starts a (LiveReload type) server that allows browsers to connect and listen for change notifications.'
		, 'inputs': [
			[None, 'Callback', 'callback', 'Function to be called (or passed to async delegate) when done']
		]
		, 'outputs':[]
		, 'paused': True
	}

	def _new_client_connected(self, connection, metadata):
		'''
		metadata = {
			'domain': site's url
			, 'from': self.request.remote_ip
			, 'through': self.request.host
		}
		'''

		with self.clients_lock:
			self.clients[connection] = metadata

		events.publish(
			'TaskHiveCoordinator.AssociateConsumerWithHive'
			, metadata
		)

	def init(self):
		# this starts the LiveReload server in general. It means all browsers CAN connect to it,
		# but they don't have a connection to any given TaskHive, and will be prompted to choose one
		# or disconnect.

		logging.debug("Initing LiveReloadServer")

		from .livereloadserver import live_reload_application

		self.server = live_reload_application
		self.run_requests = 0

		self.clients = weakref.WeakKeyDictionary()
		self.clients_lock = threading.Lock()

		events.subscribe(
			'LiveRealoadServer.NewConnection'
			, self._new_client_connected
		)

	def run(self, callback):
		'''
		@param {Function} callback to be called by runner when done (or passed to async delegate)
		'''
		self.run_requests += 1
		if not self.server.is_running:
			self.server.start()
		callback()

	@property
	def is_running(self):
		return self.server.is_running

	def stop(self):
		'''
		@param {TaskHive} taskhive Reference to the TaskHive that the browser connections would subscribe to.
		'''
		self.run_requests -= 1
		if not self.run_requests:
			self.server.stop()


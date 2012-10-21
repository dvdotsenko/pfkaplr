from __future__ import absolute_import, division, with_statement

import os
import weakref
import threading
import logging

from functools import partial as bind

## PubSub instance (global singleton)
from components import APP_NAME
from components import events
from components.taskbase import TaskBase

HELLO = "ConfigureApp - main.py: "

class Task(TaskBase):
	ID = 'Core.ConfigurationWebInterface'

	METADATA = {
		'id': ID
		, 'type': 'Task'
		, 'tasktype': ID
		, 'label': 'Configure %s' % APP_NAME
		, 'description': 'Manage all aspects of %s through a web-based graphical user interface.' % APP_NAME
		, 'inputs': [
			[None, 'Callback', 'callback', 'Function to be called (or passed to async delegate) when done']
		]
		, 'outputs':[]
		, 'paused': True
	}

	# def _new_client_connected(self, connection, metadata):
	# 	'''
	# 	metadata = {
	# 		'domain': site's url
	# 		, 'from': self.request.remote_ip
	# 		, 'through': self.request.host
	# 	}
	# 	'''

	# 	with self.clients_lock:
	# 		self.clients[connection] = metadata

	# 	events.publish(
	# 		'TaskHiveCoordinator.AssociateConsumerWithHive'
	# 		, metadata
	# 	)

	def _get_address(self):
		if self.server.bindings and \
			self.server.bindings[0] and \
			self.server.bindings[0][1]:
			return 'http://localhost:%s' % self.server.bindings[0][1]
		else:
			return ''

	def _process_request_for_config(self):
		addr = self._get_address()
		if addr:
			os.startfile(addr)

	def _tasktypes_changed_handler(self, staticpath, newcollection):
		logging.debug(HELLO + "have new collection %s " % len(newcollection.keys()))
		for tasktypeid in newcollection:
			if hasattr(newcollection[tasktypeid], 'LOGO'):
				logopath = os.path.join(staticpath, 'img', 'logos', tasktypeid + '.svg')
				try:
					with open(logopath,'wb') as fp:
						fp.write(newcollection[tasktypeid].LOGO)
				except Exception as e:
					pass

	def init(self):
		self.tasktypelogo = {}

		from .configurationserver import server, config_application

		events.subscribe(
			'TaskHiveCoordinator.TaskTypes.Changed'
			, bind( 
				self._tasktypes_changed_handler
				, os.path.join(config_application.CWD, config_application.STATIC_FOLDER)
			)
		)

		self.server = server
		self.run_requests = 0

	def run(self, callback):
		'''
		@param {Function} callback to be called by runner when done (or passed to async delegate)
		'''
		self.run_requests += 1
		if not self.server.is_running:
			self.server.start()

			events.subscribe(
				'Application.Configuration.Show'
				, self._process_request_for_config
			)

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


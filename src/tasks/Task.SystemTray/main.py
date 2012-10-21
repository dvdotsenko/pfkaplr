from __future__ import absolute_import, division, with_statement

from components.taskbase import TaskBase
from components import events
from components import APP_NAME
from .systemtraycontrol import SystemTrayControl

class TaskSystemTray(TaskBase):
	ID = 'Core.SystemTrayControls'

	METADATA = {
		'id': ID
		, 'type': 'Task'
		, 'tasktype': ID
		, 'label': 'System Tray Controls'
		, 'description': 'Allows you to control %s through a system tray icon.' % APP_NAME
		, 'inputs': [
			[None, 'Callback', 'callback', 'Function to be called (or passed to async delegate) when done']
		]
		, 'outputs':[]
		, 'paused': False
	}

	def init(self):
		if SystemTrayControl:
			self.control = SystemTrayControl()
			self.control.start()

	def run(self, callback):
		'''
		@param {Callback} callback To be called by runner when done (or passed to async delegate)
		'''
        # for now we will ignore the connections filter and will just blust to all.
		callback()

	def stop(self):
		pass

	def dispose(self):
		pass
from __future__ import absolute_import, division, with_statement

import threading
import collections

from components.taskbase import TaskBase

HELLO = 'Test.Delay: '

class TaskDelay(TaskBase):
	'''
	Delays action

	Delays a certain action by a set amount of time.
	'''
	ID = 'Core.Delay'

	METADATA = {
		'id': ID
		, 'type': 'Task'
		, 'tasktype': ID
		, 'label': 'Delay' 
		, 'description': 'Delays a certain action by a set amount of time.'
		, 'inputs': [
			["1.0", 'String', 'delay', 'Number of seconds by which to delay action']
			, [None, 'Callback', 'callback', 'Function to be called (or passed to async delegate) when done']
			# all incoming inputs are packed into Args obj dynamically by the typing system whenever it encounters Args type.
			, [None, 'Args', 'args', 'Object encompasing unused captured args and description of their types as passed into this task.']
		]
		, 'outputs':[
			# output format is calculated dynamically by the typing system whenever it encounters Args type.
			[None, 'Args', 'args', 'Object encompasing captured args of the LAST accumulated event and description of their types as passed into this task.']
		]
		, 'paused': False
	}

	def init(self):
		self.queue = {}
		self.queue_lock = threading.Lock()

	def _timer_callback(self, label, callback):
		args = None
		with self.queue_lock:
			args = self.queue.get(label)
			if args:
				del self.queue[label]

		if args:
			callback(args)

	def run(self, delay, callback, args):
		'''
		@param {String} delay
		@param {Callback} callback to be called by runner when done (or passed to async delegate)
		@param {Args} args Array of packed args objects .
		'''
		# Args are something like this:
		# [{
		#	'kw':{} # all incoming args are converted to kw because we know the declaration.
		#	'kw_types':{}
		#	'from':'long_id_of_task_runner_instance'
		#	'to':'long_id_of_task_runner_instance'
		# }, another one here ] 
		# Args are always unpacked and repacked at each hand-over point.
		# so there would not be a double-wrapping.
		dotimer = False
		if args:
			f = args.get('from')
			t = args.get('to')
			if f and t:
				label = f + '.' + t
				with self.queue_lock:
					if label not in self.queue:
						dotimer = True
					self.queue[label] = args

		if dotimer:
			try:
				seconds = float(delay)
			except:
				seconds = 1

			t = threading.Timer(
				seconds
				, self._timer_callback
				, args = [label, callback]
			)
			t.daemon = True
			t.start()


from __future__ import absolute_import, division, with_statement

try:
	from components.taskbase import TaskBase
except:
	class TaskBase:
		pass

from .protocol import Notificator

class TaskNotifySystemPopUp(TaskBase):
	'''
	Notify through system pop up.

	Use OS-specific notification mechanism (Growl, Linux's notify etc) to inform of an event.
	'''

	ID = 'Core.SystemNotify'

	METADATA = {
		'id': ID
		, 'type': 'Task'
		, 'tasktype': ID
		, 'label': 'System Popup'
		, 'description': 'Use OS-specific notification mechanism (Growl, Linux\'s notify etc) to inform of an event.'
		, 'inputs': [
			[None, 'Change[]', 'changes', 'Array of Change objects detailing the occured changes.']
			, [None, 'Message[]', 'messages', 'Array of Message objects detailing the event.']
			, [[{'domain':'.+'}], 'Client[]', 'connections', 'Array of Client objects - data collections describing a connection to a remote data consumer. By default, broadcasts to all connections.']
			, [None, 'Callback', 'callback', 'Function to be called (or passed to async delegate) when done']
		]
		, 'outputs':[]
		, 'paused': True
	}

	def init(self):
		self.notificator = Notificator()
		self.notificator.init()

	def run(self, changes, messages, connections, callback):
		'''
		@param {Change[]} changes Array of Change objects describing the changes that occured to sertain paths.
		@param {Message[]} changes Array of Message objects describing the events.
		@param {Client[]} connections Array of Client objects - data collections describing a connection to a remote data consumer.
		@param {Function} callback to be called by runner when done (or passed to async delegate)
		'''

		# example Client object:
        # {
        #     'domain': some_url_about_which_listener_cares_about (or RegEx object for wildcarding)
        #     , 'from': client's ip 
        #     , 'through': server address through which the client came in to us
        #     , 'protocol': 'someprotocol'
        # }

        # for now we will ignore the connections filter and will just blust to all.
		self.notificator.run(changes, messages, connections, callback)

	def stop(self):
		self.notificator.stop()

	def dispose(self):
		self.notificator.dispose()
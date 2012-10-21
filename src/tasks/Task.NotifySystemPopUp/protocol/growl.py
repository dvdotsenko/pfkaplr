from __future__ import absolute_import, division, with_statement

from components import APP_NAME

APPLICATION_ICON = None

# I did not test this. Just moved the code from old app.py.
# ddotsenko

from gntp import notifier

from .base import Notificator as BaseNotificator

class Notificator(BaseNotificator):

	def init(self):
		self.growl = notifier.GrowlNotifier(
			applicationName = 'APP_NAME'
			, notifications = ['Message']
			, defaultNotifications = ['Message']
			, applicationIcon = None
		)
		result = self.growl.register()
		if not result:
			raise ImportError

	def run(self, changes, messages, connections, callback):
		'''
		@param {Change[]} changes Array of Change objects describing the changes that occured to sertain paths.
		@param {Message[]} changes Array of Message objects describing the events.
		@param {Client[]} connections Array of Client objects - data collections describing a connection to a remote data consumer.
		@param {Function} callback to be called by runner when done (or passed to async delegate)
		'''
		# example Client object:
		# {
		#	 'domain': some_url_about_which_listener_cares_about (or RegEx object for wildcarding)
		#	 , 'from': client's ip 
		#	 , 'through': server address through which the client came in to us
		#	 , 'protocol': 'someprotocol'
		# }
		# example Message object:
		# {
		#	 'domain': some_url_about_which_listener_cares_about (or RegEx object for wildcarding)
		#	 , 'from': 'string describing origination of the message'
		#	 , 'metadata': {} Object with something.
		#	 , 'body': 'Full text of the message'
		# }
		if messages:
			for message in messages:
				self.growl.notify(
					'Message'
					, APP_NAME
					, message.get('body','(no message provided)')
					, icon = APPLICATION_ICON
				)
		callback()

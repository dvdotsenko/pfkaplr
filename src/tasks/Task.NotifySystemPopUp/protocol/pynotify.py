from __future__ import absolute_import, division, with_statement

from components import APP_NAME

# I did not test this. Just moved the code from old app.py.
# ddotsenko

import pynotify

from .base import Notificator as BaseNotificator

class Notificator(BaseNotificator):

	def init(self):
		pynotify.init(APP_NAME)

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
				pynotify.Notification(
					APP_NAME
					, message.get('body','(no message provided)')
				).show()
		callback()

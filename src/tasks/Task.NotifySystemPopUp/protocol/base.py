import logging

from components import APP_NAME

class Notificator(object):
	def init(self):
		pass

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
		# example (proposed) Message object:
		# {
		#	 'domain': some_url_about_which_listener_cares_about (or RegEx object for wildcarding)
		#	 , 'from': 'string describing origination of the message'
		#	 , 'metadata': {} Object with something.
		#	 , 'body': 'Full text of the message'
		# }
		# only 'body' is expected to be there now 2012-09-15 ddotsenko
		# the rest will be invented as we go.

		if messages:
			for message in messages:
				logging.info(APP_NAME + " " + message.get('body','(no message provided)'))
		callback()

	def stop(self):
		# if your run() can be long-running and is stopable, override this to stop it.
		pass

	def dispose(self):
		# here stop whatever you started in init()
		pass
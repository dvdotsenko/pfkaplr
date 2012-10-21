# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, with_statement

import logging

from components.tornado.escape import json_decode, json_encode

# these are modules local to this task.
from . import livereload_protocols as LiveRealoadProtocols

# protocol 7 commands
ALLOWED_COMMANDS = [
	'hello'
	, 'info'
	, 'url'
]

def encode(message):
	if isinstance(message, dict):
		return json_encode(message)
	else:
		return message

def parse(message):
	'''
	Parses and validates (against Protocol v7) the incoming string.
	Returns Dictionary structure (as parsed from received JSON string)
	'''
	# we only talk and validate V7 protocol.

	command_not_found = {'command':'not found'}

	try:
		message = json_decode(message)
	except Exception as ex:
		logging.debug("MessageParser: Were not able to JSON parse the message. '%s'" % ex)
		return command_not_found

	if 'command' not in message or message['command'] not in ALLOWED_COMMANDS:
		logging.debug("MessageParser: Did not find proper command in the message.")
		return command_not_found

	### HELLO
	if message['command'] == 'hello' and 'protocols' in message:
		return message
	### INFO and URL (update push from client)
	elif message['command'] in ('info','url') and 'url' in message:
		return message
	else:
		return command_not_found
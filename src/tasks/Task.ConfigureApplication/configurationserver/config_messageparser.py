# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, with_statement

import logging

from components.tornado.escape import json_decode, json_encode

# these are modules local to this task.
from . import config_protocols as Protocols

ALLOWED_COMMANDS = [
	'hello'
	, 'rpc'
]

def encode(message):
	if isinstance(message, dict):
		return json_encode(message)
	else:
		return message

def parse(data):
	'''
	Unpacks data string into JSON object. Ensures basic props are there.
	'''

	# 1. let's inspect the wrapper message
	try:
		message = json_decode(data)
	except Exception as ex:
		raise ex

	if 'method' not in message or 'params' not in message or \
		message['method'] not in ALLOWED_COMMANDS:
		raise Exception("MessageParser: Did not find proper components in the message.")

	# JSON-RPC style child args
	return (
		message['method']
		, message.get('params', {}) # when there are no args to pass, JSON-RPC allows to ommit 'params'
		, message.get('id', None) # lack of 'id' elem = 'Notify' mode in JSON-RPC
	)
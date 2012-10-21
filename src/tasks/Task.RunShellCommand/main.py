from __future__ import absolute_import, division, with_statement

import os
import subprocess

from components.taskbase import TaskBase

class TaskRunShellCommand(TaskBase):
	ID = 'Core.RunShellCommand'

	METADATA = {
		'id': ID
		, 'type': 'Task'
		, 'tasktype': ID
		, 'label': 'Run Command'
		, 'description': 'Runs a command'
		, 'inputs': [
			[None, 'String|Array', 'command', 'List of command elements or already-quoted string of the command. Elements of command list will be quoted per rules of the OS.']
			, [None, 'Callback', 'callback', 'Function to be called (or passed to async delegate) when done.']
			, ['.', 'String', 'working_directory', 'Path to the folder that will act as the current working directory for the ran command.']
			, [{}, 'Object', 'env', 'A dictionary of ADDITIONAL shell env vars. It is merged onto existing shell env vars before command is ran.']
		]
		, 'outputs':[]
		, 'paused': True
	}

	def run(self, command, callback, working_directory = '.', env = {}):
		'''
		@param {String|Array} command List of command elements or already-quoted string of the command. Elements of command list will be quoted per rules of the OS.
		@param {Callback} callback to be called by runner when done (or passed to async delegate)
		@param {String} [working_directory='.'] Path to the folder that will act as the current working directory for the ran command.
		@param {Object} [env={}] A dictionary of ADDITIONAL shell env vars. It is merged onto existing shell env vars before command is ran.
		'''
		if env:
			shellenv = os.environ.copy()
			shellenv.update(env)
			env = shellenv

		subprocess.call(
			command
			, cwd = working_directory
			, env = env
			, shell = True
		)

		callback()
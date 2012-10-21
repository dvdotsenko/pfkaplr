from __future__ import absolute_import, division, with_statement

import os
import logging
import re

from components.taskbase import TaskBase
from components import events

from .pathwatchcoordinator import PathWatchCoordinator

HELLO = 'Test.PathWatcher.main.py: '

class TaskPathWatch(TaskBase):
	'''
	Watch folder for changes

	Continuously watches a folder for changes and signals which watched path changed, what child of the watched path changed and mentions the nature of the change.
	'''

	ID = 'Core.PathWatch'

	METADATA = {
		'id': ID
		, 'type': 'Task'
		, 'tasktype': ID
		, 'label': 'Watch path change'
		, 'description': 'Continuously watches a folder for changes and signals which watched path changed, what child of the watched path changed and mentions the nature of the change.'
		, 'inputs': [
			['.', 'String', 'path', 'Filesystem path to watched folder']
			, [
				[
					(r'\.git|\.svn|\.bzr|\.pyc$', False)
					, (r'.*', True)
				]
				, 'RegExObj[]'
				, 'filter_regex'
				, 'An array of pairs of (Python-style regular expression, True/False for "must match" or "must NOT match") to be applied as filter againts the paths of the changed files. Applied only to the portion of the path AFTER the base, watched folder name. Each pair is evaluated in order, looking for first combined true value. Include `(".*",true)` as the last entry on the list to pick up all changes.'
			]
			, [None, 'Callback', 'callback', 'Function to be called (or passed to async delegate) when done']
		]
		, 'outputs':[
			# Change object: {'domain':'/home/user/projects/', 'path':'mine/file.ext', 'change':'Created'}
			# in this case, 'domain' is the 'watched path' and 'path' is the path that changed under that watched folder.
			[None, 'Change[]', 'changes', 'Array of Change objects detailing the occured changes.']
		]
		, 'paused': False
	}

	def init(self):
		self.PathWatchCoordinator = PathWatchCoordinator()

	def run(self, path, filter_regex, callback, *a, **kw):
		'''
		@param {String} path Filesystem path to watched folder.
		@param {RegExObj[]} filter_regex An array of pairs of (Python-style regular expression, True/False for "must match" or "must NOT match") to be applied as filter againts the paths of the changed files. Applied only to the portion of the path AFTER the base, watched folder name. Each pair is evaluated in order, looking for first combined true value. Include `(".*",true)` as the last entry on the list to pick up all changes.
		@param {Callback} callback to be called by runner when done (or passed to async delegate)
		'''
		logging.debug(HELLO + "Running path watcher for '%s'" % (path))
		events.publish(
			'PathWatchCoordinator.Watch'
			, os.path.abspath( path )
			, filter_regex
			, callback
		)

	def stop(self, path, filter_regex, callback, *a, **kw):
		'''
		@param {String} path Filesystem path to watched folder.
		@param {Callback} callback to be called by runner when done (or passed to async delegate)
		'''
		events.publish(
			'PathWatchCoordinator.Stop'
			, os.path.abspath( path )
			, filter_regex
			, callback
		)

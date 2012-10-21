# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, with_statement

import os
import threading
import weakref
import functools
import re
import time

import logging

from components import events
from components import systemtools

if systemtools.MODE == 'Windows':
	try:
		from .pathwatcher_windows import watch_path
	except ImportError:
		from .pathwatcher_generic import watch_path
else:
	from .pathwatcher_generic import watch_path

HELLO = "PathWatchCoordinator: "

class PathWatchCoordinator(object):

	def __init__(self):

		# 'path':callback
		self.paths = {}
		self.paths_lock = threading.Lock()

		# some OS-specific file system watchers
		# have echoes for same change
		# On windows we are fast enough to
		# fire several times between start and end of
		# write for same file. The format is:
		# {path:{changetype:time}}
		self.recently_fired = {} 
		self.recently_fired_lock = threading.Lock()

		# callback:filter_regex
		# because self.paths is the only place where we store hard refs to callbacks
		# removing it there, should autocleanup self.filters
		self.filters = weakref.WeakKeyDictionary()
		self.filters_lock = threading.Lock()
		
		# internal API
		events.subscribe(
			'PathWatchCoordinator.StartPathWatchRunner'
			, self._watch_runner
		)

		# public API
		events.subscribe(
			'PathWatchCoordinator.Watch'
			, self.watch
		)

		events.subscribe(
			'PathWatchCoordinator.Stop'
			, self.stop
		)

	def _watch_coordinator(self, watched_path, changes, *args, **kw):
		'''
		Filters through multitude of fired 'file changed' events
		and allows some of them to bubble up to consumer callbacks.

		Also restarts the path watch threads.
		'''
		# 1. Take a snapshot of callback-filter listenning on the watched_path
		# 2. If there are listeners, spin up new watch thread.
		# 2. Go over each (callback, filter_regex) pair and 
		# 3. loop over changed entries, testing against regex and
		# 4. create new Change[] for each callback.
		# 5. when done looping, fire all callbacks.

		# copying the list of callbacks
		with self.paths_lock:
			callbacks = self.paths.get(watched_path, set()).copy()

		if callbacks:
			events.publish(
				'PathWatchCoordinator.StartPathWatchRunner'
				, watched_path
			)
		else:
			return

		with self.filters_lock:
			filters = [(self.filters[c], c, []) for c in callbacks if c in self.filters]

		# loop over changes and check each change against the regex filter.
		# if matches, add to that filter's change collection.
		for p, c, a in changes:
			# changes is an array of tuples
			# [(watched_path, changed_path, change_action),...]
			# change is (watched_path, changed_path, change_action)

			# if the actual watched folder is deleted
		 	if c == '' and a == 'Deleted':
		 		# for now let's stop trying to watch it.
		 		# in the future think about switching to long-poll
		 		# and reconnecting when it reappears.
		 		with self.paths_lock:
					del self.paths[watched_path]
			
			if self.recently_fired.get(os.path.join(p,c) + ":" + a, 0) > time.time() - 2:
				continue
			else:
				self.recently_fired[os.path.join(p,c) + ":" + a] =  time.time()

			# now the main event:
			for regexcollection, callback, array in filters:
				append = False
				for regex, tone in regexcollection:
					# tone is either True or False, which stands for 
					# "Regex must match" or "Regext must NOT match" respectively.
					# example: ('\.git/', False)
					# if regex mathches, it's True, and compared to False it fails the test.
					# Only when a given regex + tone yield a match, we signal up.
					# if not tone:
					# logging.debug(HELLO + "testing regex %s on %s" % ( regex, c) )
					if bool(re.search(regex, c)):
						append = tone
						# logging.debug(HELLO + "matched regex %s on %s" % ( regex, c) )
						break

				if append:
					array.append({
						'domain': p
						, 'path': c
						, 'change': a
					})

		for regex, callback, changes in filters:
			if changes: # is not empty
				th = threading.Thread(
					target = callback
					, args = [changes]
				)
				th.daemon = True
				th.start()


	def _watch_runner(self, path):
		# we are never called directly, always through eventing system.
		# this means we are already in a separate, 'daemon' thread.
		# we can block

		# th = threading.Thread(
		# 	target = watch_path
		# 	, args = (
		# 		path
		# 		, functools.partial( self._watch_coordinator, path ) # this locks watched_path as first arg.
		# 	)
		# )
		# th.daemon = True
		# th.start()

		watch_path(
			path
			, functools.partial( self._watch_coordinator, path ) # this locks watched_path as first arg.
		)


	def watch(self, path, filter_regex, callback):
		'''
		Tell what path to watch. 

		Do it over events.publish('PathWatchCoordinator.Watch', path, filter_string )

		@param {String} path Path of the folder to watch_path
		@param {RegExOb[]} filter_regex An array of pairs of (Python-style regular expression, True/False for "must match" or "must NOT match") to be applied as filter againts the paths of the changed files. Applied only to the portion of the path AFTER the base, watched folder name. Each pair is evaluated in order, looking for first combined true value. Include `(".*",true)` as the last entry on the list to pick up all changes.
		@param {Callback} callback Function to be called with Change[] (Array of Change objects)
		'''
		with self.paths_lock:
			callbacks = self.paths[path] = self.paths.get(path, set())
			callbacks.add(callback)

		with self.filters_lock:
			self.filters[callback] = filter_regex

		logging.debug('PathWatchCoordinator: watching %s' % path)

		events.publish(
			'PathWatchCoordinator.StartPathWatchRunner'
			, path
		)

	def stop(self, path, filter_regex, callback):
		'''
		Tell us to stop watching a path.
		Stops the watcher for a particular path and callback

		Do it over events.publish('PathWatchCoordinator.Stop', path, filter_string )

		@param {String} path Path of the folder to watch_path
		@param {RegExOb[]} filter_regex An array of pairs of (Python-style regular expression, True/False for "must match" or "must NOT match") to be applied as filter againts the paths of the changed files. Applied only to the portion of the path AFTER the base, watched folder name. Each pair is evaluated in order, looking for first combined true value. Include `(".*",true)` as the last entry on the list to pick up all changes.
		@param {Callback} callback Function that was passed to 'Start'.
		'''
		with self.paths_lock:
			logging.debug(HELLO + "trying to stop: %s" % str( self.paths[path]) )
			callbacks = self.paths.get(path)
			if callbacks and callback in callbacks:
				callbacks.remove(callback)


def test():
	import tempfile
	import shutil
	import pubsub

	watched_path = tempfile.mkdtemp()
	print "Temp folder: " + watched_path

	events = pubsub.PubSub()
	w = WatchCoordinator(events)

	def display_changes(watch_path, changed_path, change_action):
		print "Watched path '%s'\nChanged path '%s'\nChange action '%s'" % (watch_path, changed_path, change_action)

	token = events.subscribe(
		'TaskHive.1.PathWatcher.1'
		, display_changes
	)

	try:
		th = w.watch(watched_path, token['topic'])
		l = threading.Event()
		l.clear()
		l.wait(2)
		open(watched_path+'/testfile.txt','w').write('')
		l.wait(50)
	except Exception, e:
		raise
	finally:
		try:
			shutil.rmtree(watched_path)
		except:
			print "were not able to remove '%s'" % watched_path

if __name__ == "__main__":
	test()
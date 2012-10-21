from __future__ import absolute_import, division, with_statement

import os
import threading

from .dirsnapshot import DirectorySnapshot

LOOP_TIME_IN_SECONDS = 2

# the function is ran inside of a Thread with daemon = True
# so, don't worry about blocking.
def watch_path(watched_path, callback):
	if not os.path.isdir(watched_path):
		callback( [(watched_path, '', 'Deleted')] )
		return

	old = DirectorySnapshot(watched_path)

	ev = threading.Event()
	ev.clear()
	while not ev.is_set():
		ev.wait(LOOP_TIME_IN_SECONDS)
		new = DirectorySnapshot(watched_path)
		diff = new - old
		if diff:
			callback(diff)
			ev.set()
		old = new

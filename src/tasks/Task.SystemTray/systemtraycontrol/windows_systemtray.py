from __future__ import absolute_import, division, with_statement

import os
import threading

from components import APP_NAME

from .windows_core import SysTrayIcon
from .menu import menu, onexit

LOCAL_PATH = os.path.abspath(os.path.dirname(__file__))

class SystemTrayControl(object):
	def __init__(self, menu = menu, exit_handler = onexit):
		# self.menu = menu

		self.control = SysTrayIcon(
			LOCAL_PATH + os.path.sep + 'logo.ico'
			, APP_NAME
			, menu
			, on_quit = exit_handler
			, default_menu_index = 0 # top-most.
		)

	def start(self):
		th = threading.Thread(
			target = self.control.start
		)
		th.daemon = True
		th.start()

# Minimal self test. You'll need a bunch of ICO files in the current working
# directory in order for this to work...
if __name__ == '__main__':

	def hello(control):
		print("Hello to you!")

	def open_file_through_association(control):
		os.startfile(LOCAL_PATH + os.path.sep + 'index.html')

	menu_options = (
		('Say Hello', None, hello),
		('Configure %s' % APP_NAME, None, open_file_through_association),
		# ('A sub-menu', None,
		# 	(
		# 		('Say Hello to Simon', None, hello),
		# 	)
		# )
	)
	
	c = SystemTrayControl(menu_options)

	ev = threading.Event()
	ev.clear()

	th = threading.Thread(target = c.start)
	th.daemon = True
	th.start()

	while True:
		ev.wait(10)
		print("main loop...")

	print "done with SysTrayIcon call"
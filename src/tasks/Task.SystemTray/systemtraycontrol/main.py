from __future__ import absolute_import, division, with_statement

# from components import events

from components import systemtools

def get_system_tray_controller():
	MODE = systemtools.MODE

	SystemTrayControl = None

	if MODE == 'Windows':
		try:
			from .windows_systemtray import SystemTrayControl
		except ImportError:
			pass

	elif MODE == 'Linux':
		# There are 3 choices there, Gnome systray, Ubuntu systray, KDE plasmoid.
		# TODO: implement
		pass

	return SystemTrayControl
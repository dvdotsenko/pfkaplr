from __future__ import absolute_import, division, with_statement

try:
	from .growl import Notificator
except:
	try:
		from .pynotify import Notificator
	except:
		from .base import Notificator

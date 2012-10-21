from __future__ import absolute_import, division, with_statement

from components import APP_NAME
from components import systemtools
from components import events

def configure(*args, **kw):
	events.publish('Application.Configuration.Show')

def onexit(*args, **kw):
	events.publish('Application.Exit')

menu = (
	('Configure %s' % APP_NAME, None, configure),
	# ('A sub-menu', None,
	# 	(
	# 		('Say Hello to Simon', None, hello),
	# 	)
	# )
)
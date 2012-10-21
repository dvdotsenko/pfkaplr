# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, with_statement

# these are "singletons" - once instance per whole app.
# reimporting them gets you same instance.

from .storage_instantiator import storage_singleton as storage

APP_NAME = 'PFKAPLR'
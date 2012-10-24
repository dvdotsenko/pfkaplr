# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, with_statement

import os
import platform
import re

from .appname import APP_NAME

MODE = platform.system()

DATA_FOLDER_NAME = APP_NAME

# it it's not listed here, does noes not mean it's not supported.
# if it's listed, it means we have specialized code for that platform.
# rest goes with "generic code" bus.
if MODE not in ['Windows', 'Darwin', 'Linux']:
	MODE = 'Default'

_SHELL_VAR_SIGNATURE = {
	'Windows' : re.compile('%(\w+)%', re.UNICODE)
	, 'Default' : re.compile('\$(\w+)', re.UNICODE)
}

_APP_DATA_FOLDER = {
	'Windows' : r'%APPDATA%/' + DATA_FOLDER_NAME
	, 'Default' : r'~/.' + DATA_FOLDER_NAME
	, 'Darwin' : r'~/Library/' + DATA_FOLDER_NAME
}

def _replace_shell_vars(matchobj):
	match = matchobj.group(1) # just the name of the var, sans decor
	# if environ does not have this env, we return back full string, including decor.
	# effectively, "not expanding unknown env vars"
	return os.environ.get(match, matchobj.group(0))

def normalize_path(path):
	# 1. expand vars
	# 2. expand ~
	# 3. normalize
	path = ( _SHELL_VAR_SIGNATURE.get(MODE) or _SHELL_VAR_SIGNATURE['Default'] ).sub(
		_replace_shell_vars
		, path
	)
	path = os.path.expanduser(path)

	ending = path[-1]
	return os.path.normpath(path) + (ending in '\\/' and os.path.sep or '' )

def get_app_data_folder():
	return normalize_path(
		_APP_DATA_FOLDER.get(MODE) or _APP_DATA_FOLDER['Default']
	)

def test():
	print normalize_path(
		'~/' + \
		'%WINDIR%/' + \
		'%DOesNotExist%\\' + \
		'asdf/qwer\\zxvc\\'
	)

	print get_app_data_folder()

if not os.path.isdir( get_app_data_folder() ):
	os.mkdir( get_app_data_folder() )

if __name__ == "__main__":
	test()
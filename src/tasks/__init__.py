# -*- coding: utf-8 -*-
import os
import imp
import re
import zipfile
import logging
import sys

if getattr(sys, 'frozen', None):
     built_in_tasks_folder = sys._MEIPASS
else:
     built_in_tasks_folder = os.path.dirname(__file__)

import components.systemtools

def tasks_iter():
	skip_pattern = re.compile('(Task\.Example\.py)')

	appdata_folder = components.systemtools.get_app_data_folder()
	user_tasks_folder = os.path.join(appdata_folder, 'tasks')

	if not os.path.isdir(user_tasks_folder) and \
		os.path.isfile(os.path.join( built_in_tasks_folder, 'tasks.zip')):
		with zipfile.ZipFile(os.path.join( built_in_tasks_folder, 'tasks.zip'), 'r') as taskszip:
		    taskszip.extractall(user_tasks_folder)
		tasks_folder = user_tasks_folder
	elif os.path.isdir(user_tasks_folder):
		tasks_folder = user_tasks_folder
	else:
		tasks_folder = built_in_tasks_folder

	for fn in os.listdir(tasks_folder): # user_tasks_folder):
		if fn.startswith('Task.') and not skip_pattern.search(fn):
			fn = os.path.join(tasks_folder, fn)
			if os.path.isdir(fn):
				module = imp.load_module(
					fn.replace('.','_')
					, None
					, fn
					, ('', '', imp.PKG_DIRECTORY)
				)

				logopath = os.path.join( fn, 'logo.svg')
				if os.path.isfile(logopath):
					try:
						with open(logopath) as logo:
							module.Task.LOGO = logo.read()
					except:
						pass

			# elif fn.endswith('.py'):
			# 	with open(fn, 'rb') as fp:
			# 		module = imp.load_module(
			# 			fn.replace('.py','').replace('.','_')
			# 			, fp
			# 			, fn
			# 			, ('.py', 'rb', imp.PY_SOURCE)
			# 		)
			if module:
				yield module.Task

if __name__ == "__main__":
	for task in tasks_iter():
		print task.ID

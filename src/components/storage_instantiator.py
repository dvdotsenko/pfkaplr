# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, with_statement
# import systemtools
import os
import json
import weakref
import threading
import logging
import re

from components import events

HELLO = "Storage.py: "

# this allows JSON / JavaScript basic types.
null = None
false = False
true = True
STARTING_VALUES = {
 "Task.Core.ConfigurationWebInterface_13495994978170.27492985455319285": {
  "inputs": [
   [
    null, 
    "Callback", 
    "callback", 
    "Function to be called (or passed to async delegate) when done"
   ]
  ], 
  "description": "Manage all aspects of hrough a graphical user interface.", 
  "consumers": [], 
  "outputs": [], 
  "label": "Configure", 
  "paused": false, 
  "tasktype": "Core.ConfigurationWebInterface", 
  "type": "Task", 
  "id": "Task.Core.ConfigurationWebInterface_13495994978170.27492985455319285"
 }, 
 "Task.Core.SystemTrayControls_13495995043540.15345499734394252": {
  "inputs": [
   [
    null, 
    "Callback", 
    "callback", 
    "Function to be called (or passed to async delegate) when done"
   ]
  ], 
  "description": "Allows you to control through a system tray icon.", 
  "consumers": [], 
  "outputs": [], 
  "label": "System Tray Controls", 
  "paused": false, 
  "tasktype": "Core.SystemTrayControls", 
  "type": "Task", 
  "id": "Task.Core.SystemTrayControls_13495995043540.15345499734394252"
 },
 "TaskHive.Default": {
  "id": "TaskHive.Default", 
  "tasks": [
    "Task.Core.ConfigurationWebInterface_13495994978170.27492985455319285",
    "Task.Core.SystemTrayControls_13495995043540.15345499734394252"
  ] , 
  "type": "TaskHive", 
  "description": "We start services that are relied upon by all task groups. For project-specific task group, make another Task Hive and put your project tasks in there..", 
  "label": "Global Tasks"
 }
}

def deep_update(target, update):
	things_changed = False
	try:
		for key in update:
			newupdate = update[key]
			newtarget = target[key] = target.get(key, {})
			if isinstance(newupdate, dict):
				if isinstance(newtarget, dict):
					things_changed = things_changed | deep_update(newtarget, newupdate)
				else:
					raise Exception('Cannot merge dictionary into non-dictionary.')
			else: # new value is NOT dictionary. This is the end of our traversal.
				oldvalue = target[key]
				target[key] = newupdate
				things_changed = things_changed | ( json.dumps(oldvalue) != json.dumps(newupdate) )
		return things_changed
	except Exception as ex:
		logging.debug(HELLO + "Target, Update are %s\n%s" % (target, update))
		raise ex

class StorageBackend_File(object):

	def __init__(self):
		self.file = os.path.join( os.getcwd(), 'database.json' )
		self.file_lock = threading.Lock()
		self.all = STARTING_VALUES
		self.all_lock = threading.Lock()

		if not os.path.isfile(self.file):
			self.save_to_file()

		self.load_from_file()

	def load_from_file(self):
		try:
			with self.file_lock:
				with open(self.file, 'rb') as fn:
					self.all.update( json.load(fn) )
		except:
			pass

	def save_to_file(self):
		with self.file_lock:
			with open(self.file, 'wb') as fn:
				json.dump(self.all, fn, indent=True)

	def get_keys(self):
		return self.all.keys()

	def query_keys(self, query_string):
		'''
		@param {Regex} filter Regular expression to be applied against each key in the data storage system.

		@returns {String[]} List of keys matching that filter.
		'''
		refilter = re.compile(query_string)
		return [key for key in self.all.keys() if refilter.search(key)]

	def get_value(self, key, default = None):
		return self.all.get(key, default)

	def get_pairs(self, keys):
		return [value for value in [self.all.get(key, None) for key in keys] if value ]

	def get_values(self, keys):
		return [value for value in [self.all.get(key, None) for key in keys] if value ]

	def set(self, key, value):
		with self.all_lock:
			if value == None:
				if key in self.all:
					del self.all[key]
			else:
				self.all[key] = value
		self.save_to_file()

class Storage(object):

	# def _save_object_handler(self, object, *args, **kw):
	# 	print "Faking 'save_object' action for object '%s'. Implement me" % object.name

	def __init__(self):
		self.storagebackend = StorageBackend_File()
		self.subscribers = {'change':{}, 'set':{}}

		self._change_lock = weakref.WeakValueDictionary()

		events.subscribe(
			'Storage.Set'
			, self.set
		)

		events.subscribe(
			'Storage.Get'
			, self.get
		)

		events.subscribe(
			'Storage.Query'
			, self.query
		)

		events.subscribe(
			'Storage.Change'
			, self.change
		)

		events.subscribe(
			'Storage.On'
			, self._data_events_subscribe
		)

	def set(self, name, obj, callback = None):
		self.storagebackend.set(name, obj)

		if callback:
			callback(obj)

		# emit signal to listeners that certain object changed.
		change = self.subscribers['set']
		logging.debug(HELLO + "set for name '%s' filters: %s" % (name, change.keys()) )
		for filterdef in change.keys():
			if re.search(filterdef, name):
				filterlisteners = change.get(filterdef)
				logging.debug(HELLO + "set listeners: %s" % filterlisteners)
				# weakref callbacks went poof, but filter is around.
				# cleaning up.
				if not filterlisteners:
					del change[filterdef]
				else:
					for callback in filterlisteners:
						callback(name, obj)

	def get(self, name, default = None, callback = None):
		value = self.storagebackend.get_value(name, default)
		if callback:
			callback(value)
		else:
			return value

	def query(self, query_string, callback = None, **flags):
		logging.debug(HELLO + " query string is '%s'" % query_string)
		values = self.storagebackend.get_values(
			self.storagebackend.query_keys(query_string)
		)
		if callback:
			callback(values)
		else:
			return values

	def change(self, name, changes, callback = None):
		changed = []
		obj = self.storagebackend.get_value(name)
		lock = self._change_lock[name] = self._change_lock.get(name) or threading.Lock()

		with lock:
			for change in changes:
				if deep_update(
					obj
					, change
				):
					changed.append(change)
			if changed:
				self.storagebackend.set(name, obj)

		if callback:
			callback(name, obj, changed)

		if changed:
			# emit signal to listeners that certain object changed.
			change = self.subscribers['change']
			for filterdef in change.keys():
				logging.debug(HELLO + "change for name '%s'. Comparing to filter: %s" % (name, filterdef) )
				if re.search(filterdef, name):
					filterlisteners = change.get(filterdef)
					logging.debug(HELLO + "change listeners len: %s, list: %s" % ( len(filterlisteners), filterlisteners) )
					logging.debug(HELLO + "change is %s" % changed)
					# weakref callbacks went poof, but filter is around.
					# cleaning up.
					if filterlisteners:
						for callback in filterlisteners:
							callback(name, obj, changed)
							logging.debug(HELLO + "fired change callback for %s" % name)

	def _data_events_subscribe(self, eventtype, filterdef, callback):
		'''Similar to jQuery's "live" or "delegate" event subscriptions.

		Global 'events' PubSub does not support filters. 
		We need domain-specific filters here, i think.

		Also, there is NO unsubscribe. No need. We store the callback as weakref.
		This means that listenner needs to store a hard ref somewhere,
		otherwise callback goes auto-poof.

		@param {String} eventtype One of following supported strings 'change', 'set'
		@param {String} filterdef A string with regex to be applied to the ID of the changed element.
		@param {Callback} callback A callable to call when matching event occurs.
		'''
		# we allow you to go nuts with creative event names.
		# we just will not trigger those we don't support yet.
		eventtypeobj = self.subscribers[eventtype] = self.subscribers.get(eventtype, {})
		filterlisteners = eventtypeobj[filterdef] = ( eventtypeobj.get( filterdef ) or set() )
		filterlisteners.add(callback)

# it's a singleton. Shared by all importers.
storage_singleton = Storage()
# get = storage_singleton.get
# set = storage_singleton.set
# query = storage_singleton.query
# change = storage_singleton.change

def test_deep_update():
	chs = [{"inputs": [[".", "String", "path","Filesystem path to watched folder"], [[["\\.git/|\\.svn/|\\.bzr/|\\.pyc$", false], [".*", true]], "RegExObj[]", "filter_regex", "An array of pairs of (Python-style regular expression, True/False for \"must match\" or \"must NOT match\") to be applied as filter againts the paths of the changed files. Applied only to the portion of the path AFTER the base, watched folder name. Each pair is evaluated in order, looking for first combined true value. Include `(\".*\",true)` as the last entry on the list to pick up all changes."], [null, "Callback", "callback", "Function to be called (or passed to async delegate) when done"]]}]
	a = {'inputs':[], 'a':1}
	for ch in chs:
		deep_update(a,ch)
	print json.dumps(a)

def test():
	logging.basicConfig(level=logging.DEBUG)
	s = Storage()
	assert len( s.query('^TaskHive') ) == 1

if __name__ == '__main__':
	test_deep_update()
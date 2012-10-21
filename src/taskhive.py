# -*- coding: utf-8 -*-
'''
TaskHiveCoordinator listens on some channels and funnels signals to right TaskHive instances. 
TaskHive instances, in-turn, decide what to do when they are poked with a particular event.
TaskHiveCoordinator is a way to "broadcast" to TaskHive instances something.

TaskHive instances normally don't get signals from outside. They control the flow through
issuing a task and passing in a callback to be called when task is done. The callback call
takes the flow back to TaskHive instance, which decides what to do next. TaskHive keeps the
list of what Tasks are connected to it and what args it has to pass around them.
 
TaskHives are "read" from some storage and kept as refs on TaskHiveCoordinator. TaskHiveCoordinator
receives calls for creation of new TaskHives (and stores them transparenlty).

Hence:
1. spin up TaskHiveCoordinator (and attach listeners to PubSub)
2. resurrect TaskHive inventory
'''

import uuid
import threading
import weakref
import logging
from functools import partial as bind

import tasks as TaskTypes
from components import toposort
from components import events
from components import storage

HELLO = "TaskHive.py: "

TASKHIVE_DEFAULT_DATA = {
	'label': '(name this task hive)'
	, 'description': '(some description would not hurt)'
	, 'type': 'TaskHive'
}

class TaskHive(object):

	def __init__(self, tasktypes, taskhive_metadata = None):
		self.get_tasktypes = weakref.ref( tasktypes )

		changed = False

		if not taskhive_metadata:
			taskhive_metadata = TASKHIVE_DEFAULT_DATA.copy()
			changed = True
		if 'tasks' not in taskhive_metadata:
			taskhive_metadata['tasks'] = []
			changed = True

		if 'id' in taskhive_metadata:
			self.id = taskhive_metadata['id']
		else:
			self.id = taskhive_metadata['id'] = taskhive_metadata['type'] + '.' + str(uuid.uuid1())
			changed = True

		self._running_tasks = weakref.WeakKeyDictionary()
		self._running_tasks_map = weakref.WeakValueDictionary()
		# used by self._hive_tasks_change_handler
		self._tasks = set(taskhive_metadata.get('tasks', []))
		# we are watching on Storage.
		# there, it stores callbacks as weak refs.
		# this means we have to keep a ref to callback locally as long
		# as we care about this task
		self._taskswatchers = {}
		self._taskswatchers_lock = threading.Lock()

		if changed:
			storage.set(self.id, taskhive_metadata)

		if not bool(taskhive_metadata.get('paused')):
			self.start()

		self.hive_change_handlers = {
			'tasks': self._hive_tasks_change_handler
		}

		# listen for changes to self
		events.publish(
			'Storage.On'
			, 'change'
			, r'^' + self.id.replace('.',r'\.') + r'$'
			, self._hive_change_handler
		)


	@property
	def is_paused(self):
		return bool(storage.get(self.id).get('paused'))

	def start(self):
		# 1. Determine the order of tasks
		# 2. Spin up first task, passing
		#  a. Args from storage
		#  b. and callback to what to do after it's done.

		# Task runner positions recorded in Hive roster don't have "require" or "depends on"
		# What is stored along with Tasks's ID is a list of "consumers" - 
		# 'I hand over control to these task IDs after I am done'
		# This is done so that when a long-running task completes, and its rules
		# were rewritten while it ran, instead of rescanning the whole task tree
		# and figuring out who now depends on it, the task's locker at this Hive will
		# have a list of who to talk to next.

		# The Task.REQUIRE list burned into each task should not bother us now, 
		# as that is a list of other components this task "needs to be around in general"
		# I would assume these were ran by tasks initializer at the start of server run, 
		# Once these are *inited* in order, they should be designed to be *ran()* async

		# But, for first run, we need the opposite data - which of the tasks don't have parents.
		# we start them all simultaneously

		logging.debug(HELLO + "Initing TaskHive %s" % self.id)

		parent_count = {}
		task_ids = storage.get(self.id).get('tasks', [])

		# this loop marks task runners that depend on other runners
		# we also use the looping opportunity to set up Strorage event watches.
		for task_id in task_ids:
			self._add_to_watched_tasks(task_id)

			for consumer in storage.get(task_id,{}).get('consumers',[]):
				parent_count[consumer] = parent_count.get(consumer, 0) + 1
		
		already_running = self._running_tasks_map.keys() 
		# here we run only those of them that do NOT have parents or are not already running.
		for task_id in task_ids:
			task_data = storage.get(task_id)
			if task_data and not parent_count.get(task_id) and task_id not in already_running:
				self.run_task(task_id, task_data)

	def stop(self):
		for callback in self._running_tasks.keys():
			if callback:
				task_id, kw = self._running_tasks.get( callback, ['', {}] )
				tasktype = self.get_tasktypes().get(storage.get(task_id, {}).get('tasktype','not to be found'))
				if tasktype and hasattr(tasktype, 'stop'):
					kw['callback'] = callback
					try:
						tasktype.stop(**kw)
					except Exception as ex:
						logging.debug(HELLO + "Stopping task '' errored out with ''" % (tasktype.ID, ex.message))

	def stop_task(self, taskid):
		was_running = False

		callback = self._running_tasks_map.get(taskid)
		
		if callback:
			stored_taskid, kw = self._running_tasks.get(callback, ['', {}])
			tasktype = self.get_tasktypes().get(storage.get(stored_taskid, {}).get('tasktype','not to be found'))
			if tasktype and hasattr(tasktype, 'stop'):
				kw['callback'] = callback
				try:
					tasktype.stop(**kw)
					was_running = True
				except Exception as ex:
					logging.debug(HELLO + "Stopping task '' errored out with ''" % (tasktype.ID, ex.message))

		return was_running

	def _task_change_handler(self, bindtoken, taskid, metadata, changes):
		# we are doing a bind higher to create a new instance of callback
		# so that we can rely on weakref autocleanup when we drop that instance.
		# the bindtoken is a throwaway value we needed to bind.
		for change in changes:
			# change is supposed to have only one change path,
			# but just in case we will loop.
			if 'inputs' in change or 'pause' in change:
				if ( self.stop_task(taskid) or not self._get_task_parents(taskid) ) and not metadata.get('paused'):
					self.run_task(taskid, metadata)

	def _add_to_watched_tasks(self, taskid):
		callback = None
		with self._taskswatchers_lock:
			if not taskid in self._taskswatchers:
				callback = self._taskswatchers[taskid] = bind(self._task_change_handler, taskid)
		if callback:
			events.publish(
				'Storage.On'
				, 'change'
				, r'^' + taskid.replace('.',r'\.') + '$'
				, callback
			)

	def _get_task_parents(self, taskid):
		parents = []
		for tid in self._tasks:
			parenttask = storage.get(tid)
			if 'consumers' in parenttask and taskid in parenttask['consumers']:
				parents.append(tid)
		return parents

	def _hive_tasks_change_handler(self):
		# we store a local copy of tasks roster between handler runs.
		# this is done so that repeat, or snoball calls don't restart
		# tasks needlessly.
		# here we only handle additions and removals of tasks.
		# individual task state changes are handled by other code.

		oldtasks = self._tasks
		self._tasks = newtasks = set( storage.get(self.id).get('tasks', []) )
		removed = oldtasks.difference(newtasks)
		added = newtasks.difference(oldtasks)

		for taskid in removed:
			with self._taskswatchers_lock:
				if taskid in self._taskswatchers:
					del self._taskswatchers[taskid] # callback goes poof on the other end.
			self.stop_task(taskid)

		for taskid in added:
			self._add_to_watched_tasks(taskid)
			if not self._get_task_parents(taskid) and not storage.get(taskid,{}).get('paused'):
				self.run_task(taskid, storage.get(taskid))

	def _hive_change_handler(self, taskhiveid, metadata, changes):
		# changes is an array of individual path-to-value dicts, one per each change.
		for change in changes:
			# change is supposed to have only one change path,
			# but just in case we will loop.
			for prop in change.keys():
				change_handler = self.hive_change_handlers.get(prop)
				if change_handler:
					change_handler()

	def process_callback(self, task_id, *args, **kw):
		'''
		This converts output arguments (those the done task pushed to the callback)
		into input arguments for each of the to-be-called-next task.
		'''
		#logging.debug(HELLO + "Processing callback on hive '%s' for args '%s'" % (self.id, args))

		donetask = storage.get(task_id)
		if not donetask:
			# which may happen if task was removed from the roster while it was running
			return

		# tasktypes = self.get_tasktypes()
		# donetasktype = tasktypes.get(donetask['type'])
		# if not donetasktype:
		# 	# kinda hard to imagine, but, heck..
		# 	return		

		consumers = [[consumer_id, storage.get(consumer_id)] for consumer_id in donetask.get('consumers',[])]

		if not consumers:
			return

		# Preassemblying input args.
		# in python, as long as you don't splat-collect args in the function,
		# all positional args can be pulled into dictionary and 
		# applied to the function as named args.
		# we rely on that here.
		# in other words, DO NOT USE SPLAT ("*args, **kw") in Task run() declaration.
		incoming_args_def = donetask.get('outputs',[])
		incoming_name_type_map = {}
		incoming_args = {}
		for arg in incoming_args_def:
			# arg is [default value, type, name, description]
			value, typename, name = arg[:3]
			if name in kw:
				incoming_args[name] = kw[name]
				incoming_name_type_map[name] = typename

		for arg_position in xrange(min( len(args), len(incoming_args_def) )):
			value, typename, name = incoming_args_def[arg_position][:3]
			# [default value, type, name, description]
			incoming_args[name] = args[arg_position]
			incoming_name_type_map[name] = typename


		# we allow task runners to push back updates to task records.
		# web server task can push back update to task label with
		# port number that was autopicked by the server. etc.
		updateargtype = 'MetadataUpdate'
		updateargname = updateargtype.lower()
		if updateargname in incoming_args and \
			incoming_name_type_map[updateargname] == updateargtype:
			storage.change(donetask.id, incoming_args[updateargname])
			del incoming_args[updateargname]

		for consumer in consumers:
			# consumer is an array [id, metadata object]
			if consumer[1]:
				self.run_task(
					consumer[0]
					, consumer[1]
					, task_id
					, incoming_args
					, incoming_name_type_map
				)

	def run_task(
		self, task_id, task_data, 
		incoming_task_id = 'no source task id', 
		incoming_args = {}, 
		incoming_name_type_map = {}
	):

		if task_data.get('paused'):
			return

		tasktype = self.get_tasktypes().get(
			task_data.get('tasktype','not to be found')
		)
		if not tasktype:
			storage.change(task_id, {'paused':True})
			return

		for name in incoming_name_type_map.keys():
			if incoming_name_type_map[name] == 'Args':
				# we have boxed args. need to unpack these.
				# Args are something like this:
				# [{
				#	'kw':{} # all incoming args are converted to kw because we know the declaration.
				#	'kw_types':{}
				#	'from':'long_id_of_task_runner_instance'
				#	'to':'long_id_of_task_runner_instance'
				# }, another one here ] 
				# Args are always unpacked and repacked at each hand-over point.
				# so there would not be a double-wrapping.
				kw = incoming_args[name].get('kw')
				kw_types = incoming_args[name].get('kw_types')
				del incoming_args[name]
				del incoming_name_type_map[name]
				kw.update(incoming_args)
				kw_types.update(incoming_name_type_map)
				incoming_args = kw
				incoming_name_type_map = kw_types

		outgoing_args = {}
		Args_packing_name = None
		for arg in task_data.get('inputs',[]):
			# arg is [default value, type, name, description]

			# the rules of args migration:
			# if consumer's arg definition has non-Null value, it wins
			# if it's Null, we look for similar name + type in incoming args and use that
			# Future TODO: if name + type did not match we try matching on "non-native" types (those not including String, Number, Object, Array, Int)
			#              if even 'non-native' type matching did not yield any matches, we use Null

			value, typename, name = arg[:3]

			if typename == 'Callback':
				callback = outgoing_args[name] = bind(self.process_callback, task_id)
			elif typename == 'Args':
				# we have to box args.
				# Args are something like this:
				# [{
				#	'kw':{} # all incoming args are converted to kw because we know the declaration.
				#	'kw_types':{}
				#	'from':'long_id_of_task_runner_instance'
				#	'to':'long_id_of_task_runner_instance'
				# }, another one here ] 
				# Args are always unpacked and repacked at each hand-over point.
				# so there would not be a double-wrapping.

				# long id is a combination of TaskHive ID + Task Run record ID.
				outgoing_args[name] = {
					'kw': incoming_args
					, 'kw_types': incoming_name_type_map
					, 'from': incoming_task_id + '@' + self.id
					, 'to': task_id + '@' + self.id
				}
			elif value == None and typename == incoming_name_type_map.get(name,'not to be matched'):
				# nice! arg name+type matches to incoming
				outgoing_args[name] = incoming_args.get(name)
			else:
				# either it's non-null, which is a proper outcome,
				# or it's null, but we are too lazy to do better matching and settle on default Null
				# either way,
				# using default value
				outgoing_args[name] = value

		# this is used for shutting long-running tasks down
		if hasattr( tasktype, 'stop' ) and 'callback' in outgoing_args:
			args_passed = outgoing_args.copy()
			del args_passed['callback']
			# _running... is Weakref dictionary. When last hard ref to
			# callback goes, so goes the _running.. entry.
			self._running_tasks[callback] = [ task_id, args_passed ]
			self._running_tasks_map[task_id] = callback

		logging.debug(HELLO + "Running '%s' task's runner for TaskHive '%s'" % (task_id, self.id))

		th = threading.Thread(
			target = tasktype.run
			, kwargs = outgoing_args
		)
		th.daemon = True
		th.start()

class TaskCollection(dict):
	'''
	Subclassing from Dictionary for only one reason:
	Want to store this structure as weakref, and dict's cannot be weakref
	But wrapped into subclass they can. So..
	'''
	pass

class TaskHiveCoordinator(object):
	'''
	This starts once by the server.
	This does NOT "run" (as in "thread") but is more like a reactive (has callback
	registered with PubSub) hash of hashes,	a reference tree of all TaskHives (NOT Tasks)

	The primary task of this is communicating to TaskHives when and if
	anybody cares about that TaskHive. (Channels call-backs, disables, enables hives)

	TaskHiveCoordinator does not keep track of tasks, but does help TaskHives manage
	tasks by funneling "general" taks-related events to and from TaskHives

	Example: TaskHiveCoordinator is called 
	when a general outside connection comes in from LiveReload Connection Acceptor Task.
	That connection needs to be tied to some TaskHive(s). TaskHiveCoordinator checks
	the "domain" lists on TaskHives. If some TaskHive allows communication with this "domain"
	TaskHiveCoordinator smiles and goes to sleep. Else, it asks the server-local notification
	system to prompt user to configure / connect this new connection.

	There TaskHive is the entity storing / keeping / managing its communication "domain" list.

	TaskHiveCoordinator IS THE PRIMARY REFERENCE TO ALL AVAILABLE TASKHIVES.
	'''
	def __init__(self):
		
		self.tasktypes = TaskCollection()
		for tasktype in self.tasktypes_iter():
			self.tasktypes[tasktype.ID] = tasktype

		events.publish(
			'TaskHiveCoordinator.TaskTypes.Changed'
			, self.tasktypes
		)

		self.taskhives = {}
		self.taskhives_lock = threading.Lock()
		for taskhive_data in storage.query(r'^TaskHive\..+'):
			taskhive_id = taskhive_data['id']
			self.taskhives[taskhive_id] = TaskHive( self.tasktypes, taskhive_data )

		# making listing of tasktypes available through pubsub system.
		events.subscribe('TaskHiveCoordinator.GetTaskTypes', self.get_tasktypes_metadata)

		events.publish(
			'Storage.On'
			, 'set'
			, r'^TaskHive\.'
			, self._hive_set_handler
		)

	def _hive_set_handler(self, taskhiveid, hivemetadata):
		# we only allow 'set' events on hives that either 
		# create or delete the hive.
		# change events are handled by hive itself.
		with self.taskhives_lock:
			if not hivemetadata and taskhiveid in self.taskhives:
				th = self.taskhives[taskhiveid]
				del self.taskhives[taskhiveid]
				th.stop()
				return

			if hivemetadata and taskhiveid not in self.taskhives:
				self.taskhives[taskhiveid] = TaskHive( self.tasktypes, hivemetadata )
				return

		logging.debug(HELLO + " HIVE SET EVENT IGNORED!!!")
	def get_tasktypes_metadata(self, callback):
		'''
		Used for communicating tasks metadata to controlling user interface.

		@param {Callback} callback Function to call with the output.

		@returns {Object} A key-value collection where key is the ID of the task type and the value is its METADATA object.
		'''
		callback([tasktype.METADATA for tasktype in self.tasktypes.values()])

	def tasktypes_iter(self):
		tasktypes = {}
		dependencies = {}
		for Task in TaskTypes.tasks_iter():
			tasktypes[Task.ID] = Task
			try:
				dependencies[Task.ID] = Task.REQUIRE
			except:
				dependencies[Task.ID] = []

		order = toposort.robust_topological_sort(dependencies)
		order.reverse()
		all_tasks = tasktypes.keys()

		# this actually inits the classes and yields the instances
		for task_group in order:
			if len( task_group ) != 1:
				raise Exception("Cannot have mutually-dependant Tasks. Not sure why yet, but I'll find a reason.")
			elif task_group[0] not in all_tasks:
				raise Exception("Task %s listed as a dependency is not found." % task_group[0])
			else:
				t = tasktypes[task_group[0]]()
				t.init()
				# what else t instances need? will add something in the future...
				yield t

# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, with_statement
'''
A task is an entry in a pile of entries.

Task class instance is designed to be a "runner representative."
Whenever possible, a task does NOT "run," it "starts the runner"
by calling out runner coordinators. When not possible, or when more practical
a Task does and can "run" but I will put on our "geek" glasses and will snarkly
point my finger at you for such uncool implementation.
In either case, at the end a "ready" callback to TaskHiveCoordinator is called
and some other Task acts on it.

A task does NOT know what starts after it's done. It also does NOT know what preceeds it.
Only TaskHive - a parent of all subservient task instances knows the ordering and
coordinates the callbacks.
This is somewhat similar to how you would declare tasks in "makefile" (and other build
automation systems), but you declare tasks individually and then link/order them through higher entity.

All tasks are tasks. Tasks marked ".template" at the end or ID string are not different from all others.
They are just not cleaned up when not linked to any TaskHive, and are shown on the list of 
available tasks. You can make any custom-built task a template task just by adding ".template"
to the module name.

Normally, a task is designed NOT to store its arguments. TaskHive - the parent - manages passing of the arguments
between tasks. However, nothing stops you from coding one Task that has input data hardcoded. You can
even make it a "template". In that case, TaskHive would just manage the ordering, but not the
arguments. Yet, you risk seeing me put on the geeky glasses again... :)

Tasks must expose common API that allows one to:
0. figure out how to display the task on task management UI (pretty name etc.)
1. figure out what arguments it takes (and have some "pretty" textual label for that too.)
2. figure out what outputs it produces (and have some "pretty" textual label for that too.)
3. run it with the args + callback pointer

Task should not care what "callback" does, short for passing into it the promissed outputs,
but what will likely happen inside of that callback is centralized pubsub sustem will be notified
on a particular channel (likely occupied by TaskHiveCoordinator) that certain Task belonging
to certain TaskHive is done and here are the outputs.

In other words, Task does NOT "return" output. It calls callback function with outputs.
In other words, noone "waits" for Task to "return" Proper handler is called async when and if it is done.

Task is always a Class. It's inited ONCE ever, generically by task inventory system without any inputs.
Task is then interrogated by the inventory system about 1,2,3 above.
Task's runner is then called again and again with new args, as needed.
It's likely that TaskHive will be calling the "run" but callbacks will be landing in TaskHiveCoordinator
'''

class TaskBase(object):

	# keep this for future compatibility with passing args to instantiator.
	def __init__(self, *args, **kw):
		pass

	### 
	# Public API:
	###

	# override these in your subclass

	# Override this with globally-unique ID, 
	# like "ABE8D500-FC33-11E1-98A4-001C230C8ABD" or unique meaningfull text
	# like "MySuperTask12341234-1234-1234" 
	# just DO NOT use dots (".") in it. We combine this ID with Type labels
	# to derive some "meaningfull" IDs and use dots to join the meaningfull parts.
	# It might be useful not no have space characters there either.
	# TaskHive arguments will be tied to this ID and the ID will be stored
	# between the server shutdown and start.
	# This also means that if you want to "upgrade" your Task in backward-INcompatible
	# way, just change the ID and server will forget all the settings it had
	# associated with this task.
	ID = 'OverrideMeInYourSub-Class'

	# you must override this one with your code
	def run(self, *args, **kw):
		raise NotImplementedError("Task %s needs 'run' method declared. See Task.Example.py" % self.id)

	# optional:
	# if your tasks are long-running or looping, or timer-based, declare a stop function
	# see Task.Example.py or Task.PathWatcher
	# if declared, it will be allowed to be called by user.
	# def stop(self, *args, **kw):
	# 	return

	# optional:
	# override this in your class instead of overriding the __init__()
	def init(self):
		'''
		Override me.

		Init is ran always, once by task inventory code after Task is instantiated
		and is dressed up with some useful properties, like references to PubSub system
		and such.

		This runs before "run()" is allowed to run. 

		Use this to set up things specific to the task (like separate long-running threads etc.)
		'''
		pass

	# optional:
	# declare function callback if you call the "done" callback with arguments.
	# see Task.Example.py for explanation.
	# lack of one means, you don't pass any args to the "done" callback.

	# optional:
	# override this in your class instead of overriding __del__
	def dispose(self):
		'''
		Override me.

		task inventory tries to make the best effort to run this before shutting down
		the server. Still, we don't guarantee that this code will run. 

		If you use same paths or resources for this task, and need to 'clean up', do 
		a preventive clean up in `init()` and optimistic clean up here in `dispose()`
		'''
		pass

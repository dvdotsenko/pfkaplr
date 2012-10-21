;(function() {

function EnvInit(events){
	var CALLSERVER = 'WSBridge.Call'
	, NOTIFYSERVER = 'WSBridge.Notify'
	, SUBSCRIBESERVER = 'WSBridge.Subscribe'

	if (!window.my) {
		window.my = {}
	}

	Backbone.sync = function (method, model, options){
		console.log('!!! Backbone.sync !!! We should never run. Investigate.', arguments)
		options.success(model.toJSON())
	}

	var Argument = Backbone.Model.extend({
		'defaults':{
			'value': null
			, 'type': '(not defined)'
			, 'name': '(not defined)'
			, 'description': '(not defined)'
		}
	})

	var Arguments = Backbone.Collection.extend({
		'model': Argument
		, 'url':'ArgumentCollection'
	})

	// TaskTypes and Task instances differ in only one respect:
	// 'id' prop on Task instance is altered and unique, 
	// likely a derivative or TaskType's id, from which the Task instance was cloned.
	// Task.id is never set on init, as Task instance is always a CLONE of parent + altered ID
	var Task = Backbone.Model.extend({
		// defaults object is coppied shallow
		// meaning anything that is copied by ref
		// will be shared to clones. 
		// No use Array, Object in defaults, you hear?!
		'defaults': {
			'id': undefined
			, 'type': 'Task'
			, 'tasktype': undefined
			// , 'inputs': [] 
			// , 'outputs': []
			// , 'consumers': []
			, 'paused': false
		}
		, 'initialize': function(){
			this.parents = ( this.parents || [] )
			// these are `link` Obj refs from us to consumers.
			// we store these for ease of clean up when we are
			// deleted. alllinks.indexOf(ref) is much faster than looping.
			this._links = ( this._links || {} )
			this.attributes.consumers = ( this.attributes.consumers || [] )
			//this.on('all',function(){console.log('task all', this.id, arguments)})
			this.on('change', function(model, options){
					this.save(null, {'changed': options.changes})
				}
			)
		}
		, 'getinputs': function (){
			if (!this._inputs) {
				var task = this
				var inputs_collection_base = []
				var map = {'value': 0, 'type': 1, 'name': 2, 'description': 3}
				_.each(task.attributes.inputs || [], function(data, i){
					var type = data[map['type']]
					if (type !== 'Callback' && type !== 'Args') {
						inputs_collection_base.push({
							'id': i
							, 'value': JSON.stringify( data[map['value']] )
							, 'type': type
							, 'name': data[map['name']]
							, 'description': data[map['description']]
						})						
					}
				})
				task._inputs = new Arguments(inputs_collection_base)
				.on('change', function(model, options){
					// setTimeout(
						(function(id, value, task){ return function(){
							// console.log("Arguments changed", task, id, value)
							// need to change the ref to force 'change' event to bubble up.
							var inputs = Array.prototype.slice.call( task.get('inputs') || [] )
							inputs[id] = Array.prototype.slice.call( inputs[id] )
							inputs[id][0] = JSON.parse( value )
							task.set('inputs',  inputs )

						}})(model.id, model.attributes.value, task)()
					// 	, 0
					// )
				})
			}
			return this._inputs
		}
		, 'checkIfRunonceCompatible': function(){
			// var inputs = this.getinputs()
			// , compatible = ( this.parents && this.parents.length )

			// inputs.each(function(model){
			// 	if (
			// 		model.attributes.value === null || 
			// 		model.attributes.value === undefined ||
			// 		model.attributes.value === 'null'
			// 	){
			// 		compatible = false
			// 	}
			// })
			// // all args have preset values.
			// return compatible
			return false
		}
		, 'sync': function (method, model, options){
			console.log('task sync', this, arguments)
			if (method === 'update') {
				// if changes are known, let's push only changes to the server.
				// otherwise whole task metadata is overwritten.
				if (options.changed && Object.keys(options.changed).length) {
					var changed = Object.keys(options.changed).map(function(name){
						var base = {}
						base[name] = model.get(name)
						return base
					})
					events.publish(
						NOTIFYSERVER
						, 'Storage.Change'
						, model.id
						, changed
					)
				} else {
					events.publish(
						NOTIFYSERVER
						, 'Storage.Set'
						, model.id
						, model.toJSON()
					)
				}
			} else if (method === 'delete') {
				events.publish(
					NOTIFYSERVER
					, 'Storage.Set'
					, model.id
					, null
				)
			} else {
				console.log("In sync hanlder for Task model. Unrecognized method '"+method+"' received. Ignoring.")
			}
		}
	})

	var AllTasksCollection = Backbone.Collection.extend({
		'model':Task
		, 'initialize': function(){
			// this.on('all', function(model, collection, options){
			// 	console.log('task own all:', arguments)
			// })
			// this.on('all',function(){console.log('AllTasksCollection all', this, arguments)})
			// this.on('add',function(model, collection, options){
			// 	model.save()
			// })
		}
		, 'sync': function (method, model, options){
			if (method === 'read') {
				events.publish(
					CALLSERVER
					, 'Storage.Query'
					, '^Task\\.' // we need "^Task\." for Python's regex, but JS needs that slash escaped.
					, options.success
				)
			} else if (method === 'update') {
				events.publish(
					NOTIFYSERVER
					, 'Storage.set'
					, model.id
					, model.toJSON()
				)
			} else if (method === 'delete') {
				events.publish(
					NOTIFYSERVER
					, 'Storage.set'
					, model.id
					, null
				)
			} else {
				console.log("In sync hanlder for TaskType model. Unrecognized method '"+method+"' received. Ignoring.")
				options.error("We don't accept methods other than 'update'")
			}
		}
	})
	var alltasks = window.my.at = new AllTasksCollection()
	alltasks.fetch()

	var TaskTypes = Backbone.Collection.extend({
		'model':Task
		, 'sync': function (method, model, options){
			if (method === 'read') {
				// options.success = (function(successcallback, collection){
				// 	return function(data){
				// 		successcallback(data)
				// 		collection.trigger(
				// 			'change'
				// 			, collection
				// 			, {'changes':{'models':true}}
				// 		)
				// 	}
				// })(options.success, this)
				events.publish(
					CALLSERVER
					, 'TaskHiveCoordinator.GetTaskTypes'
					, options.success
				)
			} else {
				console.log("In sync hanlder for TaskTypes collection. Unrecognized method '"+method+"' received. Ignoring.")
				options.error("We don't accept methods other than 'read'")
			}
		}
	})
	var tasktypes = window.my['tt'] = new TaskTypes()
	tasktypes.fetch()


	var GenericTaskCollection = Backbone.Collection.extend({
		'model':Task
		, 'initialize': function(){
			// this.on('all', function(model, collection, options){
			// 	console.log('task own all:', arguments)
			// })
			this.on('change:consumers', function(model){
				// here we are handling unsightly clean up:
				// - internal ._links collection
				// - .parent param on model
				// Proper param changes (like for 'consumers' set/get)
				// are done in 'add' 'remove' handlers somewhere.
				//console.log('task own ch:consumers:', arguments, model.previous('consumers'))
				// var previous = model.previous('consumers') || []
				
				// we only do this when .getlinks() was called already once.
				if (this._links) {
					// we don't trust "previous" cause events fire more than once.
					var alllinks = this._links
					var collection = this
					var oldconsumers = Object.keys( model._links )
					var newconsumers = ( model.attributes.consumers || [] )
					var removed = _.difference(oldconsumers, newconsumers)
					var added = _.difference(newconsumers, oldconsumers)
					
					removed.forEach(function(id){
						// removing the links entries
						var link = model._links[id]
						var index, child
						if (link && ( index = alllinks.indexOf(link) ) !== -1 ) {
							delete model._links[id]
							alllinks.splice(index, 1)
						}

						// reaching into children and cleaning up their
						// .parents entry. There is a reference in 'link'
						// object, but we don't trust it anymore.
						if (child = collection.get(id)) {
							var parents = ( child.parents || [] )
							if ( (index = parents.indexOf(model.id)) !== -1 ) {
								parents.splice(index, 1)
							}						
						}
					})

					added.forEach(function(id){
						var child 
						if (child = collection.get(id)) {
							// adding global links
							alllinks.push(
								model._links[id] = {'source':model, 'target':child}
							)

							// adding to child's "parents" list
							var parents = ( child.parents || [] )
							if ( parents.indexOf(model.id) === -1 ) {
								parents.push(model.id)
							}
						}
					})
				}
			})
		}
		, 'getlinks': function(){
			if (!this._links) {
				// returns array with Objects conforming to
				// d3's Force Links collection (https://github.com/mbostock/d3/wiki/Force-Layout#wiki-links)
				// where child and parent nodes are linked as such:
				// [{'source':parent_model, 'target':child_model}, ... ]
				// some of our tasks have .consumers = [id, id, ...] property
				// we generate link objects based on that.
				// for ease of parent link management, we also 
				// stick a 'parents' prop onto module instance = [id, id, ...]

				var links = []
				, collection = this
				this.each(function(model){
					model.attributes.consumers.forEach(function(id){
						// we are "parent" linking "children" to us
						var child = collection.get(id)
						child.parents.push(model.id)
						var link = {
							'source': model
							, 'target': child
						}
						links.push(link)
						model._links[id] = link // "Links to US" see note above.
					})
				})

				this._links = links
			}

			return this._links
		}
	})

	var TaskHive = Backbone.Model.extend({
		'defaults': {
			'id': undefined
			, 'type': 'TaskHive'
			, 'label': '(no label set yet)'
			, 'description': '(no description set yet)'
			, 'tasks': undefined
		}
		, 'initialize': function(){
			if (!this.attributes.id) {
				this.id = this.attributes.id = this.attributes.type + '.' + Date.now() + Math.random()
			}
			if (!this.attributes.tasks) {
				this.attributes.tasks = []
			}
			if (!this.attributes.tags) {
				this.attributes.tags = {}
			}

			this.on('change', function(model, options){
				this.save(null, {'changed': _.clone( options.changes )})
			})
		}
		, 'gettasks': function (){
			if (!this._tasks) {
				var taskhive = this

				this._tasks = new GenericTaskCollection(
					taskhive.attributes.tasks.map(function(taskid){
						return alltasks.get(taskid)
					})
				)
				.on('add', function(model, collection, options){
					alltasks.add(model)
					var tasks = _.clone( taskhive.attributes.tasks )
					tasks.push( model.id )
					taskhive.set('tasks', tasks)
					//taskhive.save()
				})
				.on('remove', function(model, collection, options){
					var index
					// async disaster, here we come...
					if ((index = taskhive.attributes.tasks.indexOf(model.id)) !== -1) {
						var newtasks = _.clone(taskhive.attributes.tasks)
						newtasks.splice(index, 1)
						taskhive.set(
							'tasks'
							, newtasks
						)
					}
					//taskhive.save()
				})
				// this.on('change:tasks', function(){taskhive._tasks = undefined}
				// .on('all', function(){
				// 	console.log('_tasks all', arguments)
				// })
				// change events are not cought here
				// because 'add' generates a 'change' and confuses things.
				// not sure what to do about 'change'
				// Don't need 'reset' event handler.
			}
			return this._tasks
		}
		, 'sync': function (method, model, options){
			console.log('TaskHive.sync', method, model, options)
			if (method === 'update') {
				if (options.changed && Object.keys(options.changed).length) {
					var changed = Object.keys(options.changed).map(function(name){
						var base = {}
						base[name] = model.attributes[name]
						return base
					})
					events.publish(
						NOTIFYSERVER
						, 'Storage.Change'
						, model.id
						, changed
					)
				} else {
					events.publish(
						NOTIFYSERVER
						, 'Storage.Set'
						, model.id
						, model.toJSON()
					)
				}

			} else if (method === 'delete') {
				events.publish(
					NOTIFYSERVER
					, 'Storage.Set'
					, model.id
					, null // null deletes the entry from storage.
				)
			} else {
				console.log("In sync hanlder for TaskHive model. Unrecognized method '"+method+"' received. Ignoring.")
			}
			options.success(model)
		}
	})

	var TaskHives = Backbone.Collection.extend({
		'model':TaskHive
		, 'sync': function (method, model, options){
			if (method === 'read') {
				events.publish(
					CALLSERVER
					, 'Storage.Query'
					, '^TaskHive\\.' // need python regex '^TaskHive\.', but JS needs escaping to get there.
					, options.success
				)
			} else {
				console.log("In sync hanlder for TaskHives collection. Unrecognized method '"+method+"' received. Ignoring.")
				options.error("We don't accept methods other than 'read'")
			}
		}
	})
	var taskhives = window.my['th'] = new TaskHives()
	taskhives.fetch()

	// this app has a "global" 'selected' group
	// it's the one shown on the right side of screen.
	// scrolling to other hives does NOT change the selected
	// display. Doing selections / dropping to other tasks does.
	// Keeping one "global" view of some selection set
	// will allow us to implement "move to other hive" 
	// functionality in the future.
	var globallyselectedtasks = new GenericTaskCollection()
	var LocallySelectedTasks = Backbone.Collection.extend({
		'model': Task
		, 'initialize':function(){
			this.on('add reset remove', function(){
				//console.log('local select changed', this.models)
				globallyselectedtasks.reset(this.models)
			}, this)
		}
	})

	return {
		'TaskTypes': tasktypes
		, 'TaskHives': taskhives
		, 'GloballySelectedTasks': globallyselectedtasks
		, 'LocallySelectedTasksClass': LocallySelectedTasks
		, 'GenericTaskCollectionClass': GenericTaskCollection
	}

}

// yes. It's a singleton.
var data

function getit(events){
	if (!data) {
		data = EnvInit(events)
	}
	return data
}

define(['app/pubsublive', 'js!libs/backbone.modelbinder.js'],getit)

}).call( this )
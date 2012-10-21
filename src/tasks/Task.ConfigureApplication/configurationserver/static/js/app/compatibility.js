;(function() {
'use strict'

function EnvInit(events, cache){

	function get_args_catalog(args){
		var catalog = {} // "ArgType'+'arg name' : arg line from args
	    args.forEach(function(argdef){
	    	// argdef = [(default-)value, type, name, description, templates, etc]
	    	if (argdef[1] !== 'Callback') {
	    		catalog[argdef[1]+'_'+argdef[2]] = argdef
	    	}
	    })
	    return catalog
	}

	function This(){}

	This.prototype.areJoinable = function(parent_type_id, child_type_id){
		var parent = cache['TaskTypesMetadata'][parent_type_id]
		, child = cache['TaskTypesMetadata'][child_type_id]
		, parent_outputs
		, child_inputs

		console.log('areJoinable', cache, parent, child)

		if (parent && child) {
			// tasks can connect if:
			// a) child has no other args except Callback, or 
			// b) child OR parent have Args type arg, or
			// c) none of childs args are on parent, but child has non-null default value for at least one of these, or
			// d) child has at least one arg in common with the parent

			// ^ these may change with introduction of optional ( ex: "[Typename]") arg types.

			if (child.inputs.length < 2) {
				// if it's only the callback. Case (a) above
				return true
			}

			parent_outputs = get_args_catalog(parent.outputs)
			child_inputs = get_args_catalog(child.inputs)

			// Case (b) above
			if ('Args_args' in parent_outputs || 'Args_args' in child_inputs) {
				// Args type (name 'args') is special. It compresses all incoming 
				// arguments into object and unpacks it into callback.
				// meaning, this task can connect to anything.
				return true
			}

			for(var key in child_inputs){
				// case (c) above
				if(child_inputs[key][0]){
					return true
				}
				// case (d) above
				if (key in parent_outputs) {
					return true
				}
			}
		}
		return false
	}

	return This
}

// trying to keep it a singleton
var compatibility

function get_compatibility(events, cache){
	if (!compatibility) {
		compatibility = new (EnvInit(events, cache))()
	}
	return compatibility
}

define([
  'app/pubsublive'
  , 'app/datalive'
], get_compatibility)

}).call( this )
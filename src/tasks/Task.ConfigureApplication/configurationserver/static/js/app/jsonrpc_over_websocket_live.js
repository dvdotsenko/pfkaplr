;(function() {

function EnvInit(events, WSClient){
	'use strict'

	// pubsub channels we will be listening on:
	var CALL = 'WSBridge.Call'
	, NOTIFY = 'WSBridge.Notify'
	, SUBSCRIBE = 'WSBridge.Subscribe'

	function JSONRPC_over_WebSocket(uri) {

		this.connection = new WSClient(
			uri
			, this._process_message_from_server.bind(this) // onmessage
		)
		this.callbacks = {}

		events.subscribe(
			CALL
			, this.Call.bind(this)
		)
		events.subscribe(
			NOTIFY
			, this.Notify.bind(this)
		)
		events.subscribe(
			SUBSCRIBE
			, this.Subscribe.bind(this)
		)
	}

	JSONRPC_over_WebSocket.prototype._process_message_from_server = function(jsonrpcstring){
		var o, undefined
		try{
			o = JSON.parse(jsonrpcstring)
		} catch (ex) {
			console.log("Cannot parse this response from server: ", jsonrpcstring)
			return
		}

		// JSON-RPC response
		if (o.id && o.result) {
			// sever promissed it to be an array always.
			this.callbacks[o.id].apply(undefined, o.result)
		}
		// there are other possibilities, like JSON-RPC call or notify from server,
		// but we will not care about those for now.
	}

	JSONRPC_over_WebSocket.prototype._register_callback = function(callback){
		var id = Date.now() + '' + Math.random() + '' + Math.random()
		this.callbacks[id] = callback
		return id
	}

	JSONRPC_over_WebSocket.prototype._package = function(args){
		return {
    		'jsonrpc': '2.0'
    		, 'method': args[0]
    		, 'params': args.slice(1)
    	}
	}

	JSONRPC_over_WebSocket.prototype._wrap = function(message){

		var w = {
    		'jsonrpc': '2.0'
    		, 'method': 'rpc'
    		, 'params': message
    	}

    	if (message.id) {
    		w.id = message.id
    	}

		return w
	}
    
    JSONRPC_over_WebSocket.prototype.Call = function(methodname /*, arg1, arg2, ... */, callback){
    	var message = this._package(Array.prototype.slice.call(arguments, 0, arguments.length - 1))
    	
    	message['id'] = this._register_callback(arguments[ arguments.length - 1 ])

    	this.connection.send(this._wrap(message))
    }

    JSONRPC_over_WebSocket.prototype.Notify = function(methodname /*, arg1, arg2 , ...*/){
		this.connection.send(this._wrap(this._package(Array.prototype.slice.call(arguments, 0))))
    }

    JSONRPC_over_WebSocket.prototype.Subscribe = function(methodname /*, arg1, arg2, ... */, callback){
    	throw Error("Subscribe method on JSON-over-WebSocket interface is not implemented yet.")
    	// var message = this._package(Array.prototype.slice.call(arguments, 0, arguments.length - 1))
    	
    	// message['id'] = this._register_callback(arguments[ arguments.length - 1 ])

    	// this.connection.send(this._wrap(message))
    }

    return JSONRPC_over_WebSocket
}

// yes, we are trying to keep one global instance up for the entire page
var talker
var uri = 'ws://'+window.location.host+'/web_service/'

function getsingleton(events, WSClient){
	if (!talker) {
		talker = new (EnvInit(events, WSClient))(uri)
	}
	return talker
}

define(['app/pubsublive', 'libs/websocket'], getsingleton)

}).call( this )

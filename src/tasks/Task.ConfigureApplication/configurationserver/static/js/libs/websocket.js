;(function() {
'use strict'

/*
A class that hides the mechanics of WebSocket connection and reconnection
and handling of disconnected etc etc... 

This class allows you specify `onmessage`, `onerror` handlers for the actual message
(as in 'what's passed to handler is not event, but actually event.data')

The messages given to "send" are queued and connection is reestablished when there
are messages to send.

A callback is called (without args) every time message is successfully sent.
This way you can do "optimistic" .send() - assume it's good, until you get confirmation
that it was.
*/

function WSConnection(uri, onmessage, onerror) {
	var undefined

	this.uri = uri
	this.process = this.process_message_queue.bind( this )
	
	this.onopen = (function(o){return function(){ 
		o.connection_attempts = [Date.now()]
		o.process()
	}})(this)

	this.onmessage = onmessage ? function(e){onmessage(e.data)} : function(e){console.log("Message reported", e.data)}
	this.onerror = onerror ? function(e){onerror(e.data)} : function(e){console.log("Error reported")}
	this.onclose = this.reconnect.bind( this )

	this.connection = undefined
	this.message_queue = []

	this.connection_attempts = []
}

WSConnection.prototype.reconnect = function(){
	console.log("WSConnection class: reconnect()")

	if (!this.message_queue.length) {
		console.log("why are we here? no messages to send")
		return
	}

	// if last connection attempt was less than a sec ago.
	if (this.connection_attempts.length > 10 || 
		this.connection_attempts[0] > (Date.now() - 1000) ) {
		console.log(
			"WebSocket reconnection appears chronically impossible. Giving up with these messages unsent: "
			, this.message_queue
		)
		// TODO: route this error to onerror handler.
		return
	}
	this.connection_attempts.unshift( Date.now() )

	var c = this.connection = new WebSocket(this.uri)
	c.onopen = this.onopen
	c.onclose = this.onclose
	c.onmessage = this.onmessage
	c.onerror = this.onerror
}

WSConnection.prototype.send = function(message, callback){
	if (!callback) {
		callback = function () {}
	}
	this.message_queue.push([message, callback])
	setTimeout(
		this.process
		, 0
	)
}

WSConnection.prototype.process_message_queue = function(){
	console.log("Inside process message queue")
	var message_callback_pair, result
	try {
		while (message_callback_pair = this.message_queue.shift()){
			result = this.connection.send(JSON.stringify( message_callback_pair[0] ))
			console.log('result of connection send ', result)
			if (result === false) {
				throw new Error("For f's sake! will you guys settle on the WebSocket api please?!")
			}
			setTimeout(
				message_callback_pair[1]
				, 0
			)
		}
	}
	catch (ex) {
		// yeah. putting it back on the queue
		console.log('WSConnection send() failed with: ', ex)
		if (message_callback_pair) {
			this.message_queue.unshift(message_callback_pair)
			this.reconnect() // reconnect will retry processing messages onopen.
		}
	}
}

define(function(){
	return WSConnection
})
	
}).call( this )


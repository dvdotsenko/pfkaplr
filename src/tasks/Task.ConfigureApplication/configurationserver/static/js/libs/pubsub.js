(function(window){

var PubSub = function(context){
	'use strict'
	/*  @preserve 
	-----------------------------------------------------------------------------------------------
	JavaScript PubSub library
	2012 (c) ddotsenko@willowsystems.com
	based on Peter Higgins (dante@dojotoolkit.org)
	Loosely based on Dojo publish/subscribe API, limited in scope. Rewritten blindly.
	Original is (c) Dojo Foundation 2004-2010. Released under either AFL or new BSD, see:
	http://dojofoundation.org/license for more information.
	-----------------------------------------------------------------------------------------------
	*/
	this.topics = {}
	this.context = context
	/**
	 * Allows caller to emit an event and pass arguments to event listeners.
	 * @public
	 * @function
	 * @param topic {String} Name of the channel on which to voice this event
	 * @param **arguments Any number of arguments you want to pass to the listeners of this event.
	 */
	this.publish = function(topic, arg1, arg2, etc) {
		'use strict'
		if (this.topics[topic]) {
			var currentTopic = this.topics[topic]
			, args = Array.prototype.slice.call(arguments, 1)
			, toremove = []
			, fn
			, i, l
			, pair

			for (i = 0, l = currentTopic.length; i < l; i++) {
				pair = currentTopic[i] // this is a [function, once_flag] array
				fn = pair[0] 
				if (pair[1] /* 'run once' flag set */){
				  pair[0] = function(){}
				  toremove.push(i)
				}
			   	fn.apply(this.context, args)
			}
			for (i = 0, l = toremove.length; i < l; i++) {
			  currentTopic.splice(toremove[i], 1)
			}
		}
	}
	/**
	 * Allows listener code to subscribe to channel and be called when data is available 
	 * @public
	 * @function
	 * @param topic {String} Name of the channel on which to voice this event
	 * @param callback {Function} Executable (function pointer) that will be ran when event is voiced on this channel.
	 * @param once {Boolean} (optional. False by default) Flag indicating if the function is to be triggered only once.
	 * @returns {Object} A token object that cen be used for unsubscribing.  
	 */
	this.subscribe = function(topic, callback, once) {
		'use strict'
		if (!this.topics[topic]) {
			this.topics[topic] = [[callback, once]];
		} else {
			this.topics[topic].push([callback,once]);
		}
		return {
			"topic": topic,
			"callback": callback
		};
	};
	/**
	 * Allows listener code to unsubscribe from a channel 
	 * @public
	 * @function
	 * @param token {Object} A token object that was returned by `subscribe` method 
	 */
	this.unsubscribe = function(token) {
		if (this.topics[token.topic]) {
			var currentTopic = this.topics[token.topic]
			
			for (var i = 0, l = currentTopic.length; i < l; i++) {
				if (currentTopic[i][0] === token.callback) {
					currentTopic.splice(i, 1)
				}
			}
		}
	}
}

if (typeof define === 'function' && define.amd) {
	define(function(){
		return PubSub
	})	
} else {
	window.PubSub = PubSub
}

})(typeof window !== "undefined"? window : this)


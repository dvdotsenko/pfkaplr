import threading

class PubSub(object):
    '''
    PubSub library
    '''
    def __init__(this):
        this.topics = {}
        this.topics_lock = threading.Lock()

    def publish(this, topic, *args, **kw):
        '''
         * Allows caller to emit an event and pass arguments to event listeners.
         * @public
         * @function
         * @param topic {String} Name of the channel on which to voice this event
         * @param *arguments Any number of positional arguments you want to pass to the listeners of this event.
         * @param **kw Any number of names arguments you want to pass to the listeners of this event.
        '''
        handlers = None
        with this.topics_lock:
            if topic in this.topics:
                # intentionally making a copy of hanlder array.
                # by the time we are ready to iterate some of these may be gone.
                handlers = this.topics[topic][:]

        if handlers:
            for handler in handlers:
                th = threading.Thread(target=handler, args=args, kwargs=kw)
                th.daemon = True
                th.start()

    def subscribe(this, topic, callback):
        '''
         * Allows listener code to subscribe to channel and be called when data is available 
         * @public
         * @function
         * @param topic {String} Name of the channel on which to voice this event
         * @param callback {Function} Executable (function pointer) that will be ran when event is voiced on this channel.
         * @returns {Object} A token object that cen be used for unsubscribing.  
        '''
        with this.topics_lock:
            if topic not in this.topics:
                this.topics[topic] = [callback]
            else:
                this.topics[topic].append(callback)

        return {
            "topic": topic
            , "callback": callback
        }

    def unsubscribe(this, token):
        '''
         * Allows listener code to unsubscribe from a channel 
         * @public
         * @function
         * @param token {Object} A token object that was returned by `subscribe` method 
        '''
        topic = token['topic']
        callback = token['callback']
        with this.topics_lock:
            if topic in this.topics and callback in this.topics[topic]:
                this.topics[topic].remove(callback)

events = PubSub()

publish = events.publish
subscribe = events.subscribe
unsubscribe = events.unsubscribe

;(function() {
'use strict'

function AssembleEnv(events, cache) {

	function App(){}

	App.prototype.start = function(){
		console.log("Starting Configuration Interface")
		
		require([
			'app/hiveviewcontroller'
		]).then(function(HiveViewsController){
			// it's singleton. inits by itself.
		})

		require([
			'app/addpode/main'
		]).then(function(widget){
			widget.init()
		})

		require([
			'app/detailsview'
		]).then(function(widget){
			widget.init()
		})
	}

    ;(function($, window){
      var resizetimer
      , runner = function(){
        events.publish(
			'window.resized'
			, $(window).width()
			, $(window).height()
        )
      }

      $(window).on('resize', function(){
        if (resizetimer) {
            clearTimeout(resizetimer)
        }
        resizetimer = setTimeout( 
          runner
          , 500
        )
      })
    })($, window)

	return App
}

if (typeof define === 'function' && define.amd) {
	define([
		'app/pubsublive'
		, 'app/datalive'
	], function(events, cache){
		return AssembleEnv(events, cache)
	})
}

})()
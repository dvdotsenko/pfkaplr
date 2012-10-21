;(function() {
	require([
		// ------------ initing global singletons and services
		'app/jsonrpc_over_websocket_live'
		// ---------------- non-modules, need these "globally"
		, 'js!libs/jquery-ui.js'
		, 'js!libs/mustache.min.js'
		, 'js!libs/mousetrap.js'
		// -------------------
	]).then(function(){

		$('#content').css('height', $(window).height())

		require(['app/main'])
		.then(function(App){
			app = new App()
			app.start()
		})
	})
})()
;(function() {
'use strict'

function EnvInit(events, globaldata){

	function This(templates, styles){
		this.templates = new TemplateHolder(templates) // see plugins.js
		InjectCSS(styles)
	}

	This.prototype.show = function(){
		// hide button, show list
		this.controls.stop(true)
		this.tiles.stop(true)
		if (!this.controls.hasClass('recessed-left')) {
			this.controls.addClass('recessed-left', 'fast')
			this.tiles.fadeIn('fast')
		}
	}

	This.prototype.hide = function(){
		// hide list, show button
		if (this.controls.hasClass('recessed-left')) {
			this.controls.removeClass('recessed-left', 'fast')
			this.tiles.fadeOut('fast')
		}
	}

	This.prototype.toggle = function(){
		this.tiles.fadeToggle('fast')
		this.controls.toggleClass('recessed-left', 'fast')
	}

	This.prototype.set_size = function(width, height){
		this.tiles.css('max-height', height )
	}

	This.prototype.init = function(){
		$(this.templates.get('#detailsview_wrapper_template') || '')
			.appendTo(document.getElementById('hoverbar'))

		this.controls = $('#detailsview_controls').click(this.toggle.bind(this))

		var $tiles = this.tiles = $(document.getElementById('detailsview_tiles')).css('max-height', $(window).height() )

        events.subscribe(
          'window.resized'
          , this.set_size.bind(this)
        )

		var widget = this

		var Argument_View = Backbone.View.extend({
			'template': Mustache.compile( this.templates.get('#detailsview_argument_template') || '' )
			, 'initialize': function(){
				this._binder = new Backbone.ModelBinder()
				this.render()
			}
			, close: function(){
			    this._binder.unbind();
			}
			, render:function () {
				this.$el.html(this.template(this.model.attributes))
			    this._binder.bind(this.model, this.el)
			    return this
			}
		})

		var FocusedTaskControls_View = Backbone.View.extend({
			'initialize': function(){
				this._binder = new Backbone.ModelBinder()
				this.render()
			}
			, close: function(){
			    this._binder.unbind();
			}
			, render:function () {
			    this._binder.bind(this.model, this.el)
			    return this
			}
		})

		var FocusedTask_View = Backbone.View.extend({
			'template': Mustache.compile( this.templates.get('#detailsview_focused_tile_template') || '' )
			, 'initialize': function(){
				// this.collection.on(
				// 	'reset'
				// 	, this.render.bind(this)
				// )
				this.$el.html(
					this.template({
						'label':  this.model.get('label')
						, 'runonce': ( this.model.checkIfRunonceCompatible() ? true : false )
						, 'tasktype': this.model.get('tasktype')
						, 'taskinstanceid': this.id
					})
				)

				new FocusedTaskControls_View({
					'el': this.$el.find('.detailsview_tile_controls')
					, 'model': this.model
				})

				var arguments_parent = this.$el.find('.detailsview_arguments')
				this.model.getinputs().each( function(argumentmodel){
					new Argument_View({
						'el': $( document.createElement('div') ).appendTo( arguments_parent )
						, 'model': argumentmodel
					})
				})
				arguments_parent.find('textarea').elastic()
			}			
		})

		var SelectedTasks_View = Backbone.View.extend({
			// events: {
			// "click .icon":          "open",
			// "click .button.edit":   "openEditDialog",
			// "click .button.delete": "destroy"
			// }
			'template': Mustache.compile( this.templates.get('#detailsview_tiles_template') || '' )
			, 'initialize': function(){
				this.collection.on(
					'reset remove add'
					, this.render
					, this
				)
				// this.collection.on(
				// 	'all'
				// 	, function(){console.log('detailview all handler', arguments)}
				// )
				this.$el.on('click', '.button.delete', this.handle_button.bind(this, 'delete'))
				this.$el.on('click', '.button.connect', this.handle_button.bind(this, 'connect'))
				this.$el.on('click', '.button.disconnect', this.handle_button.bind(this, 'disconnect'))
			}
			, 'render':function(){
				// the nature of change is irrelevant.
				// we just redraw whole list
				
				// template needs a "key" in an object to understand what to iterate over.
				// why can't I just give it an array?
				if (this.collection.length) {
					if (this._hide_timeout) {
						clearTimeout(this._hide_timeout)
					}
					widget.show()

					var collection = this.collection.toJSON()
					collection.pop() // we render first task separately.
					collection.reverse()

					this.$el.html(
						this.template( {'tasks': collection} )
					)

					// first task in que (last one selected) is "focused"
					// has different drawing logic
					var focused_task = new FocusedTask_View({
						'el': document.getElementById('detailsview_focused_tile')
						, 'model': this.collection.last()
					})
				} else {
					this.$el.html('')
					this._hide_timeout = setTimeout(
						widget.hide.bind(widget)
						, 500
					)
				}
			}
			,'handle_button':function(button, e){
				//console.log("button", arguments)
				if (this.collection.length) {
					if (button === 'delete') {
						this.collection.each(function(model){
							model.destroy()
						})
					} else if (button === 'connect'){
						var parentmodule
						this.collection.each(function(model){
							var consumers
							if (parentmodule) {
								consumers = Array.prototype.slice.call( parentmodule.attributes.consumers || [] )
								if ( consumers.indexOf(model.id) === -1 ) {
									consumers.push(model.id)
									parentmodule.set('consumers', consumers)
								}
							}
							parentmodule = model
						})
					} else if (button === 'disconnect'){
						var parentmodule
						this.collection.each(function(model){
							var consumers
							if (parentmodule) {
								consumers = Array.prototype.slice.call( parentmodule.attributes.consumers || [] )
								var index
								if ( (index = consumers.indexOf(model.id)) !== -1 ) {
									consumers.splice(index, 1)
									parentmodule.set('consumers', consumers)
								}
							}
							parentmodule = model
						})
					}
				}
			}
		})

		var selectedtasks_view = new SelectedTasks_View({
			'el':$tiles
			, 'collection': globaldata.GloballySelectedTasks
		})

		selectedtasks_view.render()

	}

	return This
}

// trying to keep it a singleton
var us

function getit(events, cache, templates, styles){
	if (!us) {
		us = new (EnvInit(events, cache))(templates, styles)
	}
	return us
}

define([
  'app/pubsublive'
  , 'app/datalive'
  , 'text!app/detailsview.html'
  , 'text!app/detailsview.css'
], getit)

}).call( this )
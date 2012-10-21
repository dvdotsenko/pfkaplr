;(function() {
'use strict'

function EnvInit($, events, data){

	function AddPodeWidget(templates, css){

		InjectCSS(css)

		this.templates = new TemplateHolder(templates)
	}

	AddPodeWidget.prototype.init = function(){
		$(this.templates.get('#addpode_wrapper_template') || '').appendTo($('#hoverbar'))

		var tiles = this.tiles = document.getElementById('addpode_tiles')

		var TaskTypes_View = Backbone.View.extend({
			// events: {
			// "click .icon":          "open",
			// "click .button.edit":   "openEditDialog",
			// "click .button.delete": "destroy"
			// }
			'template': Mustache.compile( this.templates.get('#addpode_tile_template') || '' )
			, 'initialize': function(){
				this.collection.on(
					'add remove reset change'
					, this.render.bind(this)
				)

		        events.subscribe(
		          'window.resized'
		          , this.window_resized_handler.bind(this)
		        )
			}
			, 'window_resized_handler': function(width, height){
				this.$el.css('max-height', height)
			}
			, 'render':function(){
				// the nature of change is irrelevant.
				// we just redraw whole list
				
				// template needs a "key" in an object to understand what to iterate over.
				// why can't I just give it an array?
				if (this.collection.length) {
					this.$el.html( 
						this.template( {'tasktypes': this.collection.toJSON() } )
					)
					this.$el.find('.addpode_tile').draggable({
						cursor: "move"
						//cursorAt: { top: -12, left: -20 },
						// , helper: 'clone'
						, helper: function( e ) {
							var replacement = $(e.currentTarget).children('.addpode_logo_wrap').clone()
							replacement[0].dataset.tasktypeid = e.currentTarget.dataset.tasktypeid
							return replacement
						}
						, opacity: 0.5
						, scroll: false
						, zIndex: 2700
						, scope: 'tasktype'
					})
				}
			}
		})

		var tasktypes_view = new TaskTypes_View({
			'el':tiles
			, 'collection': data.TaskTypes
		})

		tasktypes_view.window_resized_handler(null, $(window).height())
		tasktypes_view.render()

		$('#addpode_controls').click(function(e){
			$(tiles).fadeToggle(150)
			$(e.target).toggleClass('recessed-right','fast')
		})
	}

	return AddPodeWidget
}


var us

function getit(events, data, templates, styles){
	if (!us) {
		us = new (EnvInit($, events, data))(templates, styles)
	}
	return us
}

define([
	'app/pubsublive'
	, 'app/datalive'
	, 'text!app/addpode/template.html'
	, 'text!app/addpode/template.css'
], getit)


})()
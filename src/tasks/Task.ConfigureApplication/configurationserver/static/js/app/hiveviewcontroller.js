;(function() {

function EnvInit($, events, globaldata, HiveView){
  'use strict'

  // manage svgs
  function HiveViewsController(parent_element, templates){
    this.views = {}
    this.parent_element = $(parent_element)
    // this.w = this.parent_element.width()
    // this.h = this.parent_element.height()

    this.init(new TemplateHolder(templates))
  }

  HiveViewsController.prototype.init = function(templates){
    // InjectCSS('.taskhive_viewer {height:'+this.parent_element.height()+';width:'+this.parent_element.width()+';}')

    var TaskHives_View = Backbone.View.extend({
      'views': {} // refs to subviews
      , 'template_wrap': Mustache.compile( templates.get('#hiveview_wrapper_template') )
      , 'template_hive': Mustache.compile( templates.get('#hiveview_hive_template') )
      , 'template_addcontrols': Mustache.compile( templates.get('#hiveview_newhivecontrols_template') )
      , 'initialize': function(){
        // this is Backbone's "on"
        this.collection.on('reset', this.render, this)
          .on('add', this.add, this)
          .on('remove', this.remove, this)

        events.subscribe(
          'window.resized'
          , this.window_resized_handler.bind(this)
        )
        // .on(
        //   'all'
        //   , function(){console.log('HiveView all', this, arguments)}
        //   , this
        // )
      }
      , 'window_resized_handler': function(width, height){
        this.$el.height(height)
        this.render()
      }
      , 'render':function(){

        var view = this

        // one wrapper for all hive views
        this.$el.html(this.template_wrap())

        ///////////////
        // Add Hive section on top

        var buttons = this.$el.find('#taskhive_new')
          .html(this.template_hive({'label':'adding new'}))
          .find('.taskhive_canvas')
            .css('line-height','100%')
            .html(
              this.template_addcontrols()
            )
            .find('button')

        buttons.filter('.add')
          .button({'icons':{'primary':'ui-icon-plus'}})
          .on('click', function(){view.collection.create();return false;})

        // buttons.filter('.import')
        //   .button({
        //     'icons':{'primary':'ui-icon-script'}
        //     , 'disabled': true
        //   })
        //   //.on('click', function(){view.collection.create();return false;})

        ///////////////
        // Task Hive list

        if (this.collection.length) {
          this.collection.each(
            (function(taskhives, parent){ return function(model){
              taskhives.views[model.id] = new HiveView(
                $(taskhives.template_hive(model.attributes)).appendTo( parent )
                , model
              )
            }})(this, this.$el.find('#taskhives'))
          )          
          this.views[this.collection.first().id].show()
        }

        /////////////
        // This adjusts the scroll position to nearest hive view.
        // * after the scroll events stop firing for 300ms
        var timers = {}
        , scrollAdjust = (function(controller){return function(){
          var hiveviewelems = controller.$el.children('#taskhives').children()
          var viewheight = hiveviewelems.first().height()
          var position = controller.$el.scrollTop()
          var index = Math.round( position / viewheight )
          if (index === 0) {
            var parent = controller.$el
            parent.animate(
              { 'scrollTop': 0 }
              , { 'duration': 'fast', easing: 'swing'}
            )
          } else {
            controller.views[ hiveviewelems[index - 1].id ].show()
          }
        }})(this)

        this.$el.on('scroll', function(){
          clearTimeout(timers.scroll)
          timers.scroll = setTimeout(scrollAdjust,700)
        })

      }
      , 'add':function(model, collection, options){

        var hive_view = this.views[model.id] = new HiveView(
          $(this.template_hive(model.attributes)).appendTo(this.$el.find('#taskhives'))
          , model
        )
        hive_view.show() // scrolls to it

      }
      , 'remove':function(model, collection, options){

        this.views[model.id].remove()

      }
    })

    var taskhives_view = new TaskHives_View({
      'el':this.parent_element
      , 'collection': globaldata.TaskHives
    })

    //taskhives_view.render()
  }

  return HiveViewsController

} // EnvInit

// trying to keep it a singleton
var us

function getit(events, data, templates, HiveViewClass){
  if (!us) {
    us = new (EnvInit($, events, data, HiveViewClass))('#content', templates)
  }
  return us
}

define([
  'app/pubsublive'
  , 'app/datalive'
  , 'text!app/hiveviewcontroller.html'
  , 'app/hiveview'
], getit)

}).call( this )
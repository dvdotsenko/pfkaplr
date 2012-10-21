;(function() {

function EnvInit($, d3, events, globaldata, SVGSTYLE){
  'use strict'

  var NODE_RADIUS = 25
  , CIRCUMSCRIBED_SQUARE_SIDE = NODE_RADIUS * 1.4

  // single svg
  function HiveView(parent_element, model){
    this.id = model.get('id')
    this.model = model
    
    this.selected = new globaldata.LocallySelectedTasksClass()

    this.w = parent_element.width()
    this.h = parent_element.height()
    this.parent_element = parent_element
    
    this.init()
  }

  HiveView.prototype.init = function(){

    // doing this by hand with with d3 because inserting 
    // preformatted into "innerHTML" fails to make the
    // SVG render properly.
    var widget = this

    var tab = this.parent_element.find('.bottomtab_parent')

    tab.on('change', '[name=label]', function(e){
      console.log('changed label', this, arguments)
      var text = $(e.target).text()
      if (!text){
        e.target.innerHTML = '(set lebel)'
      } else {
        widget.model.set('label', text)
      }
    })

    var task_controls = tab.find('.button')

    task_controls.filter('.delete')
    .button({'icons': { 'primary': "ui-icon-trash" }, 'text':false}).show()
    .on('click', function(e){
      console.log('.delete handler', this, e)
      widget.model.destroy()
    })

    var stage = this.stage = d3.select(this.parent_element.find('.taskhive_canvas')[0])
      .append("svg:svg")
        .attr("width", this.w)
        .attr("height", this.h)
        .on('click', 
          (function(widget){return function(){
            if (widget.selected.length) {
              widget.selected.reset()
              widget.force.resume()
            }
          }})(widget)
        )

    stage.append('svg:style').text(SVGSTYLE)

    var center = stage.append('svg:g')
      .attr('transform','translate('+ this.w/2 + ',' + this.h/2 +')')

    var i, l, base = 221, shades = 30
    var Phi = ( Math.PI * ((Math.sqrt(5)) - 1))
    for (i = 1, l = 120; i < l; i += 1) {
      var distance = Math.sqrt(i) * 10 + i
      , angle = Phi * i
      , color = Math.round(shades * i / l) + base
      center.append('svg:circle')
        .attr('style', 'fill:rgb('+[color,color,color]+');')
        .attr('class', 'decor')
        .attr('r', 5 + 12 * i / l)
        .attr('cx', distance * Math.cos(angle))
        .attr('cy', distance * Math.sin(angle))
    }

    stage.append('svg:g')
      .attr('class', 'links')
      .append('svg:g')
        .attr('class', 'links_end')

    stage.append('svg:g')
      .attr('class', 'nodes')
      .append('svg:g')
        .attr('class', 'nodes_end')

    // var echo = function(){console.log('TH model handler for : ', arguments)}

    // this.model.on('all', echo.bind(this, 'all'))
    // this.model.on('change', echo.bind(this, 'change'))
    // this.model.on('add', echo.bind(this, 'add'))
    // this.model.on('remove', echo.bind(this, 'remove'))
    // this.model.on('reset', echo.bind(this, 'reset'))

    // this.model.on('all',function(){console.log('TaskHive\'s own all handler', arguments)})

    this.model.gettasks()
    .on(
      'add'
      , this.add_node
      , this
    )
    .on(
      'remove'
      , this.remove_node
      , this
    )
    .on(
      'change'
      , function(){
        this.force.start()
      }
      , this
    )
    // .on(
    //   'all'
    //   , function(){console.log('all handler for tasks on hive: ', this, arguments)}
    //   , this
    // )

    this.init_force()
    this.init_interaction_handlers()
  }

  HiveView.prototype.remove = function(){
    //console.log('remove', this, this.parent_element)
    this.parent_element.fadeOut(
      'slow'
      , (function(el){return function(){el.remove()}})(this.parent_element) 
    )
  }

  HiveView.prototype.show = function(){
    var parent = $('#content')
    parent.animate(
      { 'scrollTop': parent.scrollTop() + this.parent_element.offset().top - parent.offset().top }
      , { 'duration': 'fast', easing: 'swing'}
    )
  }

  HiveView.prototype.new_node_dropped_handler = function(tasktypeid, x, y) {
    var model = globaldata.TaskTypes.get(tasktypeid).clone()
    // backbone's Model.clone relies on Underscore's _.clone
    // which is 'shallow'. Need to use big guns here for deep cleaning
    // 'true' makes it yummy
    model.attributes = $.extend(true, {}, model.attributes)
    model.id = model.attributes.id = 'Task.' + tasktypeid + '_' + Date.now() + Math.random()
    model.x = x
    model.y = y
    model.save()

    this.model.gettasks().add(model)
  }

  HiveView.prototype.add_node = function(model) {

    // we allow linking dropped nodes to selected nodes.
    if (this.selected.models.length) {
      model.parents = this.selected.pluck('id')
      this.selected.each(function(parent){
        // Backbone does not count same Array with new contents 
        // as "change" We need to change ref for it to trigger "change" events.
        var consumers = Array.prototype.slice.call( parent.attributes.consumers || [] )
        consumers.push(model.id)
        parent.set('consumers', consumers)
      })
      // dropped node removes all other selecitons and only selects itself.
      this.selected.reset([model])
    } else {
      this.selected.add(model)
    }
    this.force.start()
  }

  HiveView.prototype.remove_node = function(model) {
    var widget = this

    // disconnecting from parents.
    if (model.parents && model.parents.length) {
      setTimeout(function(){
        var tasks = widget.model.gettasks()
        model.parents.forEach(function(id){
          var parent = tasks.get(id)
          // Backbone does not count same Array with new contents 
          // as "change" We need to change ref for it to trigger "change" events.
          var consumers = Array.prototype.slice.call( parent.attributes.consumers || [] )
          var index
          if ( (index = consumers.indexOf(model.id)) !== -1 ) {
            consumers.splice(model.id,1)
            parent.set('consumers', consumers)
          }
        })
        widget.force.start()
      }, 50)
    }

    // disconnecting children
    if (model.attributes.consumers && model.attributes.consumers.length) {
      model.set('consumers',[])
    }

  }

  HiveView.prototype.init_force = function(){

    // var center_focus = {'x':Math.round(w / 2), 'y':Math.round(h / 5) * 3}
    // , starts = Math.round(h / 6)
    // , ends = Math.round(h / 6) * 5
    // , lower = Math.round(w / 3)
    // , upper = Math.round(w / 3) * 2

    var force = this.force = d3.layout.force()
      .nodes(this.model.gettasks().models)
      .links(this.model.gettasks().getlinks())
      .size([this.w, this.h])
      .linkDistance(NODE_RADIUS * 2)
      .charge(function(model, i){
        return model.parents && model.parents.length ? NODE_RADIUS * -30 : NODE_RADIUS * -50
      })
      .linkStrength(1)
      // .friction(0.8)
      .gravity(function(model, i){
        if (model.parents && model.parents.length && 
          !(model.attributes.consumers && model.attributes.consumers.length)
        ) {
          return 0.1
        } else if (!(model.parents && model.parents.length)) {
          return 0.5
        } else {
          return 0.2
        }
      })
      // .gravityOrigin(function(node, i){
      //   if (node.parents.length && !node.children.length) {
      //     if (node.x <= lower) {
      //       return {'y':starts, 'x':lower}
      //     } else if (node.x >= upper ) {
      //       return {'y':starts, 'x':upper}
      //     } else {
      //       return {'y':starts}
      //     }
      //   } else if (!node.parents.length) {
      //     if (node.x <= lower) {
      //       return {'y':ends, 'x':lower}
      //     } else if (node.x >= upper ) {
      //       return {'y':ends, 'x':upper}
      //     } else {
      //       return {'y':ends}
      //     }
      //   } else {
      //     return center_focus
      //   }
      // })

    force.on("tick", this.tick_handler.bind(this))

    force.start()
  }

  function orient_link_components(data, i){
    // this === element, in this case SVG:g
    var group = d3.select(this)

    group.select('line')
      .attr("x1", data.source.x || 0)
      .attr("y1", data.source.y || 0)
      .attr("x2", data.target.x || 0)
      .attr("y2", data.target.y || 0)

    var half_pi = Math.PI / 2 // 90 degrees
    , vx = data.target.x - data.source.x
    , vy = data.target.y - data.source.y
    , angle = vx === 0 ? 
      90 : // Division by 0 = infinity ==> atan = 90 degrees in PI
      Math.atan(Math.abs(vy / vx)) * 180 / Math.PI // we figure quadrants manually, cause atan is not exactly helping there.

    if (vx < 0) {
      angle = 180 - angle
    }
    // SVG's scale transform takes negative degrees,
    // but it rotates CLOCK-WISE - the opposite of ... what you would expect
    // Our "arrow" SVG points at zero degrees position
    // If link is pointing positive 45 degrees, we actually
    // need to scale transform NEGATIVE 45 degrees
    // so, you would expect the following logic:
    // "if y is MORE than zero make angle negative"
    // BUT, SVG y coordinates are opposite of catesian: down = increase, up = decrease
    // so, in the end, logic comes out to be exactly what you would
    // expcect for catesian:
    if (vy < 0) {
      angle = angle * -1
    }


    var radius_ratio = NODE_RADIUS === 20 ? 1 : NODE_RADIUS / 20 // 20 is the actual radius of the arrow's cirlce
    group.select('path')
      .attr(
        'transform'
        ,'translate('+ [data.source.x, data.source.y] +')' +
         ' rotate('+ angle +')' +
         ' scale('+ [radius_ratio, radius_ratio] +')'
      )
  }

  HiveView.prototype.orient_node_components = function(elem, model, i){
    // this = g.node elem
    var node_elem = d3.select(elem)
      .attr("transform", "translate(" + model.x + "," + model.y + ")")

    if (!(model.parents && model.parents.length)) {
      // start of chain
      node_elem.classed('start', true).classed('end', false)
    } else if (!(model.attributes.consumers && model.attributes.consumers.length)) {
      // present parent and no children = end of chain
      node_elem.classed('start', false).classed('end', true)
    } else {
      node_elem.classed('start', false).classed('end', false)
    }

    if (model.attributes.paused) {
      node_elem.classed('paused', true)
    } else {
      node_elem.classed('paused', false)
    }

    var marker = node_elem.select('.marker')
    , marker_present = !marker.empty()
    , inselected = this.selected.get(model) ? true : false

    if (inselected && !marker_present) {
      node_elem.insert('circle', '.position_marker')
        .attr('cx',0)
        .attr('cy',0)
        .attr('r', NODE_RADIUS * 1.25)
        .attr('class', 'marker')
    } else if (!inselected && marker_present){
      marker.remove()
    }

    node_elem.select('text')
      .text(model.get('label') || '(no label)')

  }

  HiveView.prototype.tick_handler = function(){

    var vis = this.stage
    , widget = this
    , links_elem = vis.select('.links')
    , nodes_elem = vis.select('.nodes')

    // let's fill in the missing elems first.
    var links = links_elem.selectAll(".link").data(this.force.links())
    links.exit().remove()
    links.each(orient_link_components)
    links.enter().append("svg:g")
      .attr("class", "link")
      .each(function(data, i){
        var link = d3.select(this)
        link.append("svg:line")
          .attr("class", "tentacle")
        link.append('svg:path')
          .attr('class','arrow')
          .attr('d','M 55,0 C 45,0 17.86616,10.28582 14.39686,13.88282 10.7593,17.65422 5.6536,20.00002 0,20.00002 -11.045695,20.00002 -20,11.04572 -20,0 -20,-11.0457 -11.045695,-20 0,-20 5.89462,-20 11.19363,-17.4499 14.854,-13.3927 18.05266,-9.8473 45,0 55,0 z')
          .attr('class','tentacle')
        orient_link_components.call(this, data, i)
      })
    
    var nodes = nodes_elem.selectAll(".node").data(this.force.nodes())
    nodes.exit().remove()
    nodes.each(function(model, i){
      widget.orient_node_components(this, model, i)
    })
    nodes.enter().append("svg:g")
      .attr("class", "node")
      .attr('data-id', function(d,i){return d.id})
      .attr('data-index', function(d,i){return i})
      // .attr('transform','translate('+ [w/2,h/2] +')')
      .each(function(model, i){
        // this = .node
        var node = d3.select(this)

        node.append("svg:circle")
          .attr("cx", 0)
          .attr("cy", 0)
          .attr("r", NODE_RADIUS)
          .attr('class', 'position_marker')

        node.append("svg:image")
          .attr("xlink:href", "img/ball_back.svg")
          .attr("x", -NODE_RADIUS)
          .attr("y", -NODE_RADIUS)
          .attr("width", NODE_RADIUS * 2)
          .attr("height", NODE_RADIUS * 2)

        node.append("svg:image")
          .attr("xlink:href", 'img/logos/' + model.get('tasktype') + '.svg')
          //.attr("xlink:href", "img/logo.svg")
          .attr("x", CIRCUMSCRIBED_SQUARE_SIDE / -2)
          .attr("y", CIRCUMSCRIBED_SQUARE_SIDE / -2)
          .attr("width", CIRCUMSCRIBED_SQUARE_SIDE)
          .attr("height", CIRCUMSCRIBED_SQUARE_SIDE)

        node.append("svg:image")
          .attr("xlink:href", "img/ball_front.svg")
          .attr("x", -NODE_RADIUS)
          .attr("y", -NODE_RADIUS)
          .attr("width", NODE_RADIUS * 2)
          .attr("height", NODE_RADIUS * 2)

        node.append('svg:text')
          .attr("dx", NODE_RADIUS * 1.2)
          .attr("dy", ".35em")
          .attr('class', 'nodelabel showonhover')

        widget.orient_node_components(this, model, i)
      })
      .call(this.force.drag)
      .on('click', function(datum){
        widget.toggle_node_selection(datum)
        //console.log('new selected', widget.selected.models, d3.event)
        d3.event.stopPropagation()
      })
  }

  HiveView.prototype.toggle_node_selection = function(taskmodel){
    //console.log('inside toggle_node_selection', this, arguments)
    if (this.selected.get(taskmodel)) {
      this.selected.remove(taskmodel)
    } else {
      this.selected.add(taskmodel)
    }
    // our tick handler applies the right colors.
    // but needs a nudge...
    this.force.resume()
  }

  HiveView.prototype.init_interaction_handlers = function() {
    'use strict'

    // set up droppable zone
    this.parent_element.droppable({
      'drop': (function(widget){ return function(event, ui) { 
        var position = $(event.target).position()
        widget.new_node_dropped_handler(
          ui.helper[0].dataset.tasktypeid
          , ui.offset.left - position.left
          , ui.offset.top - position.top
        )
      } })(this)
      , 'activeClass': "highlight"
      //, 'hoverClass': "drophover"
      , 'scope': 'tasktype'
    })
  }

  return HiveView

} // EnvInit

// trying to keep it a singleton
var us

function getit(events, data, svgstyles){
  if (!us) {
    us = EnvInit($, d3, events, data, svgstyles)
  }
  return us
}

define([
  'app/pubsublive'
  , 'app/datalive'
  , 'text!app/hiveviewsvg.css'
  , 'js!libs/d3.v2.js' // this goes into global
], getit)

}).call( this )
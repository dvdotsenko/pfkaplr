// Avoid `console` errors in browsers that lack a console.
if (!(window.console && console.log)) {
    (function() {
        var noop = function() {};
        var methods = ['assert', 'clear', 'count', 'debug', 'dir', 'dirxml', 'error', 'exception', 'group', 'groupCollapsed', 'groupEnd', 'info', 'log', 'markTimeline', 'profile', 'profileEnd', 'table', 'time', 'timeEnd', 'timeStamp', 'trace', 'warn'];
        var length = methods.length;
        var console = window.console = {};
        while (length--) {
            console[methods[length]] = noop;
        }
    }());
}

// Place any jQuery/helper plugins in here.
function InjectCSS(cssbody) {
    var styletag = document.createElement('style')
    styletag.type = 'text/css'
    if (styletag.styleSheet) {
        styletag.styleSheet.cssText = cssbody
    } else {
        styletag.appendChild(document.createTextNode(cssbody))
    }
    document.getElementsByTagName("head")[0].appendChild(styletag)
}


// Allows one to load a long HTML with lotsa templates / fragments
// into an object and, then, call them out by ID
function TemplateHolder(tempates){

    this.holder = document.createElement('div')
    this.holder.innerHTML = tempates

    this.get = function(selector){
        var fragment = this.holder.querySelectorAll(selector)[0]
        if (fragment) {
            return fragment.innerHTML
        } else {
            return ''
        }
    }
}

// this makes elems with contenteditable = true 
// emit 'change' events when data inside changes.
$(document.body).on('focus', '[contenteditable]', function() {
    this.dataset['prior_value'] = this.innerHTML
}).on('keyup paste blur', '[contenteditable]', (function(timers){
    return function(e) {
        // escape button removes focus.
        if ( (e.which || e.keycode || 0) === 27 ) {
            $(this).blur()
        } else if (this.dataset['prior_value'] !== this.innerHTML) {
            this.dataset['prior_value'] = this.innerHTML
            clearTimeout(timers.timer)
            timers.timer = setTimeout(
                (function(el){return function(){
                    $(el).trigger('change')
                }})(e.target)
                , 600
            )
        }
    }
})({})
)
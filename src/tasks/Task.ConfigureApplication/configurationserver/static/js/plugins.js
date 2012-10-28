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

// jQuery.Elastic - makes textarea autogrow
;(function(jQuery){jQuery.fn.extend({elastic:function(){var mimics=['paddingTop','paddingRight','paddingBottom','paddingLeft','fontSize','lineHeight','fontFamily','width','fontWeight'];return this.each(function(){if(this.type!='textarea'){return false;}
var $textarea=jQuery(this),$twin=jQuery('<div />').css({'position':'absolute','display':'none','word-wrap':'break-word'}),lineHeight=parseInt($textarea.css('line-height'),10)||parseInt($textarea.css('font-size'),'10'),minheight=parseInt($textarea.css('height'),10)||lineHeight*3,maxheight=parseInt($textarea.css('max-height'),10)||Number.MAX_VALUE,goalheight=0,i=0;if(maxheight<0){maxheight=Number.MAX_VALUE;}
$twin.appendTo($textarea.parent());var i=mimics.length;while(i--){$twin.css(mimics[i].toString(),$textarea.css(mimics[i].toString()));}
function setHeightAndOverflow(height,overflow){curratedHeight=Math.floor(parseInt(height,10));if($textarea.height()!=curratedHeight){$textarea.css({'height':curratedHeight+'px','overflow':overflow});}}
function update(){var textareaContent=$textarea.val().replace(/&/g,'&amp;').replace(/  /g,'&nbsp;').replace(/<|>/g,'&gt;').replace(/\n/g,'<br />');var twinContent=$twin.html();if(textareaContent+'&nbsp;'!=twinContent){$twin.html(textareaContent+'&nbsp;');if(Math.abs($twin.height()+lineHeight-$textarea.height())>3){var goalheight=$twin.height()+lineHeight;if(goalheight>=maxheight){setHeightAndOverflow(maxheight,'auto');}else if(goalheight<=minheight){setHeightAndOverflow(minheight,'hidden');}else{setHeightAndOverflow(goalheight,'hidden');}}}}
$textarea.css({'overflow':'hidden'});$textarea.keyup(function(){update();});$textarea.live('input paste',function(e){setTimeout(update,250);});update();});}});})(jQuery);
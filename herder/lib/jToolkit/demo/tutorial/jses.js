/*
JavaScript Event Sheets
This comes from http://www.kryogenix.org/code/browser/jses/
It is a css-like (and also XBL like) approach to adding events to javascript
- Stephen Emslie, St. James Software
*/

jses_addEvent(window,"load",jses_init);

function jses_init() {
  // Find any jses tags and grab their content
  tgs = document.getElementsByTagName('link');
  if (!tgs) return;
  jsesData = '';
  for (var i=0;i<tgs.length;i++) {
    if (tgs[i].getAttribute('rel') != 'jses') continue;
    var async = true;
    uri = tgs[i].getAttribute("href");
    var xmlHttp = XmlHttpGet();
    xmlHttp.responsehandler = jses_parse;
    xmlHttp.get(uri, {});
  }
}

function jses_parse(data) {
  // Split text into rulesets
  re_ruleset = /([a-zA-Z0-9.#\s>]+)({[\s\S]+})/g;
  re_declaration = /\s*([a-z]+)\s*:\s*([a-zA-Z0-9_-]+)\s*;/g
  while ((ruleset = re_ruleset.exec(data)) != null) {
    // Parse a ruleset into a selector and a series of declarations
    selector = ruleset[1];
    declarations = ruleset[2];
    while ((declaration = re_declaration.exec(declarations)) != null) {
      j_property = declaration[1];
      j_value = declaration[2];
      applicableEls = cssQuery(selector);
      for (var i=0;i<applicableEls.length;i++) {
        jses_addEvent(applicableEls[i],j_property,eval(j_value));
      }
    }
  }
}

function jses_getInnerText(el) {
	if (typeof el == "string") return el;
	if (typeof el == "undefined") { return el };
	if (el.innerText) return el.innerText;	//Not needed but it is faster
	var str = "";
	
	var cs = el.childNodes;
	var l = cs.length;
	for (var i = 0; i < l; i++) {
		switch (cs[i].nodeType) {
			case 1: //ELEMENT_NODE
				str += jses_getInnerText(cs[i]);
				break;
			case 3:	//TEXT_NODE
				str += cs[i].nodeValue;
				break;
		}
	}
	return str;
}

/* Add an eventListener to browsers that can do it somehow.
   Originally by the fantabulous Scott Andrew. */
function jses_addEvent(obj, evType, fn){
  // a hack! this seems to make jses work for clicks (otherwise the normal link gets followed...)...
  if (evType == "click" && obj.nodeName == 'A')
  {
    obj.onclick = function() { return false; };
  }
  if (obj.addEventListener){
    obj.addEventListener(evType, fn, false);
    return true;
  } else if (obj.attachEvent){
	var r = obj.attachEvent("on"+evType, fn);
    return r;
  } else {
	return false;
  }
}


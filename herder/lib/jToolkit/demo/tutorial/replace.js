
function replacenode(orignode, newnode)
{
  // we can't use the cloneNode API because Mozilla needs to see HTML
  // elements since Mozilla is namespace-aware, and we can't use cloneNode
  // for MSIE because it's totally unreliable...
  var source = newnode;
  while (source)
  {
    switch (source.nodeType)
    {
      case 1:
        // this is an element node, create a local clone
        var clone = document.createElement(source.nodeName);
        // insert it
        orignode.parentNode.insertBefore(clone, orignode);
        var a = source.attributes;
        for (var i=0; i<a.length; i++)
        {
          // clone all attributes
          var sourceAtt = a[i];
          switch (sourceAtt.nodeName.toLowerCase())
          {
            case "class":
              // MSIE sux, its setAttribute() method sux
              clone.className = sourceAtt.nodeValue;
              break;
            case "insertbefore":
            case "insertafter":
            case "position":
              // do nothing
              break;
            default:
              clone.setAttribute(sourceAtt.nodeName, sourceAtt.nodeValue);
              break;
          }
        }
        // go deeper?
        if (source.firstChild)
          HO_cloneNodeDeep(source.firstChild, clone);
        break;

      case 3:
        // this is a text node, just clone it
        clone = document.createTextNode(source.data);
        orignode.appendChild(clone);
        break;

      default:
        // do nothing
        break;
    }
    // iterate
    source = source.nextSibling;
  }
  orignode.parentNode.removeChild(orignode);
}

function onclickreplace(e) {
    var obj = this;
    var targetid = obj.getAttribute("replacetarget");
    if (targetid)
    {
        var target = getObj(targetid);
        if (target == undefined)
        {
            alert("could not find replacetarget "+targetid);
            return false;
        }
        var xmlHttp = XmlHttpGet();
	xmlHttp.target = target;
        xmlHttp.xmlresponsehandler = function(responseXML)
        {
            replacenode(this.target, responseXML.firstChild);
        }
        xmlHttp.get(obj.href, {});
        if (!e) var e = window.event;
        e.cancelBubble = true;
        if (e.stopPropagation) e.stopPropagation();
        return false;
    }
    return true;
}

/*
 * The contents of this file are subject to the Mozilla Public License
 * Version 1.1 (the "License"); you may not use this file except in
 * compliance with the License. You may obtain a copy of the License at
 * http://www.mozilla.org/MPL/
 *
 * Software distributed under the License is distributed on an "AS IS"
 * basis, WITHOUT WARRANTY OF
 * ANY KIND, either express or implied. See the License for the specific
 * language governing rights and
 * limitations under the License.
 *
 * The Original Code is HTML Overlays.
 *
 * The Initial Developer of the Original Code is Disruptive Innovations SARL.
 * Portions created by the Initial Developer are Copyright (C) 2004.
 * The HO_addLoadEvent function's code is Copyright (C) Simon Willison 2004,
 * used and MPL'd here with written permission.
 * All Rights Reserved.
 *
 * Contributor(s):
 *   Laurent Jouanneau <laurent.jouanneau@disruptive-innovations.com>,
 *                     Original idea
 *   Daniel Glazman <glazman@disruptive-innovations.com>, Original author
 *
**/

/*
 * Change log:
 *   2004-aug-30: original version, sync mode
**/

function HO_ApplyOverlayXML(doc){
  // let's look at all the element children of the root element
  var child = doc.documentElement.firstChild;
  while (child)
  {
    if (child.nodeType == 1 &&
        child.getAttribute("id"))
    {
      // find a local element of same id
      var a = child.attributes;
      var t = getObj(child.getAttribute("id"));
      if (t)
      {
        // we found a target, let's append a clone of all the contents
        HO_cloneNodeDeep(child.firstChild, t);
      }
      // don't forget to copy all attributes
      for (var i=0; i<a.length; i++)
      {
        var sourceAtt = a[i];
        t.setAttribute(sourceAtt.nodeName, sourceAtt.nodeValue);
      }
    }
    child = child.nextSibling;
  }
}

function HO_ApplyOverlay(url)
{
  var p;
  // let's create an XMLHttpRequest
  // unfortunately, this old crap of MSIE does that through an ActiveX
  // a try/catch will help us make the difference between good browsers
  // and Internet Explorer
  try {
    p = new XMLHttpRequest();
  } catch (e) {
    p = new ActiveXObject("Msxml2.XMLHTTP");
  }

  try {
    // needed for Mozilla
    netscape.security.PrivilegeManager.enablePrivilege("UniversalBrowserRead");
  } catch (e) {
    // ignore
  }

  // send the request
  p.open("GET", url, false);
  p.send(null);

  // find the resulting DOM document
  var doc = p.responseXML;

  // do we have a valid XML document?
  if (doc)
  {
    // is it an HTML overlay?
    if (doc.documentElement &&
        doc.documentElement.nodeName == "HTMLoverlay")
    {
      HO_ApplyOverlayXML(doc);
    }
  }
}

function HO_cloneNodeDeep(source, target)
{
  // we can't use the cloneNode API because Mozilla needs to see HTML
  // elements since Mozilla is namespace-aware, and we can't use cloneNode
  // for MSIE because it's totally unreliable...
  while (source)
  {
    switch (source.nodeType)
    {
      case 1:
        // this is an element node, create a local clone
        var clone = document.createElement(source.nodeName);
        // do we have to append or insert somewhere else?
        var refElt = null;
        var insertbefore = source.getAttribute("insertbefore");
        if (insertbefore)
          refElt = getObj(insertbefore);
        if (insertafter && !refElt)
        {
          var insertafter  = source.getAttribute("insertafter");
          if (insertafter)
            refElt = getObj(insertafter);
          if (refElt)
            refElt = refElt.nextSibling;
          else
          {
            var position = source.getAttribute("position");
            if (position)
            {
              // find the position-th child of target if it exists...
              var index = 0;
              refElt = target.firstChild;
              while (refElt)
              {
                if (refElt.nodeType == 1)
                  index++;
                if (index == position)
                  break;
                refElt = refElt.nextSibling;
              }              
            }
          }
        }
        
        // insert it
        target.insertBefore(clone, refElt);
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
        target.appendChild(clone);
        break;

      default:
        // do nothing
        break;
    }
    // iterate
    source = source.nextSibling;
  }
}

function HO_ApplyOverlays()
{
  var d = document;
  var linkCollection = d.getElementsByTagName("link");
  var linkCollectionLength = linkCollection.length;
  for (var i=0; i<linkCollectionLength; i++)
  {
    var theLink = linkCollection[i];
    if (theLink.parentNode &&
        theLink.parentNode.nodeName.toLowerCase() == "head")
    {
      if (theLink.getAttribute("rel").toLowerCase() == "overlay")
        HO_ApplyOverlay(theLink.getAttribute("href"));
    }
  }
}

function HO_addLoadEvent(func) {
  var oldonload = window.onload;
  if (typeof window.onload != 'function') {
    window.onload = func;
  } else {
    window.onload = function() {
      oldonload();
      func();
    }
  }
}


//HO_addLoadEvent(HO_ApplyOverlays);



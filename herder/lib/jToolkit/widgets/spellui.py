# -*- coding: utf-8 -*-
"""
This file contains spellchecking widgets.
SpellCheckable is a text area and spellcheck button
"""

from jToolkit.web import server
from jToolkit.widgets import widgets
from jToolkit import spellcheck

# Copyright 2002, 2003 St James Software
# 
# This file is part of jToolkit.
#
# jToolkit is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# jToolkit is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with jToolkit; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

class SpellingStandby(widgets.PlainContents):
  """
  a simple 'loading...' screen
  """

  def __init__(self):
    html = """
    <body>
    <table width="100%" height="100%" valign="center">
      <tr>
        <td align="center">
        <PRE><b>checking...</b></PRE>
        </td>
      </tr>
    </table>
    </body>
    """
    widgets.PlainContents.__init__(self,html)
    
class SpellingReview(widgets.Page):
  """
  The frameset for the spellchecker
  """
  def __init__(self, session, argdict, js_url = None):
    if js_url is None:
      js_url = "js/spellui.js"
    #first do the actual spellchecking
    spellcheckfield = argdict['spellcheckfield']
    fontStyle = argdict.get('fontStyle', '')
    fontWeight = argdict.get('fontWeight', '')
    text = argdict.get(spellcheckfield, '')
    lang = argdict.get('spellchecklang', None)
    results = spellcheck.check(text, lang=lang)

    def SuggestionsToString(suggestions):
      return "Array(%s)"%','.join(["\"%s\""%suggestion for suggestion in suggestions])

    #create links in the text and javascript to store word replacement and position data
    words = []
    htmltext = text
    for index in range(len(results)):
        word,pos,suggestions = results[index]
        if isinstance(word, str):
          word = word.decode("utf8")

        #append word to the javascript array
        words.append('\nArray(\"%s\",\"%s\",%s,\"%s\")'%(word,pos,SuggestionsToString(suggestions),word))

        #add the link, referencing this element of the array
        newword = "<a href='#' name='spellcheckword' onClick=\"ShowOptions(this,%s);return false\">"%(index) + word + "</a>"
        htmltext = htmltext[:pos] + newword + htmltext[pos + len(word):]
        posmod = len(newword) - len(word)
        for seekindex in range(index+1,len(results)):
            seekword,seekpos,seeksuggestions = results[seekindex]
            results[seekindex] = (seekword,seekpos+posmod,seeksuggestions)
    htmltext = "<pre id=\"contentsparent\" style=\"font-weight: %s; font-style: %s\">" % (fontWeight,fontStyle) + htmltext + "</pre>"
    #finish the javascript
    jswordlistarray = 'Array(%s)'%(','.join(words))

    #this is the short version of the above code, but can be incorrect if the words are out of order:
    #text = text.replace(word,"<a href='#'>" + word + "</a>",1)

    #body of the javascript
    jstext = """
    <script type="text/javascript">
      //set up the array of replacements
      var wordlist = new %s;
      //store the spellcheck field
      var spellcheckfield = \"%s\";
    </script>
    """ % (jswordlistarray,spellcheckfield)
    
    #CSS to handle word wrapping
    css = widgets.PlainContents("""
    <link rel="stylesheet" href="/css/prewrap.css" type="text/css" />
    """)

    #create the javascript
    autorunscript = widgets.PlainContents(jstext)
    javascript = widgets.Script('text/javascript', '', newattribs={'src': js_url})

    #finish the page
    widgets.Page.__init__(self,contents=[htmltext],
                          newattribs={'includeheading':False,'bgcolor':'#D5E6F7'},
                          headerwidgets=[css,autorunscript,javascript])

class SpellCheckable(widgets.PlainContents):
  """
  a text area with spellcheck button
  """

  def __init__(self, newattribs, readonly = 0, contents = "", standby_url=None, target_url=None, js_url=None):
    if standby_url is None:
      standby_url = "spellingstandby.htm"
    if target_url is None:
      target_url = "spellcheck.htm"
    if js_url is None:
      js_url = "js/spellui.js"
    textarea = widgets.TextArea(newattribs, readonly, contents)
    textareaname = textarea.attribs['name']
    include_script = widgets.Script('text/javascript', '', newattribs={'src': js_url})
    if "." in textareaname:
      onclickscript = "ToggleSpellChecker(this.form['%s'], this)" % textareaname
    else:
      onclickscript = "ToggleSpellChecker(this.form.%s, this)" % textareaname
    spellcheckbutton = widgets.Input({'type': "button", 'value': "spellcheck", 'onclick': onclickscript})
    layertext = """
    <DIV id='%s.spellchecklayer' standby_url="%s" target_url="%s" 
           STYLE='visibility: hidden; position: absolute; left: 20px; z-index:1; white-space: pre-wrap'>
        <IFRAME SRC="%s" name="%s.spellcheckframe" id="%s.spellcheckframe" SCROLLING="Yes"
                WIDTH="10" HEIGHT="50" MARGINWIDTH=0 MARGINHEIGHT=0 FRAMEBORDER="No">
        </IFRAME>
    </DIV>
    <DIV id='suggestionslayer' STYLE='visibility: hidden;  position: absolute; left: 20px; z-index:2'></DIV>
    """%(textareaname, standby_url, target_url, standby_url, textareaname, textareaname)
    layer = widgets.PlainContents(layertext)
    widgets.PlainContents.__init__(self, [layer,include_script,textarea,spellcheckbutton])

def SpellCheckServer(baseclass):
 class SpellCheckServer(server.AppServer, baseclass):
  """the Server that serves the spellchecking pages"""
  def getpage(self, pathwords, session, argdict):
    """return a page that will be sent to the user"""
    if 'spellcheck.htm' in pathwords:
      return SpellingReview(session, argdict)
    else:
      return super(SpellCheckServer, self).getpage(pathwords, session, argdict)
 return SpellCheckServer


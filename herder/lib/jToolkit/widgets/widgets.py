# -*- coding: utf-8 -*-
""" This module holds the classes for widgets that can be used to generate HTML 
    They include combo, textfield, textarea, button etc.
    They are all derived from Widget, and their html representation is returned by gethtml
"""

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

import urllib

def jsquote(s):
  """quotes a string or list for javascript..."""
  if isinstance(s, list):
    return "[" + ",".join([jsquote(value) for value in s]) + "]"
  # shouldn't get anything else here but handle them in case...
  if not isinstance(s, (str, unicode)):
    return jsquote(repr(s))
  if "'" in s and '"' in s:
    return "'%s'" % s.replace("\\", "\\\\").replace("'","\\'")
  elif "'" in s:
    return '"%s"' % s.replace("\\", "\\\\")
  else: # including if '"' in s:
    return "'%s'" % s.replace("\\", "\\\\")

class Widget:
  def __init__(self, tagname = "widget"):
    self.attribs = {}
    self.tagname = tagname  # this should never be used

  def overrideattribs(self, newattribs):
    # override the template attribs with the new attribs specified in the instantiation
    for key, value in newattribs.iteritems():
      self.attribs[key.lower()] = value #Add the new attrib

  def gethtml(self):
    attribs = self.gethtmlattribs()
    contents = self.getcontents()
    tagname = self.tagname
    if isinstance(attribs, unicode) or isinstance(contents, unicode):
      tagname = tagname.decode('utf8')
      if isinstance(attribs, str): attribs = attribs.decode('utf8')
      if isinstance(contents, str): contents = contents.decode('utf8')
    return "<%s %s>%s</%s>\r" % (tagname, attribs, contents, tagname)

  def getcontents(self):
    """return what goes between the opening and closing tags"""
    return ""

  def gethtmlattribs(self):
    #return a string representing all the attribs in this class
    return " ".join([self.gethtmlattrib(key, value) for key, value in self.attribs.iteritems()])

  def escape(self, s, quote=None):
    """Replace special characters &, <, >, add and handle quotes if asked"""
    s = s.replace("&", "&amp;") # Must be done first!
    s = s.replace("<", "&lt;").replace(">", "&gt;")
    if quote:
      s = '"' + s.replace('"', "&quot;") + '"'
    if isinstance(s, unicode): s = s.encode('utf8')
    return s

  def quote(self, s, safe='/'):
    return urllib.quote(s, safe)

  def escapeattribvalue(self, key, value):
    """returns the value escaped appropriately for the key..."""
    return self.escape(value, quote=1)

  def gethtmlattrib(self, key, value):
    """turns the key and value into something usable as an html attribute and value..."""
    if value is None:
      return self.escape(str(key))
    elif isinstance(value, basestring):
      quotedvalue = self.escapeattribvalue(key, value)
    elif isinstance(value, dict):
      attribstring = "; ".join(["%s: %s" % (str(subkey), str(subvalue)) for subkey,subvalue in value.iteritems()])
      quotedvalue = self.escapeattribvalue(key, attribstring)
    else:
      quotedvalue = self.escapeattribvalue(key, str(value))
    return self.escape(str(key)) + '=' + quotedvalue

class EmptyWidget(Widget):
  """a widget with no html (useful as a placeholder)"""
  def __init__(self):
    Widget.__init__(self,"")

  def gethtml(self):
    return ""

class ContentWidget(Widget):
  """a widget with some contents..."""
  def __init__(self, tagname, contents, newattribs={}):
    Widget.__init__(self, tagname)
    self.overrideattribs(newattribs)
    if contents is None:
      contents = []
    self.contents = contents

  def getcontents(self):
    return self.getcontentshtml(self.contents)

  def getcontentshtml(self, contents):
    """returns the html for the given contents"""
    if isinstance(contents, basestring):
      return contents
    elif isinstance(contents, (tuple, list)) or hasattr(contents, "next"):
      contentslist = [self.getcontentshtml(contentspart) for contentspart in contents]
      # TODO: investigate ways to neaten this up while still preventing ASCII decoding error...
      typelist = [type(p) for p in contentslist]
      if unicode in typelist and str in typelist:
        for n in range(len(contentslist)):
          if isinstance(contentslist[n], str):
            contentslist[n] = contentslist[n].decode('utf8')
      return "".join(contentslist)
    elif hasattr(contents, "gethtml"):
      return contents.gethtml()
    elif isinstance(contents,int):
      return str(contents)
    else:
      raise ValueError, "unknown type in ContentWidget.getcontents: %r, %r" % (contents, type(contents))

  def addcontents(self, morecontents):
    """adds more to the existing contents"""
    if not isinstance(self.contents, list):
      self.contents = [self.contents, morecontents]
    else:
      self.contents.append(morecontents)

  def addcontentsbefore(self, morecontents):
    """inserts more before the existing contents"""
    if not isinstance(self.contents, list):
      self.contents = [morecontents, self.contents]
    else:
      self.contents.insert(0, morecontents)

class PlainContents(ContentWidget):
  """this is a Widget just containing straight contents, no tag"""
  def __init__(self, contents):
    ContentWidget.__init__(self, "", contents)

  def gethtml(self):
    return self.getcontents()

class SendFile(PlainContents):
  """This sends a file straight to the browser"""
  def __init__(self, filepath):
    PlainContents.__init__(self, "")
    # tell the server what file to send
    self.sendfile_path = filepath

  def gethtml(self):
    """normally this won't be called, since the server will send the file directly"""
    return open(self.sendfile_path).read()

class SeparatedList(PlainContents):
  """This contains a list of items, and separates them with the given string..."""
  def __init__(self, contents, separator=", "):
    self.separator = separator
    PlainContents.__init__(self, contents)

  def getcontentshtml(self, contents):
    if isinstance(contents, (tuple, list)):
      # need to use parent method to prevent separators from winding down...
      contentslist = [PlainContents.getcontentshtml(self, contentspart) for contentspart in contents]
      for index in range(len(contentslist)-1):
        contentslist[index] = contentslist[index].rstrip("\r")
      # TODO: investigate ways to neaten this up while still preventing ASCII decoding error...
      typelist = [type(p) for p in contentslist]
      if unicode in typelist and str in typelist:
        for n in range(len(contentslist)):
          if isinstance(contentslist[n], str):
            contentslist[n] = contentslist[n].decode('utf8')
      return self.separator.join(contentslist)
    else:
      return PlainContents.getcontentshtml(self, contents)

class Font(ContentWidget):
  def __init__(self, contents, newattribs={}):
    ContentWidget.__init__(self, "FONT", contents, newattribs)

class Button(ContentWidget):
  # Represents a button widget.  
  def __init__(self, newattribs = {}, label = ""):
    ContentWidget.__init__(self, "BUTTON", label)
    self.attribs = {'type':'button', 'value':'pass'}
    self.overrideattribs(newattribs)

class Image(Widget):
  # Represents a button widget.  
  def __init__(self, src, newattribs = {}):
    Widget.__init__(self, "IMG")
    self.attribs = {'type':'button', 'src': src}
    self.overrideattribs(newattribs)

class Item(ContentWidget):
  def __init__(self, contents, newattribs = {}):
    ContentWidget.__init__(self, "li", contents, newattribs)

class UList(ContentWidget):
  def __init__(self, contents, newattribs = {}):
    ContentWidget.__init__(self, "ul", contents, newattribs)

class OList(ContentWidget):
  def __init__(self, contents, newattribs = {}):
    ContentWidget.__init__(self, "ol", contents, newattribs)

class Option(ContentWidget):
  def __init__(self, value, description, selected=0, newattribs={}):
    ContentWidget.__init__(self, "OPTION", description, {'VALUE': value})
    self.overrideattribs(newattribs)
    if selected:
      self.attribs["selected"] = "selected"

class Select(ContentWidget):
  # Represents a combo box or Select type. Parameters include a list of options which are made
  # available when the user clicks on the down arrow. The value of the selection
  # is assigned to the parameter name when the form is closed. Note that the combo
  # must be enclosed in a form.
  # The options list is a list of tuples with the value as the first element and
  # the description as the second element.
  def __init__(self, newattribs = {}, options = []):
    # TODO: pass value as a separate option
    self.selectedvalue = newattribs.get('value', '')
    ContentWidget.__init__(self, "SELECT", [], {'name':'NewCombo', 'value':''})
    self.overrideattribs(newattribs)
    self.addoptions(options)

  def addoptions(self, options):
    """adds the options to the select widget"""
    for value, description in options:
      if isinstance(value, Option):
        self.addcontents(value)
        continue
      if not isinstance(value, basestring):
        value = str(value)
      selected = self.isselected(value)
      optionwidget = Option(value, description, selected)
      self.addcontents(optionwidget)

  def isselected(self, value):
    """returns whether a value is selected or not"""
    return (value.lower() == self.selectedvalue.lower())

class MultiSelect(Select):
  def __init__(self, newattribs = {}, options = []):
    """builds the multiple-option select box"""
    Select.__init__(self, newattribs, [])
    self.overrideattribs({"multiple": None})
    if isinstance(self.selectedvalue, (str, unicode)):
      self.selectedvalue = [self.selectedvalue.lower()]
    elif isinstance(self.selectedvalue, list):
      self.selectedvalue = [value.lower() for value in self.selectedvalue]
    self.addoptions(options)

  def gethtml(self):
    selecthtml = Select.gethtml(self)
    if "name" in self.attribs:
      selecthtml += HiddenFieldList({"allowmultikey":self.attribs["name"]}).gethtml()
    return selecthtml

  def isselected(self, value):
    """returns whether a value is selected or not"""
    return (value.lower() in self.selectedvalue)

class Input(Widget):
  def __init__(self, newattribs, readonly=0):
    Widget.__init__(self,"INPUT")
    self.attribs = {'type':'text','name':'NewName', 'value':''}
    if readonly:
      self.attribs['readonly'] = 'true'
    self.overrideattribs(newattribs)

  def gethtml(self):
    return "<"+self.tagname+" "+self.gethtmlattribs()+ "/>\r"    

class Link(ContentWidget):
  def __init__(self, href, contents, newattribs={}):
    ContentWidget.__init__(self, "A", contents)
    self.attribs = {'href':href}
    self.overrideattribs(newattribs)

  def escapeattribvalue(self, key, value):
    """returns the value escaped appropriately for the key..."""
    if key.lower() == 'href':
      return self.escape(value, quote=1).replace(" ", "%20")
    else:
      return self.escape(value, quote=1)

class Tooltip(ContentWidget):
  def __init__(self, tooltip, contents, newattribs={}):
    ContentWidget.__init__(self, "SPAN", contents)
    self.attribs = {'title':tooltip}
    self.overrideattribs(newattribs)

class TextArea(ContentWidget):
  def __init__(self, newattribs, readonly = 0, contents = ""):
    if contents is None: contents = ""
    ContentWidget.__init__(self, "TEXTAREA", contents)
    self.attribs = {'name':'NewName'}
    if readonly:
      self.attribs['readonly'] = 'true'
    self.overrideattribs(newattribs)
    self.name = self.attribs['name']

class Paragraph(ContentWidget):
  """this is a simple widgetlist wrapping some widgets in a paragraph"""
  def __init__(self, contents=None, newattribs={}):
    ContentWidget.__init__(self, tagname="p", contents=contents, newattribs=newattribs)

class Page(ContentWidget):
  def __init__(self, title="", contents=None, newattribs={}, stylesheets=None, script="", headerwidgets=None, doctype=None):
    ContentWidget.__init__(self, None, contents, newattribs)
    self.title = title
    if headerwidgets is None: headerwidgets = []
    if stylesheets is None:
      # TODO: find a better place to specify the default
      self.stylesheets = ["/css/default.css", "/css/print.css"]
      if self.attribs.get('underlinelinks',1):
        self.stylesheets.append("/css/plainlinks.css")
      else:
        self.stylesheets.append("/css/nounderlinelinks.css")
    elif isinstance(stylesheets, (str, unicode)):
      self.stylesheets = [stylesheets]
    else:
      self.stylesheets = stylesheets
    self.headerwidgets = headerwidgets
    self.script = PlainContents(script)
    self.doctype = doctype

  def gethtml(self):
    header, body, footer = self.getheader(), self.getbody(), self.getfooter()
    if self.doctype:
      doctype = self.doctype
    else:
      doctype = ""
    if True in [isinstance(x, unicode) for x in (header, body, footer, doctype)]:
      if isinstance(header, str): header = header.decode('utf8')
      if isinstance(body, str): body = body.decode('utf8')
      if isinstance(footer, str): footer = footer.decode('utf8')
      if isinstance(doctype, str): doctype = doctype.decode('utf8')
    return doctype + header + body + footer

  def getheader(self):
    base=self.attribs.get('base','')
    target=self.attribs.get('target','')
    refresh=self.attribs.get('refresh',None)
    refreshurl=self.attribs.get('refreshurl',None)
    result = """
      <html>
      <head>
      <title>%s</title>""" % self.title
    # meta info
    result += """
      <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">"""
    if refresh is not None:
      if refreshurl is None:
        result += """<meta http-equiv="Refresh" content="%d">""" % (refresh)
      else:
        # TODO: check out the URL escaping more thoroughly...
        # escape query as spaces cause problems when refreshing...
        refreshurl = refreshurl.replace(' ','%20')
        result += """<meta http-equiv="Refresh" content="%d; URL=%s">""" % (refresh, refreshurl)
    # stylesheet info
    for stylesheet in self.stylesheets:
      result += """
        <LINK REL="stylesheet" TYPE="text/css" HREF="%s">""" % stylesheet
    # base/target info
    if base != '' or target != '': result += """
      <BASE href="%s" target="%s">""" % (base, target)
    # any script required
    for widget in self.headerwidgets:
      result += widget.gethtml()
    result += self.script.gethtml()
    # finished the head
    result += """
      </head>"""
    return result

  def getbody(self):
    # start the body...
    onload=self.attribs.get('onload',None)
    includeheading=self.attribs.get('includeheading',1)
    bgcolor=self.attribs.get('bgcolor',"#ffffff")
    if onload is None:
      start = """<body bgcolor="%s">""" % bgcolor
    else:
      start = """<body bgcolor="%s" onload="%s">""" % (bgcolor,onload)
    if includeheading and self.title is not None:
      start += """
      <h1>%s</h1>""" % (self.title)
    end = "</body>"
    contents = self.getcontents()
    if True in [isinstance(x, unicode) for x in (start, contents, end)]:
      if isinstance(start, str): start = start.decode('utf8')
      if isinstance(contents, str): contents = contents.decode('utf8')
      if isinstance(end, str): end = end.decode('utf8')
    return start + contents + end

  def getfooter(self):
    return """
      </html>
      """

class Frame(Widget):
  def __init__(self, name, src, newattribs={}):
    Widget.__init__(self, 'frame')
    self.name = name
    self.src = src
    self.attribs = {'name':name, 'src':src}
    self.overrideattribs(newattribs)

class NoFrames(ContentWidget):
  def __init__(self, contents=None, newattribs={}):
    ContentWidget.__init__(self, 'noframes', contents, newattribs)

class Frameset(ContentWidget):
  def __init__(self, newattribs={}, frames=None, noframes=None):
    if noframes is None:
      noframes = NoFrames()
    if frames is None:
      frames = []
    ContentWidget.__init__(self, 'frameset', frames, newattribs)
    self.addcontents(noframes)

class Script(ContentWidget):
  def __init__(self, language, scripttext, newattribs = {}):
    if len(scripttext.strip()) == 0:
      # may have no contents if for example it has a src attribute
      contents = ""
    else:
      # make the contents include the script text and comments to hide it from old browsers
      contents = "\r<!--\r" + scripttext + "\r//-->\r"
    ContentWidget.__init__(self, "script", contents)
    self.attribs = {'type':language}
    self.overrideattribs(newattribs)

class Form(ContentWidget):
  def __init__(self, contents=None, newattribs={}):
    # by default, post as NewName to the current URL
    ContentWidget.__init__(self, 'form', contents)
    self.attribs = {'method':'post','name':'NewName','action':''}
    self.overrideattribs(newattribs)

class HiddenFieldList(PlainContents):
  """this is a PlainContents containing a list of hidden fields"""
  def __init__(self, fielddict):
    """create a HiddenFieldList with fielddict containing the field definitions
    fielddict can be a dictionary or a list of key, value pairs"""
    fieldwidgets = []
    if isinstance(fielddict, list):
      fielditer = fielddict
    else:
      fielditer = fielddict.iteritems()
    for fieldname, fieldvalue in fielditer:
      fieldwidget = Input({'type':'hidden', 'name':fieldname, 'value':fieldvalue})
      fieldwidgets.append(fieldwidget)
    PlainContents.__init__(self, fieldwidgets)

class Division(ContentWidget):
  """an html div tag"""
  def __init__(self, contents=None, id=None, cls=None, newattribs={}):
    """constructs the div tag"""
    ContentWidget.__init__(self, 'div', contents)
    if id is not None:
      self.attribs['id'] = id
    if cls is not None:
      self.attribs['class'] = cls
    self.overrideattribs(newattribs)

class Span(ContentWidget):
  """an html span tag"""
  def __init__(self, contents=None, id=None, cls=None, newattribs={}):
    """constructs the span tag"""
    ContentWidget.__init__(self, 'span', contents)
    if id is not None:
      self.attribs['id'] = id
    if cls is not None:
      self.attribs['class'] = cls
    self.overrideattribs(newattribs)

def getrgb(color, default = '&H808080'):
  """take various color formats and convert them to the html format"""
  if color is None:
    color = default
  if color[:2] == '&H':
    color = color[2:]
  else:
    try:
      color = "%06x" % int(color)
    except:
      pass
  if len(color) == 6:
    color = color[4:6] + color[2:4] + color[0:2]
  return color


#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""this is a jToolkit template server using SimpleTAL"""

# Copyright 2005 St James Software
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

from jToolkit.web import server
from jToolkit.widgets import widgets
try:
  import kid
except ImportError:
  kid = None
try:
  from jToolkit.xml import DOMOverlay
except ImportError:
  DOMOverlay = None
import os
import sys
import imp
import mimetypes
import pprint

class AttrDict(dict):
  """Dictionary that also allows access to keys using attributes"""
  def __getattr__(self, attr, default=None):
    if attr in self:
      return self[attr]
    else:
      return default

def attribify(context):
  """takes a set of nested dictionaries and converts them into AttrDict. Also searches through lists"""
  if isinstance(context, dict) and not isinstance(context, AttrDict):
    newcontext = AttrDict(context)
    for key, value in newcontext.items():
      if isinstance(value, (dict, list)):
        newcontext[key] = attribify(value)
    return newcontext
  elif isinstance(context, list):
    for n, item in enumerate(context):
      if isinstance(item, (dict, list)):
        context[n] = attribify(item)
    return context
  else:
    return context

class TemplateCache(object):
  """caches templates and modules associated with them"""
  def __init__(self, templatedir=None, moduledir=None):
    self.templatedir = templatedir
    self.moduledir = moduledir
    self.templatecache = {}
    self.modulecache = {}

  def gettemplate(self, templatename):
    """loads a template from a file"""
    templatefilename = os.path.join(self.templatedir, templatename + ".html")
    currentmodtime = os.stat(templatefilename)[os.path.stat.ST_MTIME]
    if templatename in self.templatecache:
      lastmodtime, lasttemplate = self.templatecache[templatename]
      if currentmodtime == lastmodtime:
        return lasttemplate
    template = open(templatefilename, "r").read()
    self.templatecache[templatename] = currentmodtime, template
    return template

  def getmodule(self, templatename):
    """gets the module associated with a template"""
    # TODO: check how this works with similarly-named modules in different paths
    # (see vampire's approach)
    pyfilename = os.path.join(self.moduledir, templatename + ".py")
    if not os.path.exists(pyfilename):
      return None
    currentmodtime = os.stat(pyfilename)[os.path.stat.ST_MTIME]
    if templatename in self.modulecache:
      lastmodtime, lastmodule = self.modulecache[templatename]
      if currentmodtime == lastmodtime:
        return lastmodule
    try:
      if self.moduledir not in sys.path:
        sys.path.append(self.moduledir)
      imp.acquire_lock()
      modulefile = open(pyfilename, 'r')
      module = imp.load_module(templatename, modulefile, pyfilename, ('.py', 'U', 1))
      self.modulecache[templatename] = currentmodtime, module
      return module
    finally:
      imp.release_lock()

class TemplateCacheServer(server.AppServer, TemplateCache):
  """an AppServer equipped with a TemplateCache"""
  def __init__(self, instance, webserver=None, sessioncache=None, errorhandler=None, templatedir=None, pydir=None):
    """constructs a templateserver on the given template directory"""
    if pydir is None:
      pydir = templatedir
    super(TemplateCacheServer, self).__init__(instance, webserver, sessioncache, errorhandler)
    TemplateCache.__init__(self, templatedir, pydir)

  def sendpage(self, req, thepage):
    """bridge to widget code to allow templating to gradually replace it"""
    if kid is not None and hasattr(thepage, "templatename") and hasattr(thepage, "templatevars"):
      # renders using templates rather than the underlying widget class
      template = self.gettemplate(thepage.templatename)
      loadurl = getattr(thepage, "loadurl", None)
      if loadurl is None:
        loadurl = getattr(self, "loadurl", None)
      pagestring = self.buildpage(template, thepage.templatevars, loadurl, req.session.localize)
      builtpage = widgets.PlainContents(pagestring)
      # make sure certain attributes are retained on the built page
      for copyattr in ('content_type', 'logresponse', 'sendfile_path', 'allowcaching', 'etag'):
        if hasattr(thepage, copyattr):
          setattr(builtpage, copyattr, getattr(thepage, copyattr))
      thepage = builtpage
    elif isinstance(thepage, server.Redirect):
      if thepage.withtemplate:
        templatename, templatevars = (thepage.withtemplate)
        templatevars["refreshurl"] = thepage.location
        template = self.gettemplate(templatename)
        loadurl = getattr(self, "loadurl", None)
        pagestring = self.buildpage(template, templatevars, loadurl, req.session.localize)
        builtpage = widgets.PlainContents(pagestring)
        thepage.withpage = builtpage
    return super(TemplateCacheServer, self).sendpage(req, thepage)

  def buildpage(self, source, context, loadurl=None, localize=None, innerid=None):
    """build a response for the template with the vars in context"""
    if DOMOverlay is not None:
      innerid = context.pop("@innerid", None)
      if loadurl is None:
        loadurl = DOMOverlay.loadurl
      domoverlay = DOMOverlay.DOMOverlay(source, loadurl, context)
      source = domoverlay.serialise(innerid)
    context = attribify(context)
    t = kid.Template(source=source,**context)
    try:
      return t.serialize(output="xhtml")
    except Exception, e:
      tb = sys.exc_info()[2]
      tb_point = tb
      while tb_point.tb_next:
          tb_point = tb_point.tb_next
      ancestors = tb_point.tb_frame.f_locals.get("ancestors", [])
      xml_traceback = []
      for ancestor in ancestors:
          if ancestor is None: continue
          try:
            ancestor_str = kid.et.tostring(ancestor)
          except Exception, e:
            ancestor_str = "(could not convert %s: %s)" % (str(ancestor), str(e))
          xml_traceback.append(ancestor_str)
      context_str = pprint.pformat(context)
      xml_traceback_str = "  " + "\n  ".join(xml_traceback)
      self.errorhandler.logerror("Error converting template: %s\nContext\n%s\nXML Ancestors:\n%s\n%s\n" % (e, context_str, xml_traceback_str, self.errorhandler.traceback_str()))
      if self.webserver.options.debug:
        import pdb
        pdb.post_mortem(tb)
      raise

class RequestHandler:
  def __init__(self, req):
    self.req = req
    self.session = req.session
    self.argdict = req.argdict
    self.template = req.template
    self.templatevars = {}
  def handleaction(self, actionname):
    if actionname in self.argdict:
      actionhandler = getattr(self, actionname)
      actionvars = actionhandler()
      self.templatevars.update(actionvars)

class TemplateServer(TemplateCacheServer):
  """simple server that serves pages from templates"""
  def getpage(self, pathwords, session, argdict):
    """return a page that will be sent to the user"""
    import inspect

    class req(object): pass
    req.pathwords = pathwords
    req.session = session
    req.argdict = argdict

    top = "".join(pathwords[:1])
    if not top:
      top = "index.html"
    if top.endswith(".html"):
      templatename = top.replace(".html", "")
      pathwords = pathwords[1:]
      innerid = "".join(pathwords[:1]) or None
      template = self.gettemplate(templatename)
      module = self.getmodule(templatename)
      if module is not None:
        # get all classes in the module
        classes = [value for name,value in inspect.getmembers(module) if inspect.isclass(value)]
        assert len(classes) > 0, "Module contains no classes"
        # get all classes that inherit from RequestHandler
        handlers = [cls for cls in classes if issubclass(cls,RequestHandler)]
        assert len(handlers) == 1, "Module must contain exactly 1 subclass of RequestHandler"
        # make an instance of the handler
        req.template = template
        handler = handlers[0](req)
        context = handler.templatevars
      else:
        # no module, so no variables ...
        context = {}
      # build the page
      response = self.buildpage(template, context, innerid=innerid)
      if innerid:
        response = widgets.PlainContents(response)
        response.content_type = "text/xml"
      return response
    else:
      filepath = os.path.join(self.templatedir,*pathwords)
      response = widgets.PlainContents(None)
      response.content_type, encoding = mimetypes.guess_type(filepath)
      response.sendfile_path = filepath
      if response.content_type is None:
        return None
      return response


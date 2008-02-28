#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""implementation of XML overlays on the Python DOM libraries
provides required enhancements to the DOM libraries too, which are applied by importing this
"""

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

from jToolkit.xml.fixminidom import minidom
import re
import sre
import imp
try:
  from cStringIO import StringIO
except ImportError:
  from StringIO import StringIO

OverlayNamespaceURI = "http://dev.sjsoft.com/ns/overlay"

class escaped(basestring):
  """some kind of string that has already been escaped and doesn't need to be again"""
  pass

class escapedunicode(unicode, escaped):
  """unicode that has already been escaped and doesn't need to be again"""
  pass

class escapedstr(str, escaped):
  """str that has already been escaped and doesn't need to be again"""
  pass

def format(values,formatstring):
  """helper function for formatting strings"""
  return formatstring%values

def loadurl(urlname,context={}):
    """resolves a url and returns the results
    if the url starts with file:// then it will try to find a static file
    if it starts with python:// then it will try to find a python object"""
    parameter_re = "\s*(\w+\s*=|)\s*\w+\s*"
    namedparameter_re = "\s*((?P<key>\w+)\s*=|)\s*(?P<value>\w+)\s*"
    identifier_re = "(\w+[.])+\w+"
    module_re = "(?P<module>(%s))" % identifier_re
    parameters_re = "(?P<params>(%s,)*%s)" % (parameter_re, parameter_re)
    innerid_re = "[.]\w+"
    import_re = "\s*%s\s*(\(%s\)\s*|)" % (module_re, parameters_re)
    import_matcher = sre.compile(import_re)
    import_match = import_matcher.match(urlname)
    if not import_match:
        raise ValueError("Invalid overlay definition: %s" % urlname)
    module = import_match.group("module")
    moduleparts = module.split(".")
    
    #load the first part as that should be a module
    modulename = moduleparts.pop(0)
    includeobject = imp.load_module(modulename,*imp.find_module(modulename))

    #cycle through the rest of the url parts gathering objects as we go
    for part in moduleparts:
        if hasattr(includeobject,part):
            includeobject = getattr(includeobject,part)

    if callable(includeobject):
        parameters = import_match.group("params")
        includeargs = []
        includekwargs = {}
        if parameters:
            for parameterdef in parameters.split(","):
                namedparameter_match = sre.match(namedparameter_re, parameterdef)
                key = namedparameter_match.group("key")
                value = namedparameter_match.group("value")
                value = context.get(value)
                if key:
                    if isinstance(key, unicode):
                        key = key.encode("utf-8")
                    includekwargs[key] = context.get(value,value)
                else:
                    includeargs.append(context.get(value,value))
        includeobject = includeobject(*includeargs, **includekwargs)
    return str(includeobject)

    includesource = open(os.path.join(namespacedir, filename), "r").read()
    return includesource

class DOMOverlay:
  """class that allows special attributes to do XUL-style overlays on XML DOM trees"""
  def __init__(self, source, loadurlcallback=loadurl, context={}):
    if isinstance(source, basestring):
      self.sourcedom = minidom.parseString(source)
    else:
      self.sourcedom = source
    self.context = context
    self.loadurlcallback = loadurlcallback

  operations = ["include", "insertbefore", "insertafter", "replace", "delete"]

  def loadurl(self, filename):
    """loads the given filename and returns the contents as a string"""
    if self.loadurlcallback:
        return self.loadurlcallback(filename,self.context)
    else:
        return open(filename, "r").read()

  def appendchildren(self,parentnode,childnode):
    """
    Adds children to the parentnode.
    If children is a list then it adds all of the items in the list
    """
    for node in childnode:
      if isinstance(node,tuple):
        parent,children = node
        parent = self.appendchildren(parent,children)
        parentnode.appendChild(parent)
      elif isinstance(node,list):
        self.appendchildren(parentnode,list)
      else:
        parentnode.appendChild(node)
    return parentnode

  def sortoperations(self, a, b):
    """return whether a should be before or after b"""
    return self.operations.index(a[0]) - self.operations.index(b[0])

  def getElementById(self, rootnode, id):
    """searches for an element by id within a rootnode (depth-first)"""
    for childnode in rootnode.childNodes:
      if isinstance(childnode, minidom.Element):
        attrs = childnode.attributes._attrs
        if "id" in attrs and attrs["id"].value == id:
          return childnode
        childidresult = self.getElementById(childnode, id)
        if childidresult is not None:
          return childidresult
    return None

  def separateattributes(self, srcnode):
    """separates attributes into overlay attributes and other attributes, returning a tuple"""
    overlayattrs, standardattrs = [], []
    for attr in srcnode.attributes.values():
      if attr.nodeName.startswith("over:"):
        overlayattrs.append(attr)
      else:
        standardattrs.append(attr)
    return overlayattrs, standardattrs

  def overlayexpand(self, srcnode):
    """returns an expanded node using any over: attributes"""
    newOwnerDocument = srcnode.ownerDocument   # will be changed when reattaching
    if isinstance(srcnode, minidom.DocumentType):
      # documenttypes can't be cloned
      targetnode = minidom.DocumentType(None)
      targetnode.name = srcnode.name
      targetnode.nodeName = srcnode.name
      srcnode._call_user_data_handler(minidom.xml.dom.UserDataHandler.NODE_CLONED, srcnode, targetnode)
      return targetnode
    includechildren = True
    isincludenode = False
    if isinstance(srcnode, minidom.Element):
      targetnode = newOwnerDocument.createElementNS(srcnode.namespaceURI, srcnode.nodeName)
      overlayoperations = []
      operationspresent = {}
      overlayattrs, standardattrs = self.separateattributes(srcnode)
      for attr in overlayattrs:
        operation = attr.nodeName.replace("over:", "", 1)
        if operation in self.operations:
          overlayoperations.append((operation, attr.value))
          operationspresent[operation] = True
        else:
          print "unknown overlay operation: %s in tag %r" % (operation, srcnode)
      getparameters = lambda filterop: [parameter for operation, parameter in overlayoperations if operation == filterop]
      if "include" in operationspresent:
        isincludenode = True
        for parameter in getparameters("include"):
          if "#" in parameter:
            includeurl, includeid = parameter.split("#", 1)
          else:
            includeurl, includeid = parameter, ""
          if includeurl:
            includtarget = self.context.get(includeurl)
            if includtarget is None:
                includesrctext = self.loadurl(includeurl)
            else:
                includesrctext = str(includtarget)
            includedom = minidom.parseString(includesrctext)
          else:
            includedom = self.sourcedom
          if includeid:
            includesrcnode = includedom.getElementById(includeid)
          else:
            if isinstance(includedom, minidom.Document):
              includesrcnode = includedom.documentElement
            else:
              includesrcnode = includedom
          includetargetnode = self.overlayexpand(includesrcnode)
          for attr in includetargetnode.attributes.values():
            if not attr.nodeName in standardattrs:
              targetnode.setAttributeNS(attr.namespaceURI, attr.nodeName, attr.value)
              a = targetnode.getAttributeNodeNS(attr.namespaceURI, attr.localName)
              a.specified = attr.specified
          for includechild in includetargetnode.childNodes:
            if isinstance(includechild, list):
              targetnode = self.appendchildren(targetnode, includechild)
            else:
              includechild = includechild.cloneNode(deep=True)
              targetnode.appendChild(includechild)
      overlayoperations.sort(self.sortoperations)
      for attr in standardattrs:
        if attr.nodeName == "xmlns:over" and attr.value == OverlayNamespaceURI:
            continue
        targetnode.setAttributeNS(attr.namespaceURI, attr.nodeName, attr.value)
        a = targetnode.getAttributeNodeNS(attr.namespaceURI, attr.localName)
        a.specified = attr.specified
      for operation, parameter in overlayoperations:
        if operation != "include":
          targetnode.setAttribute("over:" + operation, parameter)
    elif isinstance(srcnode, minidom.Text):
      targetnode = srcnode.cloneNode(deep=False)
    else:
      targetnode = srcnode.cloneNode(deep=False)
    if includechildren:
      for srcchild in srcnode.childNodes:
        targetchild = self.overlayexpand(srcchild)
        if isincludenode and self.dooverlay(targetchild, targetnode):
          continue
        if targetchild is None:
          break
        elif isinstance(targetchild, list):
          targetnode = self.appendchildren(targetnode,targetchild)
        else:
          targetnode.appendChild(targetchild)
    return targetnode

  def dooverlay(self, targetchild, targetnode):
    """does an overlay operation defined on a node"""
    if targetchild.attributes:
      overlayattrs, standardattrs = self.separateattributes(targetchild)
      handledchild = False
      for attr in overlayattrs:
        targetchild.removeAttributeNS(attr.namespaceURI, attr.localName)
        operation = attr.nodeName.replace("over:", "", 1)
        referredsibling = self.getElementById(targetnode, attr.value)
        if referredsibling is None:
          raise ValueError("Could not find node %s to do operation %s on" % (attr.value, operation))
        operationnode = referredsibling.parentNode
        if operation == "insertbefore":
          operationnode.insertBefore(targetchild, referredsibling)
          handledchild = True
        elif operation == "insertafter":
          referredsibling = referredsibling.nextSibling
          if referredsibling:
            operationnode.insertBefore(targetchild, referredsibling)
          else:
            operationnode.appendChild(targetchild)
          handledchild = True
        elif operation == "replace":
          operationnode.replaceChild(targetchild, referredsibling)
          handledchild = True
        elif operation == "delete":
          operationnode.removeChild(referredsibling)
          handledchild = True
        else:
          print "unknown overlay operation: %s in tag %r" % (operation, srcnode)
      return handledchild

  def expand(self, innerid=None):
    """expands the template (or a subtemplate using innerid)"""
    if innerid is None:
      targetnode = minidom.Document()
      for srcchild in self.sourcedom.childNodes:
        targetchild = self.overlayexpand(srcchild)
        if targetchild is not None:
          targetnode.appendChild(targetchild)
    else:
      srcnode = self.sourcedom.getElementById(innerid)
      if srcnode is None:
        return None
      targetnode = minidom.Document()
      targetchild = self.overlayexpand(srcnode)
      # try and inherit namespaces...
      for mainnode in self.sourcedom.childNodes:
        attrs = getattr(mainnode, "_attrs", {})
        for attr, attrvalue in attrs.iteritems():
          if attr.startswith("xmlns"):
            # TODO: fix me and do this properly
            targetchild._attrs[attr] = attrvalue
      targetnode.appendChild(targetchild)
    return targetnode

  def serialise(self,innerid=None):
    """returns text representation of the expanded template"""
    return self.expand(innerid).toxml("utf-8")

def CompileXML(source, loadurlcallback=None, context={}):
  return DOMOverlay(source, loadurlcallback, context)


#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""implementation of TAL templating on the Python DOM libraries
if simpletal is installed, it will fall back to that (for possible performance gains)
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
try:
  from simpletal import simpleTAL, simpleTALES
except ImportError:
  simpleTAL, simpleTALES = None, None
try:
  from cStringIO import StringIO
except ImportError:
  from StringIO import StringIO

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
  
class DOMTemplate:
  def __init__(self, sourcedom):
    self.sourcedom = sourcedom
    self.contextstack = []
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

  def getcontext(self):
    """merges the levels of the context stack so that local 
    variables can override global variables only within their scope"""
    localcontext = {}
    for context in self.contextstack:
      localcontext.update(context)
    return localcontext
  
  def taleval(self, expr, context):
    """evaluates a tal expression using the context"""
    if expr.startswith("not "):
      result = not self.taleval(expr.replace("not ", "", 1), context)
      return result
    if expr.startswith("python:"):
      expression, formatting = self.parseformat(expr)
      if formatting is None:
        return None
      # expand the TALES path and perform evaluate the function
      value = self.taleval(expression, context)
      return format(value,formatting)
    if "/" in expr:
      parentvar, subexpr = expr.split("/", 1)
      if parentvar in context:
        return self.taleval(subexpr, context[parentvar])
      # print expr, "not found", repr(parentvar), parentvar in context, context.keys()
      return None
    if expr in context:
      return context[expr]
    return None

  def findtalattrs(self, srcnode=None):
    """returns a list of all the tal attributes defined"""
    if srcnode is None:
      srcnode = self.sourcedom
    attrs = []
    if isinstance(srcnode, minidom.Element):
      for attr in srcnode.attributes.values():
        if attr.nodeName.startswith("tal:"):
          attrs.append((srcnode.nodeName, attr.nodeName, attr.value))
    for srcchild in srcnode.childNodes:
      attrs += self.findtalattrs(srcchild)
    return attrs

  def findtalvarnames(self, srcnode=None):
    """returns a list of all the variable names expected"""
    expressions = []
    repeatvars = []
    for nodename, attrname, parameter in self.findtalattrs(srcnode):
      if attrname == "tal:content":
        expressions.append(parameter)
      elif attrname == "tal:repeat":
        repeatvar, repeatexpr = self.parserepeat(parameter)
        expressions.append(repeatexpr)
        repeatvars.append(repeatvar)
      elif attrname == "tal:attributes":
        for attrname, attrexpr in self.parseattributes(parameter):
          expressions.append(attrexpr)
    for expression in expressions:
      while expression.startswith("not "):
        expression = expression.replace("not ", "", 1)
      if expression.startswith("python:"):
        expression, format = self.parseformat(expression)
      if expression not in repeatvars:
        yield expression

  def parserepeat(self, parameter):
    """returns the repeat variable and repeat expression"""
    repeatvar, repeatexpr = parameter.split(" ", 1)
    return repeatvar, repeatexpr

  def parseattributes(self, parameter):
    """yields a list of attribute names and value expressions"""
    attributedefs = parameter.split(";")
    for attributedef in attributedefs:
      attrname, attrexpr = attributedef.strip().split(" ", 1)
      yield attrname, attrexpr

  def parseformat(self, parameter):
    """returns a (expression, format string) tuple"""
    if parameter.startswith("python:"):
      pythonpart = parameter.replace("python:", "", 1)
      match = re.match("^format\((.*),['](.*)[']\)$",pythonpart)
      if match:
        expression = match.group(1)
        formatting = match.group(2)
        return expression, formatting
    return None, None

  def sortoperations(self, a, b):
    """return whether a should be before or after b"""
    operations = ["condition", "define", "content", "repeat", "attributes", "named"]
    return operations.index(a[0]) - operations.index(b[0])
    
  def talexpand(self, srcnode, localize=None, forrepeatvar=None):
    """returns an expanded node using the context variables and any tal: attributes"""
    context = self.getcontext()
    contextframe = {"id":srcnode}
    self.contextstack.append(contextframe)
    newOwnerDocument = srcnode.ownerDocument   # will be changed when reattaching
    if isinstance(srcnode, minidom.DocumentType):
      # documenttypes can't be cloned
      targetnode = minidom.DocumentType(None)
      targetnode.name = srcnode.name
      targetnode.nodeName = srcnode.name
      srcnode._call_user_data_handler(minidom.xml.dom.UserDataHandler.NODE_CLONED, srcnode, targetnode)
      return targetnode
    includechildren = True
    if isinstance(srcnode, minidom.Element):
      targetnode = newOwnerDocument.createElementNS(srcnode.namespaceURI, srcnode.nodeName)
      taloperations = []
      operationspresent = {}
      standardattrs, derivedattrs = [], []
      repeatvar = None
      for attr in srcnode.attributes.values():
        if attr.nodeName.startswith("tal:"):
          operation = attr.nodeName.replace("tal:", "", 1)
          if operation in ("content", "repeat", "condition", "attributes", "named", "define"):
            taloperations.append((operation, attr.value))
            operationspresent[operation] = True
          else:
            print "unknown tal operation: %s in tag %r" % (operation, srcnode)
        else:
          standardattrs.append(attr)
      getparameters = lambda filterop: [parameter for operation, parameter in taloperations if operation == filterop]
      if "repeat" in operationspresent:
        for parameter in getparameters("repeat"):
          repeatvar, repeatexpr = self.parserepeat(parameter)
          if repeatvar == forrepeatvar:
            continue
          ## if repeatvar in context:
            ## raise ValueError("repeatvar %s already defined in context" % (repeatvar))
          repeatitems = self.taleval(repeatexpr, context)

          #repeatitems is a list of dictionaries
          repeatnodes = []
          for repeatvalue in repeatitems:
            contextframe[repeatvar] = repeatvalue
            repeatnodes.append(self.talexpand(srcnode, localize, repeatvar))

          self.contextstack.pop()
          return repeatnodes
      taloperations.sort(self.sortoperations)
      for operation, parameter in taloperations:
        if operation == "content":
          content = self.taleval(parameter, context)
          if content is not None:
            if isinstance(content, escaped):
              # this is awful. but its the easiest way of not escaping the data...
              contentdocument = "<xml>" + content + "</xml>"
              contentnode = minidom.parseString(contentdocument).firstChild
              for childnode in contentnode.childNodes:
                targetnode.appendChild(childnode.cloneNode(deep=True))
            elif isinstance(content,minidom.Element):
              contentnode = self.talexpand(content.cloneNode(deep=True))
              targetnode.appendChild(contentnode)
            else:
              contentnode = newOwnerDocument.createTextNode(content)
              targetnode.appendChild(contentnode)
          includechildren = False
        elif operation == "repeat":
          pass
        elif operation == "condition":
          condition = self.taleval(parameter, context)
          if not condition:
            self.contextstack.pop()
            return []
        elif operation == "attributes":
          for attrname, attrexpr in self.parseattributes(parameter):
            attrvalue = self.taleval(attrexpr, context)
            if attrvalue is not None:
              targetnode.setAttribute(attrname, attrvalue)
              derivedattrs.append(attrname)
        elif operation == "named":
          # Defines a named template in the global context
          self.contextstack[0][parameter] = srcnode
        elif operation == "define":
          # a tal variable is being defined:
          # argument       ::= define_scope [';' define_scope]*
          # define_scope   ::= (['local'] | 'global') define_var
          # define_var     ::= variable_name expression
          # variable_name  ::= Name          variable_name, expression = parameter.split(" ")
          if parameter.startswith('local'):
            scope = 'local'
            parameter = parameter.replace('local ','')
          elif parameter.startswith('global'):
            scope = 'global'
            parameter = parameter.replace('global ','')
          else:
            scope = 'local'
          variable_name,expression = parameter.split(' ')
          value = self.taleval(expression,context)
          if value:
            if scope == 'global':
              self.contextstack[0][variable_name] = value
            if scope == 'local':
              #local scope
              contextframe[variable_name] = value
      for attr in standardattrs:
        if not attr.nodeName in derivedattrs:
          targetnode.setAttributeNS(attr.namespaceURI, attr.nodeName, attr.value)
          a = targetnode.getAttributeNodeNS(attr.namespaceURI, attr.localName)
          a.specified = attr.specified
    elif isinstance(srcnode, minidom.Text):
      text = srcnode.data.strip()
      if text and localize is not None:
        textpos = srcnode.data.find(text)
        lwhitespace, rwhitespace = srcnode.data[:textpos], srcnode.data[textpos+len(text):]
        text = lwhitespace + localize(text) + rwhitespace
        # TODO: handle XML within the localization...
        targetnode = newOwnerDocument.createTextNode(text)
      else:
        targetnode = srcnode.cloneNode(deep=False)
    else:
      targetnode = srcnode.cloneNode(deep=False)
    if includechildren:
      for srcchild in srcnode.childNodes:
        targetchild = self.talexpand(srcchild, localize)
        if targetchild is None:
          break
        elif isinstance(targetchild, list):
          targetnode = self.appendchildren(targetnode,targetchild)
        else:
          targetnode.appendChild(targetchild)
    self.contextstack.pop()
    return targetnode

  def expand(self, context, innerid=None, localize=None):
    """expands the template (or a subtemplate using innerid) with the given context. localizes if localize given"""
    # put the global context into the context stack
    self.contextstack.append(context)
    if innerid is None:
      targetnode = minidom.Document()
      for srcchild in self.sourcedom.childNodes:
        targetchild = self.talexpand(srcchild, localize)
        if targetchild is not None:
          targetnode.appendChild(targetchild)
    else:
      srcnode = self.sourcedom.getElementById(innerid)
      targetnode = minidom.Document()
      targetchild = self.talexpand(srcnode, localize)
      targetnode.appendChild(targetchild)
    # print "nodetype", targetnode.nodeType, minidom.Node.DOCUMENT_NODE
    return targetnode.toxml("utf-8")

# alternative implementations using the functions here and the simpleTAL ones

# jToolkitTAL (this module) wrappers

class jToolkitTALContext(dict):
  def addGlobal(self, key, value):
    self[key] = value
  def evaluate(self, expr, originalAtts=None):
    return self[expr]

def jToolkitTALcompileXMLTemplate(source):
  sourcedom = minidom.parseString(source)
  return DOMTemplate(sourcedom)

# simpleTAL modifications

if simpleTAL is not None:
  XMLTemplate = simpleTAL.XMLTemplate
  class XMLTemplateWithInnerId(XMLTemplate):
      def expand(self, context, innerid=None):
          if innerid is not None:
              if innerid in self.innertemplates:
                  innertemplate = self.innertemplates[innerid]
              else:
                  innerelement = self.sourcedom.getElementById(innerid)
                  if innerelement:
                      innersource = innerelement.toxml().encode("UTF-8")
                      innertemplate = simpleTAL.compileXMLTemplate(innersource)
                      self.innertemplates[innerid] = innertemplate
                  else:
                      raise ValueError("innerid %s not found: %r" % (innerid, self.sourcedom._id_cache))
              return innertemplate.expand(context)
          outputbuf = StringIO()
          XMLTemplate.expand(self, context, outputbuf)
          return outputbuf.getvalue()
  simpleTAL.XMLTemplate = XMLTemplateWithInnerId

# simpleTAL wrappers

def simpleTALcompileXMLTemplate(source):
  sourcedom = minidom.parseString(source)
  template = simpleTAL.compileXMLTemplate(source)
  template.sourcedom = sourcedom
  template.innertemplates = {}
  return template

# switch implementations

implementation = None

def usesimpleTAL():
  global Context, compileXMLTemplate, implementation
  Context = simpleTALES.Context
  compileXMLTemplate = simpleTALcompileXMLTemplate
  implementation = "simpleTAL"

def usejToolkitTAL():
  global Context, compileXMLTemplate, implementation
  Context = jToolkitTALContext
  compileXMLTemplate = jToolkitTALcompileXMLTemplate
  implementation = "jToolkitTAL"

# use jToolkit TAL by default
usejToolkitTAL()


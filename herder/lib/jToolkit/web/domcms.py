# -*- coding: utf-8 -*-
from elementtree import ElementTree

def compile(htmlfile,handlers):
  """
  parses an html file and searches for the id's defined in the keys of handlers
  if it finds a match then it passes the element with the id to the function it maps to
  """
  
  dom = ElementTree.parse(htmlfile)
  root = dom.getroot()

  parentmap = GetParentMap(dom)

  #check all subelements for id's and try to match them up to a handler
  #note that this iterates through all levels of the tree, not just direct children
  for element in dom.getiterator():
    if element.attrib.has_key('id'):
      id = element.attrib.get('id')

      #if we find a handler for this id then pass the element to the handler
      if handlers.has_key(id):

        #if element is None then it should be removed
        #find the parent and remove this element
        if handlers[id](element) is False:
          parentmap[element].remove(element)

  print ElementTree.tostring(root)
  return ElementTree.tostring(root)

def GetParentMap(dom):
  """
  returns a dictionary mapping children to parents
  """
  map={}
  for p in dom.getiterator():
    for c in p:
      map[c] = p
  return map

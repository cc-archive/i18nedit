#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""provides required enhancements to the DOM libraries, which are applied by importing this"""

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

from xml.dom import minidom
from xml.dom import expatbuilder

Attr = minidom.Attr
class AttrWithID(Attr):
  """Attr object that checks if its name is id and makes itself a magic id"""
  def __init__(self, *args, **kwargs):
    Attr.__init__(self, *args, **kwargs)
    if self.name == 'id':
      self.__dict__['_is_id'] = True
  def unlink(self):
    """unlink the Attr from the ownerElement/Document, preventing our _is_id from causing problems"""
    if self._is_id and self.ownerDocument is None:
      self._is_id = False
      Attr.unlink(self)
      self._is_id = True
    else:
      Attr.unlink(self)
minidom.Attr = AttrWithID

ExpatBuilderNS = expatbuilder.ExpatBuilderNS
class ExpatBuilderNSWithID(ExpatBuilderNS):
  """ExpatBuilder that checks for magic Attr ids"""
  def start_element_handler(self, name, attributes):
    ExpatBuilderNS.start_element_handler(self, name, attributes)
    node = self.curNode
    for aname, a in node._attrs.iteritems():
      if a._is_id:
        node._magic_id_nodes += 1
        node.ownerDocument._magic_id_count += 1
        node.ownerDocument._id_cache.clear()
        node.ownerDocument._id_search_stack = None
expatbuilder.ExpatBuilderNS = ExpatBuilderNSWithID


#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""this is a jToolkit tutorial"""

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

from jToolkit.web import server
from jToolkit.web import templateserver
from jToolkit.widgets import widgets
import os
import imp

class TutorialServer(templateserver.TemplateServer):
  """the Server that serves the Tutorial Pages"""
  def __init__(self, instance, webserver=None, sessioncache=None, errorhandler=None):
    templatedir = os.path.dirname(os.path.abspath(__file__))
    templateserver.TemplateServer.__init__(self, instance, webserver, sessioncache, errorhandler, templatedir=templatedir)

  def getpage(self, pathwords, session, argdict):
    """return a page that will be sent to the user"""
    top = "".join(pathwords[:1])
    if top == "src":
      return self.getsource(pathwords[1:], session, argdict)
    return templateserver.TemplateServer.getpage(self, pathwords, session, argdict)

  def getsource(self, pathwords, session, argdict):
    """returns the source code of the page"""
    filename = os.path.join(*pathwords)
    if not os.path.exists(filename): 
      return None
    page = widgets.PlainContents(open(filename, 'r').read())
    page.content_type = "text/plain"
    return page

if __name__ == '__main__':
  # run the web server
  from jToolkit.web import simplewebserver
  parser = simplewebserver.WebOptionParser()
  parser.set_default('prefsfile', 'tutorial.prefs')
  parser.set_default('instance', 'TutorialConfig')
  parser.set_default('htmldir', os.curdir)
  options, args = parser.parse_args()
  server = parser.getserver(options)
  simplewebserver.run(server, options)


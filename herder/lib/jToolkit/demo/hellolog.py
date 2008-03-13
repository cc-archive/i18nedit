#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""this is a Hello Log-style demonstration program of jToolkit"""

from jToolkit.web import server
from jToolkit.widgets import widgets

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

import os, threading

class HelloLogServer(server.AppServer):
  """the Server that serves the Hello Log Pages"""
  def getpage(self, pathwords, session, argdict):
    """return a page that will be sent to the user"""
    self.errorhandler.logtrace("Log Trace")
    return widgets.PlainContents("Hello Log from process %08x/%08x and thread %s" % (os.getppid(), os.getpid(), threading.currentThread().getName()))

if __name__ == '__main__':
  # run the web server
  from jToolkit.web import simplewebserver
  parser = simplewebserver.WebOptionParser()
  parser.set_default('prefsfile', 'hellolog.prefs')
  parser.set_default('instance', 'HelloLogConfig')
  parser.set_default('htmldir', "html")
  options, args = parser.parse_args()
  server = parser.getserver(options)
  simplewebserver.run(server, options)


# -*- coding: utf-8 -*-
"""this is a demonstration of an NT service using the Hello World demo"""

from jToolkit.web import ntservice
from jToolkit.demo import helloworld
import sys
import os

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

class HelloWorldService(ntservice.WebServerService):
  """The service that runs the server that Jack^Wserves the Hello World Pages"""
  _svc_name_ = "HelloWorldWebServer"
  _svc_display_name_ = "Hello World"

  def SetDefaultsOnParser(self, parser):
    ntservice.WebServerService.SetDefaultsOnParser(self, parser)
    if "__file__" not in dir():
      __file__ = sys.executable
      servicedir = os.path.dirname(os.path.abspath(helloworld.__file__))
    else:
      servicedir = os.path.dirname(os.path.abspath(__file__))
    parser.set_default('prefsfile', os.path.join(servicedir, 'helloworld.prefs'))
    parser.set_default('instance', 'HelloWorldConfig')
    parser.set_default('htmldir', os.path.join(servicedir, "html"))

if __name__ == '__main__':
  ntservice.HandleCommandLine(HelloWorldService)


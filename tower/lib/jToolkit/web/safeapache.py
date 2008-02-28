#!/usr/bin/python
# -*- coding: utf-8 -*-

"""import mod_python apache modules safely
if they are imported from the command-line environment, errors will be trapped
this allows testing of python scripts from outside apache
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

from jToolkit import errors

class FakeConnection:
  user = 'testuser'

class FakeRequest:
  connection = FakeConnection()
  content_type = 'not externally set'
  def send_http_header(self):
    print 'send_http_header():'
    print self.content_type
  def write(self,towrite):
    print 'write():'
    print towrite

class FakeUtil:
  fakestorage = {}
  def FieldStorage(self,req):
    return self.fakestorage

class FakeApache:
  OK = "FakeApache returned OK"
  APLOG_ERR = 0
  APLOG_DEBUG = 1
  def log_error(*args):
    pass

class Fake_Apache:
  def _global_lock(self, server, something, ID):
    print "Fake_Apache just pretended to lock something"
  def _global_unlock(self, server, something, ID):
    print "Fake_Apache just pretended to unlock something"

# fakereq is useful for testing in Python interpreter
fakereq = FakeRequest()

try:
  from mod_python import apache
except:
  apache = FakeApache()

try:
  import _apache
except:
  _apache = Fake_Apache()

try:
  from mod_python import util   # for FieldStorage class
except:
  util = FakeUtil()

######################
# Area to work around the crippled sys module in Apache
######################

realapache = not isinstance(_apache, Fake_Apache)

import sys

class ApacheErrorHandler(errors.ErrorHandler):
  """a class that handles error logging etc"""
  def __init__(self, instance, webserver):
    errors.ErrorHandler.__init__(self, instance)
    self.webserver = webserver

  def logerror(self, msg):
    if isinstance(msg, unicode):
      msg = msg.encode("UTF-8")
    if self.webserver is None:
      apache.log_error(msg, apache.APLOG_ERR)
    else:
      apache.log_error(msg, apache.APLOG_ERR, self.webserver.server)
    errors.ErrorHandler.logerror(self, msg)

  def logtrace(self, msg):
    if isinstance(msg, unicode):
      msg = msg.encode("UTF-8")
    if self.webserver is None:
      apache.log_error(msg, apache.APLOG_INFO)
    else:
      apache.log_error(msg, apache.APLOG_INFO, self.webserver.server)
    errors.ErrorHandler.logtrace(self, msg)



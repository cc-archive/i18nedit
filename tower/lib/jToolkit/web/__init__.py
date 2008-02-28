# -*- coding: utf-8 -*-
"""jToolkit.web package index and master handler function for mod_python"""

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

import sys
import os
from jToolkit.web import httpcodes
from jToolkit.web import server
from jToolkit import prefs
try:
  import rptcrash
except Exception, e:
  rptcrash = None
server.rptcrash = rptcrash

# the global list of application servers, used to remember the server based on the fullinstancename
# one server per instance defined in the configuration
servers = {}

logtimes = 0

def logtimetofile(message):
  import thread, time
  osid = os.getpid()
  threadid = thread.get_ident()
  t = time.time()
  ms = int((t - int(t))*1000.0)
  timestr = time.strftime('%Y-%m-%d %H:%M:%S') + '.%03d' % ms
  f = open(logfilename, 'a')
  f.write('%s: pid %r tid %r: %s\n' % (timestr, osid, threadid, message))
  f.close()

def logtimetonowhere(message):
  """don't log anything as we aren't in logtimes mode"""
  pass

if os.path.isdir('/tmp'):
  logfilename = '/tmp/trace.log'
elif os.path.isdir('c:\\temp'):
  logfilename = 'c:\\temp\\trace.log'
else:
  logfilename = 'trace.log'

if logtimes:
  import time
  try:
    import thread
  except ImportError:
    # pretend we have threads if we don't
    def thread_get_ident():
      return 0
    class blank: pass
    thread = blank()
    thread.get_ident = thread_get_ident
  logtime = logtimetofile
else:
  logtime = logtimetonowhere

def mapmodulename(modulename):
  """maps the modulename to a different name (for customizing the import system by overriding this function)"""
  return modulename

class ApacheLock:
  def __init__(self,server,apachemodule):
    self.server = server
    self.apachemodule = apachemodule
    self.locked = False

  def lock(self): 
    self.apachemodule._apache._global_lock(self.server,None,0)
    self.locked = True

  def unlock(self):
    if self.locked:
      self.apachemodule._apache._global_unlock(self.server,None,0)
      self.locked = False

  def isLocked(self):
    return self.locked

class ApacheWebServer:
  def __init__(self, server):
    """Initializes the wrapper for the mod_python server object"""
    from jToolkit.web import safeapache
    self.apachemodule = safeapache
    self.server = server
    self.DECLINED = self.apachemodule.apache.DECLINED
    self.OK = self.apachemodule.apache.OK
    import socket
    self.errorclass = socket.error

  def createlock(self):
    """creates a new server-wide lock object"""
    return ApacheLock(self.server, self.apachemodule)

  def createerrorhandler(self, instance):
    """creates a new errorhandler using the given instance"""
    return self.apachemodule.ApacheErrorHandler(instance, self)

  def parseargs(self, req):
    """produces an argument dictionary from the request"""
    return self.apachemodule.util.FieldStorage(req)

def getserver(modulename, instancename, webserver):
  """returns a server based on a given instance in a given module"""
  fullinstancename = modulename + "." + instancename
  if fullinstancename in servers:
    server = servers[fullinstancename]
  else:
    modulename = mapmodulename(modulename)
    # this is equivalent to: from modulename import instancename
    try:
      module = __import__(modulename, globals(), locals(), [instancename])
    except ImportError, importmessage:
      errormessage = "Error importing module %r: %s\nPython path is %r" \
                     % (modulename, importmessage, sys.path)
      raise ImportError(errormessage)
    # get the actual instance
    try:
      instance = getattr(module, instancename)
    except AttributeError:
      errormessage = "module %r has no attribute %r\nmodule is %r, attributes are %r\nPython path is %r" \
                     % (modulename, instancename, module, dir(module), sys.path)
      raise AttributeError(errormessage)
    # change directory
    instancedir = getattr(instance, "instancedir", None)
    if instancedir is None:
      instancedir = os.path.dirname(module.__file__)
    os.chdir(instancedir)
    # construct a server of the appropriate class using the instance
    server = instance.serverclass(instance, webserver)
    server.name = fullinstancename
    servers[fullinstancename] = server
  return server

def getserverwithprefs(prefsfile, instancename, webserver):
  """returns a server based on a given instance in a given module"""
  fullinstancename = os.path.join(os.path.abspath(prefsfile), instancename)
  if fullinstancename in servers:
    return servers[fullinstancename]
  serverprefs = prefs.PrefsParser()
  try:
    serverprefs.parsefile(prefsfile)
  except IOError:
    errormessage = "Error using prefs file %r:\nNo such file" % (prefsfile,)
    raise IOError(errormessage)

  # find the instance prefs
  try:
    instance = serverprefs
    if instancename:
      for part in instancename.split("."):
        instance = getattr(instance, part)
  except AttributeError:
    errormessage = "Prefs file %r has no attribute %r\nprefs file is %r, attributes are %r" \
                   % (prefsfile, instancename, serverprefs, [top[0] for top in serverprefs.iteritems()])
    raise AttributeError(errormessage)
  # change directory
  instancedir = getattr(instance, "instancedir", None)
  if instancedir is None:
    instancedir = os.path.dirname(os.path.abspath(prefsfile))
  os.chdir(instancedir)
  # import any required modules
  serverprefs.resolveimportmodules(mapmodulename)
  # stepwise resolution for serverclass
  serverclass = instance.serverclass
  # if its a string it obviously should be resolved via import modules...
  if isinstance(serverclass, basestring):
    serverclassresolve = serverprefs.importmodules
    for part in serverclass.split("."):
      serverclassresolve = getattr(serverclassresolve, part)
    serverclass = serverclassresolve
  if hasattr(serverclass, "resolve"):
    serverclass = serverclass.resolve()
  if hasattr(serverclass, "template"):
    template = getattr(serverclass, "template")
    if hasattr(template, "resolve"):
      template = template.resolve()
    templateargs = {}
    for key, value in getattr(serverclass, "templateargs", {}).iteritems():
      if hasattr(value, "resolve"):
        value = value.resolve()
      templateargs[key] = value
    serverclass = template(**templateargs)
  server = serverclass(instance, webserver)
  server.name = instancename
  server.webserver = webserver
  servers[fullinstancename] = server
  return server

# handler is in here so that we can say PythonHandler jToolkit.web
# (modpython automatically looks for handler in that module)
def handler(req):
  """the standard handler which locates the instance, creates the server if neccessary, and hands off to it"""
  logtime('handler start: ' + req.uri)
  apache_options = req.get_options()
  webserver = ApacheWebServer(req.server)
  instancename = apache_options['jToolkit.instance'].strip()
  if apache_options.has_key('jToolkit.prefs'):
    prefsfile = apache_options['jToolkit.prefs']
    server = getserverwithprefs(prefsfile, instancename, webserver)
  elif apache_options.has_key('jToolkit.module'):
    modulename = apache_options['jToolkit.module']
    server = getserver(modulename, instancename, webserver)
  else:
    raise ValueError("You need to specify either jToolkit.module or jToolkit.prefs in the apache configuration")
  pathwords = filter(None, req.uri.split('/'))  # split into bits, strip out empty strings
  argdict = webserver.parseargs(req)
  logtime('calling server.handle: ' + req.uri)
  if server.logrecord:
    server.logrecord.logrequest(req)
  thepage = server.handle(req, pathwords, argdict)
  logtime('calling server.sendpage: ' + req.uri)
  result = server.sendpage(req, thepage)
  logtime('done: ' + req.uri)
  if result is None: return webserver.DECLINED
  if result == httpcodes.OK: return webserver.OK
  return result


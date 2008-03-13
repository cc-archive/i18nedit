#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""a simple web server so you don't have to run your app from inside Apache etc.
mostly useful for testing / small setups"""

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

import BaseHTTPServer
import SocketServer
import threading
import socket
import urllib
import posixpath
import cgi
import sys
import os
import time
import mimetypes
from cStringIO import StringIO
from jToolkit import glock

try:
  import win32api, win32process, win32con
except:
  class EmptyObject:
    pass
  def EmptyFunction(*args):
    print "Error: win32 function called - the Python win32 libraries were not available"
  win32con = EmptyObject()
  win32api = EmptyObject()
  win32process = EmptyObject()
  win32con.PROCESS_QUERY_INFORMATION = 0
  win32con.STILL_ACTIVE=0
  win32api.OpenProcess = EmptyFunction
  win32process.GetExitCodeProcess = EmptyFunction
  
from jToolkit.web import getserver, getserverwithprefs
from jToolkit.web import httpcodes
from jToolkit.widgets import widgets
from jToolkit import errors

class HeadersList(list):
  """simple list of headers that defines a method to add a name and value"""
  def add(self, name, value):
    self.append((name, value))

class jToolkitHTTPRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
  """Handles an HTTP Request, using a jToolkit server"""
  protocol_version = "HTTP/1.0"
  def __init__(self, request, client_address, server):
    """construct the request, making sure the appropriate attributes are available"""
    request.setblocking(1)
    self.options = server.options
    # we need to be able to keep track of outgoing headers to send cookies...
    self.headers_out = HeadersList()
    BaseHTTPServer.BaseHTTPRequestHandler.__init__(self, request, client_address, server)

  # stuff based on BaseHTTPServer
  server_version = 'jToolkitHTTP/0.1'

  def address_string(self):
    """Return the client address formatted for logging.
    Only try and resolve if options has hostnamelookups set on"""
    if self.options.hostnamelookups:
      return BaseHTTPServer.BaseHTTPRequestHandler.address_string(self)
    else:
      return self.client_address[0]

  def log_message(self, format, *args):
    """Log an arbitrary message.
    This is used by all other logging functions.  Override
    it if you have specific logging wishes.
    The first argument, FORMAT, is a format string for the
    message to be logged.  If the format string contains
    any % escapes requiring parameters, they should be
    specified as subsequent arguments (it's just like
    printf!).
    The client host and current date/time are prefixed to
    every message.
    """
    if not hasattr(self,'authuser'):
      self.authuser = None
    if self.authuser is None:
      self.authuser = getattr(getattr(self, 'session', None), 'username', None)
    if self.authuser is None:
      self.authuser = '-'
    if isinstance(self.authuser, unicode):
      self.authuser = self.authuser.encode("utf-8")
    self.server.errorhandler.logtrace("%s - %s [%s] %s\n" %
                     (self.address_string(),
                      self.authuser,
                      self.log_date_time_string(),
                      format%args))

  def build_argdict(self, argdict):
    """build a real dictionary out of the argdict, ignoring empty keys"""
    newdict = {}
    for key in argdict:
      value = argdict[key]
      if isinstance(value, cgi.FieldStorage):
        if value.filename is None:
          value = value.value
        else:
          newdict[key] = value
          continue
      newdict[key] = value
    return newdict

  def process_get_args(self):
    """process GET-style args in the URL"""
    querypos = self.path.find('?')
    if querypos != -1:
      path = self.path[:querypos]
      querystring = self.path[querypos+1:]
      argdict = cgi.parse_qs(querystring, 1, 0)
      return path, self.build_argdict(argdict)
    else:
      return self.path, {}

  def process_post_args(self):
    """process POST-style args in the content body"""
    path, getargs = self.process_get_args()
    contenttype = self.headers.gettype()
    if contenttype <> 'application/x-www-form-urlencoded' and contenttype <> 'multipart/form-data':
      # check this
      self.send_response(httpcodes.NOT_IMPLEMENTED)
      self.end_headers()
      return
    contentlength = int(self.headers.getheader('Content-Length'))
    querystring = self.rfile.read(contentlength)
    if contenttype == 'application/x-www-form-urlencoded':
      postargs = cgi.parse_qs(querystring, 1, 0)
    else:
      typeOptions = {'content-type':self.headers.getheader('Content-Type')}
      postargs = cgi.FieldStorage(fp=StringIO(querystring), headers=typeOptions, environ={"REQUEST_METHOD":"POST"})
    postargs = self.build_argdict(postargs)
    getargs.update(postargs)
    return path, getargs

  def register_cleanup(self, cleanup, data=None):
    """registers a cleanup for a request"""
    self.cleanup = cleanup
    if data is not None:
      self.cleanup_data = data

  def serve_request(self, path, argdict):
    """Serve a GET or POST request"""
    self.headers_in = self.headers
    self.authuser = None
    path = posixpath.normpath(urllib.unquote(path))
    pathwords = filter(None, path.split('/'))  # split into bits, strip out empty strings
    if len(pathwords) > 0 and pathwords[-1] == '.':
      pathwords = pathwords[:-1]
    self.pathwords = pathwords
    try:
      thepage = self.server.handle(self, self.pathwords, argdict)
    except Exception, e:
      self.content_type = "text/plain"
      self.send_http_header(httpcodes.INTERNAL_SERVER_ERROR)
      errorhandler = self.server.errorhandler
      exceptionstr = errorhandler.exception_str()
      errormessage = str(e)
      traceback = errorhandler.traceback_str()
      if self.options.browsererrors == 'traceback':
        self.wfile.write(traceback)
      elif self.options.browsererrors == 'exception':
        self.wfile.write(exceptionstr)
      elif self.options.browsererrors == 'message':
        self.wfile.write(errormessage)
      if self.options.logerrors == 'traceback':
        errorhandler.logerror(traceback)
      elif self.options.logerrors == 'exception':
        errorhandler.logerror(exceptionstr)
      elif self.options.logerrors == 'message':
        errorhandler.logerror(errormessage)
      return
    self.sendpage(thepage)
    if hasattr(self, "cleanup"):
      if hasattr(self, "cleanup_data"):
        self.cleanup(self.cleanup_data)
      else:
        self.cleanup()

  def send_http_header(self, response=httpcodes.OK):
    """ala the apache method"""
    self.send_response(response)
    if hasattr(self, "content_type"):
      self.send_header("Content-type", self.content_type)
    for name, value in self.headers_out:
      self.send_header(name, value)
    self.end_headers()

  def sendfile(self, filename):
    """sends the contents of a file in response"""
    if self.content_type.startswith("text/"):
      mode = 'r'
    else:
      mode = 'rb'
    contents = open(filename, mode).read()
    self.wfile.write(contents)

  def sendpage(self, thepage):
    """sends the page back to the user"""
    self.write = self.wfile.write
    response = self.server.sendpage(self, thepage)
    if response is None:
      # this is equivalent to letting Apache handle it...
      if self.command == 'GET' and self.options.htmldir is not None:
        filepath = os.path.join(self.options.htmldir, *self.pathwords)
        if os.path.isfile(filepath):
          self.content_type, encoding = mimetypes.guess_type(filepath)
          if self.content_type is None:
            self.content_type = 'application/octet-stream'
          self.send_http_header()
          self.sendfile(filepath)
          return
      self.send_http_header(httpcodes.NOT_FOUND)
    elif response != httpcodes.OK:
      self.send_http_header(response)

  def do_GET(self):
    """Serve a GET request"""
    path, argdict = self.process_get_args()
    self.serve_request(path, argdict)

  def do_POST(self):
    """Serve a POST request"""
    path, argdict = self.process_post_args()
    self.serve_request(path, argdict)
    # TODO: find out why this makes IE work :-)
    # on Windows XP machines, with IE 6 (but not Firefox), POST requests sometimes give a "Page could not be loaded"
    # even though the request has been received and returned by simplewebserver!
    # doesn't happen on Apache, and a sleep here seems to fix it
    # time.sleep(0.1)

BaseErrorHandler = errors.ErrorHandler
consoleerrorhandler = errors.ConsoleErrorHandler()
class TeeConsoleErrorHandler(errors.TeeErrorHandler):
  def __init__(self, instance):
    """constructs a normal error handler but also redirects it to the console"""
    if hasattr(instance, 'errorfile') or hasattr(instance, 'tracefile'):
      errorhandler = BaseErrorHandler(instance)
      self.instance = errorhandler.instance
      errors.TeeErrorHandler.__init__(self, errorhandler, consoleerrorhandler)
    else:
      errors.TeeErrorHandler.__init__(self, consoleerrorhandler)
      self.instance = instance

class AltThreadingMixIn:
    """Mix-in class to handle each request in a new thread. the Thread class is programmable."""

    # Decides how threads will act upon termination of the
    # main process
    daemon_threads = False
    import threading
    ThreadClass = threading.Thread
    SafeThreadClass = threading.Thread
    def test_service(self):
        if hasattr(self, "runningasservice"):
            return self.runningasservice
        try:
            import servicemanager
        except ImportError:
            self.runningasservice = False
            return self.runningasservice
        self.runningasservice = servicemanager.RunningAsService()
        return self.runningasservice

    try:
        import PyLucene
        # FIXME: bug 742: this fails with PyLucene.PythonThread inside a service
        ThreadClass = PyLucene.PythonThread
    except ImportError:
        pass

    def process_request_thread(self, request, client_address):
        """Same as in BaseServer but as a thread.

        In addition, exception handling is done here.

        """
        try:
            self.finish_request(request, client_address)
            self.close_request(request)
        except:
            self.handle_error(request, client_address)
            self.close_request(request)

    def process_request(self, request, client_address):
        """Start a new thread to process the request."""
        if self.test_service():
            ThreadClass = self.SafeThreadClass
        else:
            ThreadClass = self.ThreadClass
        t = ThreadClass(target = self.process_request_thread,
                             args = (request, client_address))
        if self.daemon_threads:
            t.setDaemon (1)
        t.start()

class ThreadedHTTPServer(AltThreadingMixIn, BaseHTTPServer.HTTPServer):
  pass

class ForkedHTTPServer(SocketServer.ForkingMixIn, BaseHTTPServer.HTTPServer):
  pass

class ThreadLockWrap:
  def __init__(self):
    self._lock = threading.Lock()
    self.locked = False

  def lock(self):
    self._lock.acquire()
    self.locked = True

  def unlock(self):
    if self.locked:
      self._lock.release()
      self.locked = False

  def isLocked(self):
    return self.locked

class DummyServer:
  def createlock(self):
    """returns a server-wide lock object"""
    return ThreadLockWrap()

  def createerrorhandler(self, instance):
    """creates a new errorhandler using the given instance"""
    return TeeConsoleErrorHandler(instance)

def jToolkitHTTPServer(baseserver):
 class jToolkitHTTPServer(baseserver):
  def __init__(self, options, startuperrorhandler):
    self.options = options
    self.errorclass = socket.error
    self.startuperrorhandler = startuperrorhandler
    server_address = ('', self.options.port)
    baseserver.__init__(self, server_address, jToolkitHTTPRequestHandler)
    if self.options.watchpid != -1:
      self.parentprocess = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION, False, int(self.options.watchpid))
    else:
      self.parentprocess = False
    self.maxrequests = self.options.maxrequests
    self.requestcount = 0
    # if this is set to True then in handle_error, errors will be raised instead of caught
    self.raise_errors = False

  def server_bind(self):
    """Called by constructor to bind the socket."""
    # The only reason for the timeout is so we can notice keyboard
    # interrupts on Win32, which don't interrupt accept() by default
    self.socket.settimeout(0.2)
    if self.options.runninglock:
      self.startuperrorhandler.logtrace("waiting for running lock...")
      self.runninglock = glock.GlobalLock(self.options.runninglock, True)
      self.startuperrorhandler.logtrace("got running lock...")
    else:
      self.runninglock = None
    if self.options.socketlock:
      self.startuperrorhandler.logtrace("waiting for socket lock...")
      self.socketlock = glock.GlobalLock(self.options.socketlock, True)
      self.startuperrorhandler.logtrace("got socket lock...")
    else:
      self.socketlock = None
    try:
      baseserver.server_bind(self)
    except socket.error, e:
      self.startuperrorhandler.logtrace("error binding socket: %s" % e)
      self.startuperrorhandler.logtrace("waiting one second for socket to clear, then trying again")
      time.sleep(1)
      baseserver.server_bind(self)

  def server_activate(self):
    """Called by constructor to activate the server."""
    baseserver.server_activate(self)
    self.hostaddr, self.port = self.socket.getsockname()
    try:
      self.hostname = socket.gethostbyaddr(self.hostaddr)[0]
    except:
      self.hostname = self.hostaddr
    # 0.0.0.0 is a fake address that people can't use...
    if self.hostname == "0.0.0.0":
      self.hostname = "127.0.0.1"
    self.startuperrorhandler.logtrace("Listening on port %d" % self.port)
    if self.port == 80:
      starturl = "http://%s/" % self.hostname
    else:
      starturl = "http://%s:%d/" % (self.hostname, self.port)
    if self.options.startbrowser:
      import webbrowser
      self.startuperrorhandler.logtrace("Opening web browser at %s" % starturl)
      webbrowser.open(starturl, new=1, autoraise=1)
    else:
      self.startuperrorhandler.logtrace("To use the server, open a web browser at %s" % starturl)

  def getstop(self):
    return self._stop
  def setstop(self, newval):
    if newval == False and getattr(self, "_stop", None) == True:
      return
    self._stop = newval
  stop = property(getstop, setstop)

  def handle_request(self):
    """Override handle_request to trap timeout exception."""
    try:
      baseserver.handle_request(self)
    except KeyboardInterrupt:
      self.startuperrorhandler.logtrace("<Ctrl-C> hit: shutting down")
      sys.exit(0)

  def handle_error(self, request, client_address):
    """Handle errors by outputting to error log rather than stdout"""
    exception = self.startuperrorhandler.exception_str()
    traceback = self.startuperrorhandler.traceback_str()
    self.startuperrorhandler.logerror("Error handling request from %s: %s" % (client_address, exception))
    self.startuperrorhandler.logerror("Traceback follows:\n%s" % traceback)
    if self.raise_errors:
      raise

  def sendpage(self, req, thepage):
    return self.jtoolkitserver.sendpage(req, thepage)

  def handle(self, req, pathwords, argdict):
    self.requestcount += 1
    return self.jtoolkitserver.handle(req, pathwords, argdict)

  def createlock(self):
    """returns a server-wide lock object"""
    return ThreadLockWrap()

  def createerrorhandler(self, instance):
    """creates a new errorhandler using the given instance"""
    return errors.TeeErrorHandler(self.startuperrorhandler, errors.ErrorHandler(instance))

  def run(self, server):
    self.jtoolkitserver = server
    self.errorhandler = self.jtoolkitserver.errorhandler
    if self.options.trace:
      def tracefunc(frame, event, arg):
        if frame.f_code.co_name != "?":
          space = ""
        below = frame.f_back
        while below:
          below = below.f_back
          space += " "
        code = frame.f_code
        logstring = "%s%s %s:%d, %r, %s\n" % (space, code.co_filename, code.co_name, frame.f_lineno, event, arg)
        open("pytrace.log", "a").write(logstring)
        return tracefunc
      sys.settrace(tracefunc)
    # this means the server has to be interrupted manually...
    if self.options.debug:
      import pdb
      pdb.runcall(self.serve_forever)
    else:
      self.serve_forever()

  def serve_forever(self):
    self.setstop(False)
    # handoverlock is the runninglock of the next expected running process...
    handoverlock = None
    while not self.getstop():
      if handoverlock:
        # wait for the next process to acquire its runninglock (our handoverlock) before releasing the socket
        # TODO: replace this. if the next process finishes before this activates, it will carry on for ever
        if handoverlock.tryacquire():
          handoverlock.release()
        else:
          self.errorhandler.logtrace("other process has handoverlock, closing socket and exiting")
          self.socket.close()
          self.socketlock.release()
          return
      self.handle_request()
      if self.parentprocess:
        termination = win32process.GetExitCodeProcess(self.parentprocess)
        if termination != win32con.STILL_ACTIVE:
          self.setstop(True)
      if self.maxrequests:
        if self.requestcount >= self.maxrequests:
          # exit with an error code so that autorestart can restart us if required
          if self.runninglock:
            self.errorhandler.logtrace("received %d requests, releasing running lock" % self.requestcount)
            self.runninglock.release()
            runninglockname, parentpid, processcount = self.runninglock.name.split("-")
            processcount = int(processcount) + 1
            handoverlock = glock.GlobalLock("%s-%s-%d" % (runninglockname, parentpid, processcount))
          else:
            self.errorhandler.logtrace("received %d requests, exiting")
            sys.exit(1)
          self.maxrequests = None

 return jToolkitHTTPServer

servertypes = [("standard", BaseHTTPServer.HTTPServer), ("threaded", ThreadedHTTPServer), ("forked", ForkedHTTPServer), ("dummy", None)]

def logpid(pidfile, pid):
  f = open(pidfile,'w')
  f.write('%d' % pid)
  f.close()

import optparse
class WebOptionParser(optparse.OptionParser):
  def __init__(self, errorhandler=None, version=None):
    optparse.OptionParser.__init__(self, version=version)
    if errorhandler is None:
      self.errorhandler = consoleerrorhandler
    else:
      self.errorhandler = errorhandler
    self.add_option("-B", None, dest="background", action="store_true", default=False, help="fork into background")
    self.add_option("-o", None, dest="output", action="store", default=None, help="write output to file")
    self.add_option("-p", "--port", dest="port", action="store", type="int", default=8080, help="set port to listen on")
    self.add_option("", "--prefsfile", dest="prefsfile", action="store", default=None, help="use prefs file")
    self.add_option("", "--configmodule", dest="configmodule", action="store", default=None, help="use config module")
    self.add_option("", "--instance", dest="instance", action="store", default="master", help="select server instance")
    self.add_option("", "--htmldir", dest="htmldir", action="store", default=None, help="serve files from html directory")
    self.add_option("", "--hostnamelookups", dest="hostnamelookups", action="store_true", default=False, help="Resolve client IP addresses")
    self.add_option("", "--pidfile", dest="pidfile", action="store", default=None, help="store the server process id here")
    self.add_option("", "--debug", dest="debug", action="store_true", default=False, help="run under the python debugger")
    self.add_option("", "--trace", dest="trace", action="store_true", default=False, help="output verbose tracing")
    servertypenames = [servertypename for servertypename, webserverclass in servertypes]
    self.add_option("", "--servertype", dest="servertype", type="choice", choices=servertypenames, default="standard", help="server process model: " + ", ".join(servertypenames))
    errorleveltypes = ["none", "message", "exception", "traceback"]
    self.add_option("", "--browsererrors", dest="browsererrors", default="exception", choices = errorleveltypes,
      metavar="ERRORLEVEL", help="level of errors to send to browser: %s" % (", ".join(errorleveltypes)))
    self.add_option("", "--logerrors", dest="logerrors", default="traceback", choices = errorleveltypes,
      metavar="ERRORLEVEL", help="level of errors to send to log: %s" % (", ".join(errorleveltypes)))
    self.add_option("", "--autorestart", dest="autorestart", action="store_true", default=False, help="automatically restart if the server dies unexpectedly")
    self.add_option("", "--socketlock", dest="socketlock", action="store", default=None, help="use the given lock file / mutex to control binding the socket [used internally]")
    self.add_option("", "--runninglock", dest="runninglock", action="store", default=None, help="use the given lock file / mutex to control running child processes [used internally]")
    self.add_option('', '--maxrequests', dest='maxrequests', action="store", default=None, type="int", help="Only serve a limited number of requests")
    self.add_option("", "--startbrowser", dest="startbrowser", action="store_true", default=False, help="start a web browser when the server is ready")
    self.add_option('', '--watchpid', dest='watchpid', action="store", default=-1, help="Run the webserver as dependent on another process")

  def getserver(self, options):
    if options.background:
      # fork into background
      childpid = os.fork()
      if childpid:
        if options.pidfile:
          logpid(options.pidfile, childpid)
        # exit the parent
        sys.exit()
    else:
      if options.pidfile:
        logpid(options.pidfile, os.getpid())
    if options.autorestart:
      finished = False
      argv = ['"' + sys.executable + '"'] + [arg for arg in sys.argv if arg != "--autorestart"]
      pid = os.getpid()
      socketlock = glock.GlobalLock("socket-%d" % pid)
      processcount = 0
      while not finished:
        processcount += 1
        runninglock = glock.GlobalLock("running-%d-%d" % (pid, processcount))
        thisargv = argv[:]
        thisargv += ["--socketlock=%s" % socketlock.name]
        thisargv += ["--runninglock=%s" % runninglock.name]
        childpid = os.spawnv(os.P_NOWAIT, sys.executable, thisargv)
        running = False
        while not running:
          if runninglock.tryacquire():
            runninglock.release()
            time.sleep(0.1)
          else:
            running = True
        while running:
          try:
            # wait for running lock to be released...
            runninglock.acquire()
            runninglock.release()
            # childpid, result = os.waitpid(childpid, 0)
            result = 1
          except KeyboardInterrupt:
            result = 0
          running = False
        finished = (result == 0) or (result == 2)
        if result == 1:
          self.errorhandler.logtrace("child released running lock, restarting")
        elif not finished:
          self.errorhandler.logtrace("child server %d finished unexpectedly (return code %d) ; restarting (Ctrl-C will quit)" % (pid, result))
      sys.exit()
    if options.output is not None:
      sys.stdout = open(options.output,'a')
      sys.stderr = sys.stdout
    if options.servertype == "dummy":
      httpd = DummyServer()
    else:
      baseserver = dict(servertypes)[options.servertype]
      webserverclass = jToolkitHTTPServer(baseserver)
      httpd = webserverclass(options, self.errorhandler)
    try:
      if options.prefsfile is not None:
        server = getserverwithprefs(options.prefsfile, options.instance, httpd)
      elif options.configmodule is not None:
        server = getserver(options.configmodule, options.instance, httpd)
      else:
        self.error("must specify one of prefsfile or configmodule")
    except Exception, e:
      if options.logerrors == 'traceback':
        traceback = self.errorhandler.traceback_str()
        self.errorhandler.logerror(traceback)
      elif options.logerrors == 'exception':
        exceptionstr = self.errorhandler.exception_str()
        self.errorhandler.logerror(exceptionstr)
      elif options.logerrors == 'message':
        errormessage = str(e)
        self.errorhandler.logerror(errormessage)
      self.errorhandler.logtrace("Error initializing server, exiting: %s" % e)
      time.sleep(2)
      sys.exit(2)
    return server

def run(server, options):
  server.webserver.run(server)

if __name__ == '__main__':
  # run the web server
  parser = WebOptionParser()
  options, args = parser.parse_args()
  server = parser.getserver(options)
  run(server, options)


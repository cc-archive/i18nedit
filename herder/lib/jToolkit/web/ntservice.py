#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""A class for handling a simplewebserver instance as a service"""

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

import win32serviceutil, win32service
import win32evtlogutil, win32evtlog
from win32event import *
import pywintypes, winerror, win32api
import _winreg
import sys, os
import imp

from jToolkit.web import simplewebserver
from jToolkit import errors

status_messages = {
    win32service.SERVICE_STOPPED: "Stopped",
    win32service.SERVICE_STOP_PENDING: "Stopping",
    win32service.SERVICE_RUNNING: "Running",
    win32service.SERVICE_PAUSED: "Paused",
    win32service.SERVICE_START_PENDING: "Starting",
}

# We can't have a consoleerrorhandler in a service, so we change it for something that will log Events in the EventLog
class ServiceErrorHandler(errors.ConsoleErrorHandler):
  def __init__(self, errorsource="jToolkitWebServer"):
    self.errorfile = win32evtlog.EVENTLOG_ERROR_TYPE
    self.tracefile = win32evtlog.EVENTLOG_INFORMATION_TYPE
    self.auditfile = None
    self.instance = self
    self.errorsource = errorsource
    self.registersource()
  def registersource(self):
    # this tells it to use the win32evtlog.pyd library for reading error strings - string 1 is %s, so lets us store straight log messages
    win32evtlogutil.AddSourceToRegistry(self.errorsource, win32evtlog.__file__)
  def writelog(self, f, message):
    win32evtlogutil.ReportEvent(self.errorsource, 1, 0, f, [message], None, None)

class WebServerService(win32serviceutil.ServiceFramework):
  """The service that runs the server that Jack^Wserves the Hello World Pages"""
  # These two should be changed for each subclass
  _svc_name_ = "jToolkitWebServer"
  _svc_display_name_ = "jToolkit Web Server"
  def __init__(self, args):
    win32serviceutil.ServiceFramework.__init__(self, args)
    self.errorhandler = ServiceErrorHandler(self._svc_name_)
    self.webserver = None
    self.allowstart = True

  def SvcStop(self):
    self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
    if self.webserver is None:
      self.allowstart = False
      self.errorhandler.logerror("Stop before start, will not startup")
    else:
      self.webserver.setstop(True)

  def SvcDoRun(self):
    self.ReportServiceStatus(win32service.SERVICE_START_PENDING)
    parser = self.__class__.GetParserClass()(self.errorhandler)
    self.SetDefaultsOnParser(parser)
    cmdargs = self.GetCommandArgs()
    options, args = parser.parse_args(args=cmdargs)
    self.server = parser.getserver(options)
    self.webserver = self.server.webserver
    if self.allowstart:
      self.ReportServiceStatus(win32service.SERVICE_RUNNING)
      simplewebserver.run(self.server, options)
    else:
      self.errorhandler.logtrace("Stopping before startup")
    self.errorhandler.logtrace("Shutting down")

  def GetParserClass(cls):
    # Allow override of the parser we use
    # static, so we can get a parser without initialising the class
    return simplewebserver.WebOptionParser
  GetParserClass = classmethod(GetParserClass)

  def SetDefaultsOnParser(self, parser):
    """Override to set parser defaults for specific services"""
    pass

  def GetCommandArgs(self):
    # We pull default values from HKLM\SYSTEM\CurrentControlSet\Services\_svc_name_\Parameters
    try:
      OptionsKey = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, "SYSTEM\\CurrentControlSet\\Services\\%s" % self._svc_name_)
    except:
      # This probably means the key doesn't exist, in which case we add no default values
      return

    try:
      (value, valueType) = _winreg.QueryValueEx(OptionsKey, "Parameters")
    except EnvironmentError:
      return []
     
    _winreg.CloseKey(OptionsKey)
    args = value
    self.errorhandler.logtrace("service arguments: %s" % str(args))
    return args

import optparse
def CreateServiceOptionParser(parserclass):
  class ServiceOptionParser(parserclass):
    def __init__(self, errorhandler=None):
      parserclass.__init__(self, errorhandler)
      serviceoptions = optparse.OptionGroup(self, "Service options", "These options are used for controlling the service")
      serviceoptions.add_option("", "--serviceinstall", dest="install", action="store_true", default=False, help="Install the service")
      serviceoptions.add_option("", "--serviceremove", dest="remove", action="store_true", default=False, help="Remove the service")
      serviceoptions.add_option("", "--servicestart", dest="start", action="store_true", default=False, help="Start the service")
      serviceoptions.add_option("", "--servicerestart", dest="restart", action="store_true", default=False, help="Restart the service")
      serviceoptions.add_option("", "--servicestop", dest="stop", action="store_true", default=False, help="Stop the service")
      serviceoptions.add_option("", "--servicestatus", dest="status", action="store_true", default=False, help="Show the service status")
      serviceoptions.add_option("", "--servicedebug", dest="debug", action="store_true", default=False, help="Run service commands in debug mode")
      serviceoptions.add_option("", "--serviceuser", dest="user", action="store", default=None, help="Specify the user with which to run the service")
      serviceoptions.add_option("", "--servicepassword", dest="password", action="store", default=None, help="Specify the password to use to run the service")
      startuptypes = ["manual","auto","disabled"]
      serviceoptions.add_option("", "--servicestartup", dest="startup", type="choice", choices=startuptypes, default="manual", help="Specify the startup type for the service: "+ ", ".join(startuptypes))
      serviceoptions.add_option("", "--runservice", dest="runservice", action="store_true", default=False, help="Run this executable as a service (should only be run by the Services Control Manager in Windows")
      self.add_option_group(serviceoptions)
  
  return ServiceOptionParser

def RunService(service):
  import servicemanager
  # Events are sourced from the servicemanager
  evtsrc_dll = os.path.abspath(servicemanager.__file__)
  # Tell the servicemanager what our service class is
  servicemanager.Initialize(service._svc_name_, evtsrc_dll)
  servicemanager.PrepareToHostSingle(service)
  servicemanager.StartServiceCtrlDispatcher()

def check_if_frozen():
  return (hasattr(sys, "frozen") or # new py2exe
          hasattr(sys, "importers") # old py2exe
          or imp.is_frozen("__main__")) # tools/freeze   

def InstallService(service, options, script=None, nonserviceargs=None):
  # Rebuild the rest of the command-line
  if nonserviceargs is None:
    nonserviceargs = GetNonServiceArgs(sys.argv[1:])

  if options.startup == "manual":
    startType = win32service.SERVICE_DEMAND_START
  elif options.startup == "auto":
    startType = win32service.SERVICE_AUTO_START
  else:
    startType = win32service.SERVICE_DISABLED

  # Now, are we frozen or not?
  if check_if_frozen():
    # Use sys.executable as the executable name
    exeName = sys.executable + " --runservice"
  else:
      # Run using the current command-line except without
    if script is None:
      script = sys.argv[0]
    exeName = sys.executable + " " + os.path.abspath(script) + " --runservice"

  # Run the actual service install
  svc_display_name = getattr(service, "_svc_display_name_", service._svc_name_)
  svc_deps = getattr(service, "_svc_deps_", None)
  
  hscm = win32service.OpenSCManager(None,None,win32service.SC_MANAGER_ALL_ACCESS)
  try:
    hs = win32service.CreateService(hscm,
            service._svc_name_,
            svc_display_name,
            win32service.SERVICE_ALL_ACCESS,         # desired access
            win32service.SERVICE_WIN32_OWN_PROCESS,  # service type
            startType,
            win32service.SERVICE_ERROR_NORMAL,       # error control type
            exeName,
            None,
            0,
            svc_deps,
            options.user,
            options.password)
    win32service.CloseServiceHandle(hs)
  finally:
    win32service.CloseServiceHandle(hscm)
                                              
  # Write the command line to the registry
  try:
    ServiceKey = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, "SYSTEM\\CurrentControlSet\\Services\\%s" % service._svc_name_, 0, _winreg.KEY_READ | _winreg.KEY_WRITE)
  except EnvironmentError:
    print "Error attempting to store default parameters for service: Service is not installed"
    return
    
  _winreg.SetValueEx(ServiceKey, "Parameters", 0, _winreg.REG_MULTI_SZ, nonserviceargs)

def GetNonServiceArgs(args):
  """This function returns all command-line arguments not to do with services"""
  nonserviceargs = []
  usernameoption=False
  passwordoption=False
  startupoption=False
  for arg in args:
    if usernameoption and arg == options.user:    # If this is the username specified
      continue
    if passwordoption and arg == options.password:
      continue
    if startupoption and arg == options.startup:
      continue

    usernameoption = False
    passwordoption = False
    startupoption = False
    
    if arg[:9] == "--service":
      if "user" in arg:
        usernameoption = True
      if "password" in arg:
        passwordoption = True
      if "startup" in arg:
        startupoption = True
      continue
    nonserviceargs.append(arg)
  return nonserviceargs

def HandleCommandLine(service):
  # The object of this function is to wrap win32serviceutil.HandleCommandLine, 
  # so we can install command-line options for simplewebserver as well
  
  # Build a parser for the win32serviceutil stuff, for the commands install, remove, start, stop, restart and debug
  # with the extra options user, password and startup
  serviceerrorhandler = ServiceErrorHandler(service._svc_name_)
  errorhandler = errors.TeeErrorHandler(serviceerrorhandler)
  parser = CreateServiceOptionParser(service.GetParserClass())(errorhandler)
  options, args = parser.parse_args()

  if options.runservice:
    # Start this as a service
    RunService(service)
    return
  else:
    errorhandler.errorhandlers += (simplewebserver.consoleerrorhandler,)

  if options.debug:
    # FIXME: Not sure what the right thing to do here is
    return
  
  # Store the rest of the command line (only on install)
  if options.install:
    errorhandler.logtrace("Installing Service %s" % service._svc_name_)
    InstallService(service, options)
    serviceerrorhandler.registersource()
    return
  
  elif options.remove:
    errorhandler.logtrace("Removing Service %s" % service._svc_name_)
    win32serviceutil.RemoveService(service._svc_name_)
    return

  elif options.start:
    extraargs = GetNonServiceArgs(sys.argv[1:])
    errorhandler.logtrace("Starting Service %s with args %r" % (service._svc_name_, extraargs))
    win32serviceutil.StartService(service._svc_name_, extraargs)
    return
    
  elif options.restart:
    extraargs = GetNonServiceArgs(sys.argv[1:])
    errorhandler.logtrace("Restarting Service %s with args %r:" % (service._svc_name_, extraargs))
    win32serviceutil.StopService(service._svc_name_)

    servicestarted = False
    # We need to give it a few tries to restart
    for i in range(10):
      try:
        StartService(service._svc_name_, extraargs)
        servicestarted = True
        break
      except pywintypes.error, (hr, name, msg):
        if hr != winerror.ERROR_SERVICE_ALREADY_RUNNING:
          raise win32service.error, (hr, name, msg)
        win32api.Sleep(500)
    if not servicestarted:
      errorhandler.logerror("Unable to restart Service %s after %d tries" % (service._svc_name_, i))
    return
  
  elif options.stop:
    errorhandler.logtrace("Stopping Service %s" % service._svc_name_)
    win32serviceutil.StopService(service._svc_name_)
    return

  elif options.status:
    scm = win32service.OpenSCManager(None, None, win32service.SERVICE_QUERY_CONFIG)
    handle = win32service.OpenService(scm, service._svc_name_, win32service.SERVICE_ALL_ACCESS)
    status = win32service.QueryServiceStatus(handle)[1]
    status_message = status_messages.get(status, "Unknown status %d" % status)
    print "Service %s is %s" % (service._svc_name_, status_message)
    return

  else:
    parser.print_help()
    return

if __name__ == '__main__':
  HandleCommandLine(WebServerService)


#!/usr/bin/env python

import win32serviceutil
import win32service
import servicemanager
import os
from jToolkit.demo import helloworldservice
from jToolkit.web import ntservice
import urllib2
try:
	import cookielib
except ImportError:
	# fallback for python before 2.4
	cookielib = None
	import ClientCookie
import time

class ServiceManager:
	_svc_name_ = "HelloWorldWebServer"
	_svc_evt_src_ = _svc_name_
	def __init__(self):
		self.hscm = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_ALL_ACCESS)
		self._hs = None

	def __del__(self):
		if self._hs is not None:
			win32service.CloseServiceHandle(self._hs)
		win32service.CloseServiceHandle(self.hscm)

	def readhs(self):
		return win32service.OpenService(self.hscm, self._svc_name_, win32service.SERVICE_ALL_ACCESS)

	def geths(self):
		if self._hs is None:
			try:
				self._hs = self.readhs()
			except:
				pass
			return self._hs
		return self._hs
	hs = property(geths)

	def closeservice(self):
		if self._hs is not None:
			win32service.CloseServiceHandle(self._hs)
			self._hs = None

	def getstatus(self):
		hs = self.hs
		if hs is not None:
			return win32service.QueryServiceStatus(hs)[1]
		return None
	status = property(getstatus)

	def installservice(self, extraargs=[]):
		class dummyoptions:
			startup = "manual"
			user = None
			password = None
		script = os.path.abspath(helloworldservice.__file__)
		prefsfile = os.path.join(os.path.dirname(script), "helloworld.prefs")
		serviceargs = ["--prefsfile", prefsfile] + extraargs
		ntservice.InstallService(helloworldservice.HelloWorldService, dummyoptions, script, serviceargs)

	def killprocess(self, pid):
		"""Tries to kill the given process, using pskill if available, or asks user to"""
		# TODO: add more info for user. pskill is from sysinternals.com
		result = os.system("pskill %d" % pid)
		if result == 0:
			# give the operating system time to recover
			time.sleep(1)
		else:
			print "Please try and kill process %d" % pid
			raw_input("Press Enter when done... ")

	def removeservice(self, pid=None):
		"""Removes the service. The given process ID will be killed if stopping the service fails"""
		stoperror = None
		try:
			self.stopservice()
		except Exception, e:
			print "Error stopping service, will try delete anyway:", e
			if pid is not None:
				self.killprocess(pid)
				# if the kill process is successful, stopservice will succeed...
				self.stopservice()
			else:
				stoperror = e
		try:
			win32service.DeleteService(self.hs)
		except Exception, e:
			if e.args[2] != 'The specified service has been marked for deletion.':
				raise
		if stoperror:
			raise
		self.closeservice()

	def startservice(self):
		win32service.StartService(self.hs, [])
		win32serviceutil.WaitForServiceStatus(self._svc_name_, win32service.SERVICE_RUNNING, 15)

	def stopservice(self):
		hs = self.hs
		if hs is not None:
			if self.status != win32service.SERVICE_STOPPED:
				win32service.ControlService(hs, win32service.SERVICE_CONTROL_STOP)
			win32serviceutil.WaitForServiceStatus(self._svc_name_, win32service.SERVICE_STOPPED, 15)

class TestService(object):
	hostname = "localhost"
	port = 8080
	def setup_class(cls):
		cls.servicemanager = ServiceManager()

	def setup_method(self, method):
		try:
			hs = self.servicemanager.hs
			if hs is not None:
				self.servicemanager.removeservice()
		except Exception, e:
			from jToolkit import errors
			print errors.ErrorHandler(None).traceback_str()
			n = 0
			while "marked for deletion" in str(e) and n < 8:
				n += 1
				e = None
				try:
					self.servicemanager.removeservice()
				except Exception, e:
					pass
				else:
					time.sleep(0.25)
			if e is not None:
				print "attempt to wait for service deletion unsuccessful, trying to stop with net command"
				os.system("net stop %s" % self.servicemanager._svc_name_)
				if self.servicemanager.hs is not None:
					print "attempt to wait for service deletion unsuccessful"
					raise
			else:
				print "error removing service (not neccessarily serious): %s" % e
		self.setup_cookies()

		# can specify extra arguments per object or method
		dirname = os.path.abspath(os.getcwd())
		self.pidfile = os.path.join(dirname, "%s_%s.pid" % (self.__class__.__name__, method.__name__))
		if os.path.exists(self.pidfile):
			os.remove(self.pidfile)
		extraargs = ["--pidfile", self.pidfile]
		extraargs += getattr(self, "extraargs", [])
		extraargs += getattr(method, "extraargs", [])
		self.servicemanager.installservice(extraargs=extraargs)
		try:
			self.servicemanager.startservice()
		except Exception, e:
			print "Error starting service, so will remove: %s" % e
			self.servicemanager.removeservice()
			raise
		self.method_start = time.clock()
		print "starting method", method.__name__

	def setup_cookies(self):
		"""handle cookies etc"""
		if cookielib:
			self.cookiejar = cookielib.CookieJar()
			self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookiejar))
			self.urlopen = self.opener.open
		else:
			self.urlopen = ClientCookie.urlopen

	def teardown_method(self, method):
		try:
			pid = int(open(self.pidfile, "r").read())
		except Exception, e:
			print "Could not read pid from file"
			pid = None
		method_time = time.clock() - self.method_start
		if method_time < 0.2:
			print "%s took only %0.2f seconds, sleeping to recover" % (method.__name__, method_time)
			time.sleep(0.3 - method_time)
		self.servicemanager.removeservice(pid)
		# this sleep seems to help let them get deleted
		time.sleep(0.25)
		if os.path.exists(self.pidfile):
			os.remove(self.pidfile)

	def fetch_page(self, relative_url):
		"""Fetches a page from the webserver installed in the service"""
		url = "http://%s:%d/%s" % (self.hostname, self.port, relative_url)
		print "fetching", url
		stream = self.urlopen(url)
		contents = stream.read()
		return contents

class TestHelloWorldService(TestService):
	def test_hello_world(self):
		"""Tests that the page returns Hello World"""
		contents = self.fetch_page("")
		assert contents.strip() == "Hello World"
	test_hello_world.extraargs = ["--servertype", "standard"]

	def test_hello_world_threaded(self):
		"""Tests that services work in threaded mode"""
		self.test_hello_world()
	test_hello_world_threaded.extraargs = ["--servertype", "threaded"]

if __name__ == "__main__":
	ntservice.HandleCommandLine(helloworldservice.HelloWorldService)


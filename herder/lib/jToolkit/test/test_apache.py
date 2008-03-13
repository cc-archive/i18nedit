#!/usr/bin/env python

from py import test
import win32serviceutil
import win32service
import servicemanager
import os
try:
	import subprocess
except ImportError:
	subprocess = None
import urllib2
try:
	import cookielib
except ImportError:
	# fallback for python before 2.4
	cookielib = None
	import ClientCookie
import time
from jToolkit.web import apacheconf

class ServiceManager:
	def __init__(self, servicename):
		self.hscm = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_ALL_ACCESS)
		self._hs = None
		self.servicename = servicename

	def __del__(self):
		if self._hs is not None:
			win32service.CloseServiceHandle(self._hs)
		win32service.CloseServiceHandle(self.hscm)

	def readhs(self):
		return win32service.OpenService(self.hscm, self.servicename, win32service.SERVICE_ALL_ACCESS)

	def geths(self, raiseerrors=False):
		if self._hs is None:
			try:
				self._hs = self.readhs()
			except Exception, e:
				if raiseerrors:
					raise e
			return self._hs
		return self._hs

	def closeservice(self):
		if self._hs is not None:
			win32service.CloseServiceHandle(self._hs)
			self._hs = None
	hs = property(geths)

	def getstatus(self):
		hs = self.hs
		if hs is not None:
			return win32service.QueryServiceStatus(hs)[1]
		return None
	status = property(getstatus)
	
	def installservice(self, apachedir, configfile):
		"""Asks apache to install itself as a service with the given configuration"""
		exe = os.path.join(apachedir, "bin", "Apache.exe")
		args = [exe, "-f", configfile, "-n", self.servicename, "-k", "install"]
		if subprocess is None:
			result = os.spawnl(os.P_WAIT, exe, *args)
		else:
			result = subprocess.call(args)
		return result == 0

	def killprocess(self, pid):
		"""Tries to kill the given process, using pskill if available, or asks user to"""
		# TODO: add more info for user. pskill is from sysinternals.com
		result = os.system("pskill %d" % pid)
		if result != 0:
			print "Please try and kill process %d" % pid
			raw_input("Press Enter when done... ")

	def removeservice(self, pid=None):
		"""Removes the service. The given process ID will be killed if stopping the service fails"""
		stoperror = None
		try:
			self.stopservice()
		except Exception, e:
			print "Error stopping service, will try delete anyway:", e
			stoperror = e
			if pid is not None:
				self.killprocess(pid)
		try:

			win32service.DeleteService(self.geths(True))
		except Exception, e:
			if len(e.args) < 2:
				raise
			elif e.args[2] == 'The specified service has been marked for deletion.':
				pass
			elif e.args[2] == 'The specified service does not exist as an installed service.':
				pass
			else:
				raise
		if stoperror:
			raise
		self.closeservice()

	def startservice(self):
		win32service.StartService(self.hs, [])
		win32serviceutil.WaitForServiceStatus(self.servicename, win32service.SERVICE_RUNNING, 5)

	def stopservice(self):
		hs = self.hs
		if hs is not None:
			if self.status != win32service.SERVICE_STOPPED:
				win32service.ControlService(hs, win32service.SERVICE_CONTROL_STOP)
			win32serviceutil.WaitForServiceStatus(self.servicename, win32service.SERVICE_STOPPED, 5)

class TestApacheService(object):
	servicename = "ApacheTest_jLogbook"
	hostname = "localhost"
	port = 8080
	def setup_class(cls):
		"""constructs a service manager to manage the apache service"""
		cls.servicemanager = ServiceManager(cls.servicename)
		cls.find_apache_dir()

	def find_apache_dir(cls):
		"""finds the newest version of apache, sets .apachedir to its directory"""
		diroptions = apacheconf.getApacheDirOptions()
		apacheversion = max(diroptions)
		cls.apachedir = diroptions[apacheversion]
		print "found apache %s in %s" % (apacheversion, cls.apachedir)
	find_apache_dir = classmethod(find_apache_dir)

	def clear_testdir(self):
		"""removes the test directory"""
		if os.path.exists(self.testdir):
			for dirpath, subdirs, filenames in os.walk(self.testdir, topdown=False):
				for name in filenames:
					os.remove(os.path.join(dirpath, name))
				for name in subdirs:
					os.rmdir(os.path.join(dirpath, name))
				if os.path.exists(self.testdir): os.rmdir(self.testdir)
		assert not os.path.exists(self.testdir)

	def setup_method(self, method):
		"""sets up a new service and configfile for the given method"""
		dirname = os.path.abspath(os.getcwd())
		testname = "%s_%s" % (self.__class__.__name__, method.__name__)
		self.configfile = os.path.join(dirname, "%s.conf" % testname)
		self.testdir = os.path.join(dirname, testname)
		self.clear_testdir()
		os.mkdir(self.testdir)
		if os.path.exists(self.configfile):
			os.remove(self.configfile)
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
				os.system("net stop %s" % self.servicemanager.servicename)
				if self.servicemanager.hs is not None:
					print "attempt to wait for service deletion unsuccessful"
					raise
			else:
				print "error removing service (not neccessarily serious): %s" % e
		# handle cookies etc
		if cookielib:
			self.cookiejar = cookielib.CookieJar()
			self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookiejar))
			self.urlopen = self.opener.open
		else:
			self.urlopen = ClientCookie.urlopen
		config_contents = self.make_config_file(method)
		open(self.configfile, "w").write(config_contents)
		assert self.servicemanager.installservice(apachedir=self.apachedir, configfile=self.configfile)
		try:
			self.servicemanager.startservice()
		except:
			self.servicemanager.removeservice()
			raise
		self.method_start = time.clock()
		print "starting method", method.__name__

	def make_apache_path(self, dirname):
		"""returns the path with / separators for apache"""
		return "/".join(os.path.abspath(dirname).split(os.path.sep))

	def make_config_file(self, method):
		"""returns the contents of an apache config file for tests"""
		serverroot = self.make_apache_path(self.apachedir)
		modpython_path = self.make_apache_path(os.path.join(self.apachedir, "modules", "mod_python.so"))
		listenport = 8080
		contents = """ServerRoot "%s"\nServerName 127.0.0.1\nListen %d\nLoadModule python_module "%s"\nDocumentRoot "%s"\n""" % (serverroot, listenport, modpython_path, self.testdir)
		return contents

	def teardown_method(self, method):
		"""clean up after the method by removing the service and test files"""
		method_time = time.clock() - self.method_start
		if method_time < 0.2:
			print "%s took only %0.2f seconds, sleeping to recover" % (method.__name__, method_time)
			time.sleep(0.3 - method_time)
		self.servicemanager.removeservice()
		# this sleep seems to help let them get deleted
		time.sleep(0.25)
		if os.path.exists(self.configfile):
			os.remove(self.configfile)
		self.clear_testdir()

	def fetch_page(self, relative_url):
		"""Fetches a page from the webserver installed in the service"""
		url = "http://%s:%d/%s" % (self.hostname, self.port, relative_url)
		print "fetching", url
		stream = self.urlopen(url)
		contents = stream.read()
		return contents

	def test_basic_apache(self):
		"""tests we can actually run the service"""
		assert test.raises(urllib2.HTTPError, self.fetch_page, "does-not-exist.html")

	def make_directory_config(self, dirname, directives):
		contents = "\n  ".join(directives)
		return "<Directory '%s'>\n  %s\n</Directory>\n" % (self.make_apache_path(dirname), contents)

class TestApacheHelloWorld(TestApacheService):
	"""Tests serving up a simple Hello World page"""
	def test_hello_world(self):
		"""Tests that the page returns Hello World"""
		contents = self.fetch_page("")
		assert contents.strip() == "Hello World"

	def make_config_file(self, method):
		"""returns the contents of an apache config file for tests"""
		contents = super(TestApacheHelloWorld, self).make_config_file(method)
		if method == self.test_hello_world:
			from jToolkit.demo import helloworld
			helloworlddir = os.path.dirname(os.path.abspath(helloworld.__file__))
			prefsfile = os.path.join(helloworlddir, "helloworld.prefs")
			directives = ["SetHandler mod_python",
				"PythonHandler jToolkit.web",
				"PythonOption jToolkit.prefs '%s'" % self.make_apache_path(prefsfile),
				"PythonOption jToolkit.instance HelloWorldConfig",
				"PythonDebug On"]
			contents += self.make_directory_config(self.testdir, directives)
		return contents


#!/usr/bin/env python

import threading
import time
import win32serviceutil
import win32evtlog
import win32evtlogutil
import win32service
import servicemanager
import sys
import os
import traceback

class TestThreading:
	ThreadClass = threading.Thread
	def target(self, argdict):
		argdict["success"] = True
	def test_thread_creation(self):
		argdict = {}
		t = self.ThreadClass(target = self.target, args = (argdict,))
		t.start()
		t.join()
		assert "success" in argdict
		return True

class TestLuceneThreading(TestThreading):
	def setup_class(cls):
		import PyLucene
		cls.ThreadClass = PyLucene.PythonThread

def run_tests():
	testplain = TestThreading()
	print testplain.test_thread_creation()
	testlucene = TestLuceneThreading()
	testlucene.setup_class()
	print testlucene.test_thread_creation()

class ServiceRunner(win32serviceutil.ServiceFramework):
	_svc_name_ = "PyThreadTest"
	_svc_display_name_ = "PyThreadTest"
	_svc_evt_src_ = _svc_name_
	def SvcStop(self):
		self.dolog("CALLED SvcStop")
		self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
		self.stop = True
	def SvcDoRun(self):
		self.dolog("CALLED SvcDoRun")
		while not self.stop:
			self.run_tests()
	def run_tests(self):
		testplain = TestThreading()
		testplain.test_thread_creation()
		win32evtlogutil.ReportEvent(self._svc_evt_src_, 1, 0, win32evtlog.EVENTLOG_INFORMATION_TYPE, ["Plain Test passed"], None, None)
		# testlucene = TestLuceneThreading()
		# testlucene.setup_class()
		# testlucene.test_thread_creation()
		# win32evtlogutil.ReportEvent(self._svc_evt_src_, 1, 0, win32evtlog.EVENTLOG_INFORMATION_TYPE, ["PyLucene Test passed"], None, None)
		time.sleep(1)
	def dolog(self, message):
		win32evtlogutil.ReportEvent(service._svc_evt_src_, 1, 0, win32evtlog.EVENTLOG_INFORMATION_TYPE, [message], None, None)

class ServiceManager:
	_svc_name_ = "PyThreadTest"
	_svc_display_name_ = "PyThreadTest"
	_svc_evt_src_ = _svc_name_
	def get_manager(self):
		self.hscm = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_ALL_ACCESS)
	def release_manager(self):
		win32service.CloseServiceHandle(self.hscm)
	def installservice(self):
		self.get_manager()
		pythonserviceexe = sys.executable # win32serviceutil.LocatePythonServiceExe()
		exeName = "%s %s --runservice" % (pythonserviceexe, os.path.abspath(__file__))
		try:
			hs = win32service.CreateService(self.hscm, self._svc_name_, self._svc_display_name_,
				win32service.SERVICE_ALL_ACCESS,
				win32service.SERVICE_WIN32_OWN_PROCESS,
				win32service.SERVICE_DEMAND_START,
				win32service.SERVICE_ERROR_NORMAL,
				exeName, None, 0, None, None, None)
			win32service.CloseServiceHandle(hs)
		finally:
			self.release_manager()
	def removeservice(self):
		win32serviceutil.RemoveService(self._svc_name_)
	def runservice(self):
		servicemanager.SetEventSourceName(self._svc_evt_src_)
		win32evtlogutil.AddSourceToRegistry(self._svc_evt_src_, win32evtlog.__file__)
		self.stop = False
		servicemanager.Initialize(self._svc_name_, os.path.abspath(servicemanager.__file__))
		servicemanager.PrepareToHostSingle(ServiceRunner)
		self.ssh = servicemanager.RegisterServiceCtrlHandler(self._svc_name_, self.ServiceCtrlHandler)
		servicemanager.StartServiceCtrlDispatcher()
	def launchservice(self):
		hs = None
		self.get_manager()
		try:
			hs = win32service.OpenService(self.hscm, self._svc_name_, win32service.SERVICE_ALL_ACCESS)
			win32service.StartService(hs, [])
			win32serviceutil.WaitForServiceStatus(self._svc_name_, win32service.SERVICE_RUNNING, 5)
			win32service.ControlService(hs, win32service.SERVICE_STOP)
			win32serviceutil.WaitForServiceStatus(self._svc_name_, win32service.SERVICE_STOPPED, 5)
		finally:
			if hs is not None:
				win32service.CloseServiceHandle(hs)
			self.release_manager()

class TestService:
	def disabled_test_service(self):
		servicemanager = ServiceManager()
		try:
			servicemanager.removeservice()
		except Exception, e:
			print "error removing service (not neccessarily serious): %s" % e
		try:
			servicemanager.installservice()
			time.sleep(1)
			servicemanager.launchservice()
		finally:
			servicemanager.removeservice()


if __name__ == "__main__":
	if "--runservice" in sys.argv:
		service = ServiceRunner()
		try:
			service.runservice()
		except Exception, e:
			exc_info = sys.exc_info()
			logmessage = "".join(traceback.format_exception(exc_info[0], exc_info[1], exc_info[2]))
			win32evtlogutil.ReportEvent(service._svc_evt_src_, 1, 0, win32evtlog.EVENTLOG_INFORMATION_TYPE, [logmessage], None, None)
			raise
	elif "--serviceinstall" in sys.argv:
		service = ServiceManager()
		service.installservice()
	elif "--serviceremove" in sys.argv:
		service = ServiceManager()
		service.removeservice()
	else:
		run_tests()


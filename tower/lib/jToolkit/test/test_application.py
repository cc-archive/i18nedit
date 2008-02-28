#!/usr/bin/env python

from jToolkit import prefs
from jToolkit.data import dates
from jToolkit.demo import helloworld
from jToolkit.web import server
from jToolkit.web import session
from jToolkit.web import simplewebserver

sessioncache = session.SessionCache()

def mixedmethod(m):
    """returns a method that can be called either as a class method or as an instance method"""
    def internal(*args, **kwargs):
         sorc = args[0]
         print sorc
         return m(*args, **kwargs)
    return staticmethod(internal)

def isclassmethod(cls, method):
    """returns whether the given method (accessed as a class attribute) is a classmethod"""
    return method.im_self == cls

class ApplicationTester(object):
    """Defines a framework for constructing Application Tests.
    Requires staticmethods for setup_ and teardown_ methods
    These methods can then be used either ClassWise or MethodWise (see below)
    """
    SessionClass = session.Session

    @staticmethod
    def setup_testframe(self_or_cls):
        """sets up a webserver and application server for this object or class"""
        self_or_cls.webserver = self_or_cls.setup_webserver(self_or_cls)
        self_or_cls.prefs = self_or_cls.setup_prefs(self_or_cls)
        self_or_cls.server = self_or_cls.setup_application(self_or_cls)
        if type(self_or_cls) == type:
            self_or_cls.server.name = self_or_cls.__name__
        else:
            self_or_cls.server.name = self_or_cls.__class__.__name__
        self_or_cls.instance = self_or_cls.server.instance
        self_or_cls.session = self_or_cls.setup_session(self_or_cls)

    @staticmethod
    def teardown_testframe(self_or_cls):
        """tears down the webserver and application server..."""
        self_or_cls.prefs = None
        self_or_cls.server = None
        self_or_cls.instance = None
        self_or_cls.session = None
        self_or_cls.webserver = None

    @staticmethod
    def setup_webserver(self_or_cls):
        """setup the webserver that will be used for the tests"""
        return simplewebserver.DummyServer()

    @staticmethod
    def setup_application(self_or_cls):
        """Returns the application server object"""
        raise NotImplemented

    @staticmethod
    def teardown_application(self_or_cls):
        """tears down the application server object"""
        raise NotImplemented

    @staticmethod
    def setup_session(self_or_cls):
        """sets up the session for the test"""
        test_session = self_or_cls.SessionClass(sessioncache, self_or_cls.server)
        timestamp = dates.formatdate(dates.currentdate(), '%Y%m%d%H%M%S')
        # test_session.create("admin","",timestamp,'en')
        test_session.remote_ip = "unit tests..."
        return session

    @staticmethod
    def setup_prefs(self_or_cls):
        """returns a prefs file object"""
        return prefs.PrefsParser()

class TestApplicationClassWise:
    """a test class to run tests on a jToolkit application"""
    def setup_class(cls):
        """sets up a webserver and application server for this class"""
        cls.setup_testframe(cls)

    def teardown_class(cls):
        """tears down the webserver and application server..."""
        cls.teardown_testframe(cls)

class TestApplicationMethodWise:
    """don't reuse webserver objects between methods"""
    def setup_method(self, method):
        """sets up a webserver and jlogbookserver for this method"""
        self.setup_testframe(self)

    def teardown_method(self, method):
        """sets up a webserver and jlogbookserver for this method"""
        self.setup_testframe(self)

def CreateApplicationTester(ApplicationTesterClass, serverperclass):
    """sets up an application tester. If serverperclass is True, uses one server per class, otherwise one per method"""
    if serverperclass:
        class TestApplication(ApplicationTesterClass, TestApplicationClassWise):
            pass
            # setup_webserver = classmethod(ApplicationTesterClass.setup_webserver)
            # setup_application = classmethod(ApplicationTesterClass.setup_application)
            # teardown_application = classmethod(ApplicationTesterClass.teardown_application)
            # setup_session = classmethod(ApplicationTesterClass.setup_session)
            # setup_prefs = classmethod(ApplicationTesterClass.setup_prefs)
        print TestApplication.setup_webserver, ApplicationTesterClass.setup_webserver
        TestApplication.setup_webserver(TestApplication)
    else:
        class TestApplication(ApplicationTesterClass, TestApplicationMethodWise):
            pass
    return TestApplication

class DemoAppTester(ApplicationTester):
    @staticmethod
    def setup_application(self_or_cls):
        return helloworld.HelloWorldServer(self_or_cls.prefs, self_or_cls.webserver)

    def test_demo(self):
        assert isinstance(self.server, server.AppServer)

TestDemoAppClassWise = CreateApplicationTester(DemoAppTester, serverperclass=True)
TestDemoAppMethodWise = CreateApplicationTester(DemoAppTester, serverperclass=False)


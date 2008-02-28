#!/usr/bin/env python

# The purpose of this module is to provide a battery of tests for a database
# The idea being that you would then implement the necessary database-specific bits in separate modules

from jToolkit.data import database
from jToolkit import errors
import os
import glob
import threading
import time

class BaseTestDatabase:
    def create_database(cls, config):
        # config is enough of a configuration to create the required database class
        cls.db = database.dbwrapper(config, errors.ConsoleErrorHandler())
    create_database = classmethod(create_database)
        
    def setup_method(self, method):
        self.methodid = "%s_%s" % (self.__class__.__name__, method.__name__)
        self.tablename = method.__name__
        self.sqlfile = "%s.sql" % (self.methodid)
        if os.path.exists(self.sqlfile):
            os.remove(self.sqlfile)
        for resultfile in self.getresultfiles():
            os.remove(resultfile)
        self.teardownsql = None

    def teardown_method(self, method):
        if self.teardownsql:
            self.db.execute(self.teardownsql)
        if os.path.exists(self.sqlfile):
            os.remove(self.sqlfile)
        for resultfile in self.getresultfiles():
            os.remove(resultfile)
            
    def getresultfiles(self):
        """lists available result files"""
        return glob.glob("%s*.txt" % self.methodid)

    def test_table_create(self, tablename=None):
        """Test creating a table"""
        if not tablename:
            tablename = self.tablename
        createsql = "create table %s(x %s, y %s)" % (tablename, self.db.dbtypename("string"), self.db.dbtypename("string"))
        self.teardownsql = "drop table %s" % tablename
        self.db.execute(createsql)

    def test_insert(self, tablename=None):
        """Test inserting into a table - doesn't test the validity of what's inserted (see select test for that)"""
        if not tablename:
            tablename = self.tablename
        self.test_table_create(tablename)
        insertsql = "insert into %s(x, y) values('test', 'me')" % tablename
        self.db.execute(insertsql)
        self.db.execute(insertsql)

    def test_select(self, tablename=None):
        """Test selecting from a table"""
        if not tablename:
            tablename = self.tablename
        self.test_insert(tablename)
        selectsql = "select * from %s" % tablename
        rows = self.db.allrowdicts(selectsql)
        assert len(rows) == 2
        for row in rows:
            assert len(row) == 2
            assert row["x"] == "test"
            assert row["y"] == "me"

    def test_threaded(self, threadClass=None):
        """Test multi-threaded insert/select"""
        NUM_THREADS = 30
        if not threadClass:
            threadClass = threading.Thread
        def test_threaded_func(obj, num):
            print "In thread %d" % num
            obj.test_select("test_threaded_%d" % num)
            self.db.execute("drop table test_threaded_%d" % num)
            print "Done thread %d" % num
        threads = [threadClass(target=test_threaded_func, args=[self, num]) for num in range(NUM_THREADS)]
        for thr in threads:
            thr.start()
        
        threadsEnded = False
        for i in range(6000):       # Give ourselves 10 minutes
            if not (True in [thr.isAlive() for thr in threads]):
                threadsEnded = True
                break
            time.sleep(1)
        assert(threadsEnded)
        self.teardownsql = None

    def test_pylucene_threaded(self):
        """Test threaded with PyLucene threads"""
        try:
            import PyLucene
        except ImportError:
            print "PyLucene has to be installed for this test"
            assert(False)
        self.test_threaded(PyLucene.PythonThread)

    def test_intensive_select_count(self):
        """Test select count(*) intensively"""
        NUM_ROWS = 20
        self.test_table_create()
        insertsql = "insert into %s(x, y) values ('test', 'me')" % self.tablename
        countsql = "select count(*) from %s" % self.tablename
        for i in range(NUM_ROWS):
            self.db.execute(insertsql)
            count = self.db.singlevalue(countsql)
            assert(count is not None)
            assert(int(count) == (i+1))

    def test_list_fields(self):
        """Test listing the fields in a database table"""
        self.test_select()
        columnnames = self.db.listfieldnames(self.tablename)
        assert(str(columnnames[0]) == 'x')
        assert(str(columnnames[1]) == 'y')

    def test_list_fields_and_select_count(self):
        """Test a condition which seems to be failing on Nick's computer with MyOleDB"""
        self.test_list_fields()
        countsql = "select count(*) from %s" % self.tablename
        count = self.db.singlevalue(countsql)
        assert(count is not None)
        assert(int(count) == 2)
        columnnames = self.db.listfieldnames(self.tablename)
        assert(str(columnnames[0]) == 'x')
        assert(str(columnnames[1]) == 'y')
        count = self.db.singlevalue(countsql)
        assert(count is not None)
        assert(int(count) == 2)



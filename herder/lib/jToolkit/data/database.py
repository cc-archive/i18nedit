#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""database is a wrapper for Python DB-API 2.0 client database drivers, making functionality simple"""

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

from jToolkit import cidict
from jToolkit import timecache
from jToolkit import prefs
from jToolkit.data import dates
from jToolkit.data import dbtable
import types
import atexit
import time
import StringIO
import csv
import os

try:
  import threading
except:
  threading = None

def importPyADO():
  """imports the PyADO module. returns module, error class"""
  from jToolkit.data import PyADO
  return PyADO, PyADO.error

def importpg():
  """imports pgdb driver. returns module, error class"""
  import pgdb
  return pgdb, pgdb.Error

def importmysql():
  """imports MySQLdb driver. returns module, error class"""
  import MySQLdb
  return MySQLdb, MySQLdb.Error

def importcx_Oracle():
  """imports MySQLdb driver. returns module, error class"""
  import cx_Oracle
  return cx_Oracle, cx_Oracle.Error

def importsqlite():
  """imports the sqlite driver. returns module, error class"""
  from pysqlite2 import dbapi2 as sqlite3
  return sqlite3, sqlite3.Error
  
# TODO: expand to have a short string type that's length 64 (if required)
dbtypenames = {
  'access': {'string':'string', 'text':'text', 'datetime':'datetime',
             'integer':'integer', 'number':'integer', 'double':'float'},
  'sqlserver': {'string':'varchar(255)', 'text':'varchar(4000)', 'datetime':'datetime',
             'integer':'integer', 'number':'integer', 'double':'float'},
  'oracle': {'string':'varchar2(255)', 'text':'varchar2(4000)', 'datetime':'date',
             'integer':'integer', 'number':'integer', 'double':'float'},
  'postgres': {'string':'varchar(255)', 'text':'varchar(4000)', 'datetime':'timestamp',
             'integer':'integer', 'number':'integer', 'double':'float'},
  'mysql': {'string':'varchar(255)', 'text':'text', 'datetime':'datetime',
             'integer':'integer', 'number':'integer', 'double':'float'},
  'sqlite': {'string':'unicode', 'text': 'unicode', 'datetime':'timestamp',
             'integer':'integer', 'number':'integer', 'double':'numeric'},
  }

def upper(text):
  """uppercase function, handling str or unicode text"""
  if hasattr(text, "upper"):
    return text.upper()
  return text

def lower(text):
  """lowercase function, handling str or unicode text"""
  if hasattr(text, "lower"):
    return text.lower()
  return text

def nonetoblank(text):
  """converts None to a blank string"""
  if text is None: return ""
  return text

if threading:
  dbwrapperinitlock = threading.RLock()
else:
  class nothreadlock:
    def acquire(self): pass
    def release(self): pass
  dbwrapperinitlock = nothreadlock()

class NoErrorHandling:
  def logerror(self, message):
    pass

  def logtrace(self, message):
    pass

  def exception_str(self):
    return ""

class ThreadLocalDB(object):
  """wraps a db connection object by forwarding attributes to the thread-local db"""
  def __init__(self, dbparent):
    """sets up the thread wrapper, dbparent is the dbwrapper instance"""
    self.__dbparent = dbparent
  def __getdb__(self):
    """calls getlocaldb on dbparent to find the actual thread-local db"""
    return self.__dbparent.getlocaldb()
  def __getattr__(self, attrname):
    """finds the attribute on the thread-local database"""
    db = self.__getdb__()
    return getattr(db, attrname)

class ThreadComDB(object):
  """Makes sure we call CoInitializeEx on each thread that uses the DB"""
  def __init__(self, dbparent):
    """sets up the thread wrapper, dbparent is the dbwrapper instance"""
    self.__dbparent = dbparent
  def __getdb__(self):
    """calls initthread on dbparent to init the thread and returns the db"""
    self.__dbparent.initthread()
    return self.db
  def __getattr__(self, attrname):
    """finds the attribute on the real database"""
    db = self.__getdb__()
    return getattr(db, attrname)

class LocalThreading(object):
  """simple implementation of localthreading for python < 2.4"""
  def __init__(self):
    self.__dict__["__threadsdict"] = {}
  def __getattr__(self, attrname):
    """gets the attribute from the thread dictionary"""
    threadname = threading.currentThread().getName()
    threaddict = self.__dict__["__threadsdict"].setdefault(threadname, {})
    if attrname in threaddict:
      return threaddict[attrname]
    else:
      raise AttributeError("attribute %s not present in threadlocal storage for thread %s" % (attrname, threadname))
  def __setattr__(self, attrname, attrvalue):
    """sets the attribute in the thread dictionary"""
    threadname = threading.currentThread().getName()
    threaddict = self.__dict__["__threadsdict"].setdefault(threadname, {})
    threaddict[attrname] = attrvalue

class dbwrapper:
  def __init__(self, instance, errorhandler=None, cachetables=None, generalcache=True):
    """initialises the dbwrapper class..."""
    self.isopen = False
    if errorhandler is None:
      self.errorhandler = NoErrorHandling()
    else:
      self.errorhandler = errorhandler
    dbwrapperinitlock.acquire()
    self.instance = instance
    if hasattr(self.instance, "DBFROMREGISTRY"):
      self.readregistrysettings(self.instance.DBFROMREGISTRY)
    self.tracestatements = prefs.evaluateboolean(getattr(self.instance, "DBTRACESQL", None))
    self.DBTYPE = instance.DBTYPE
    self.initlocal()
    try:
      self.importdriver()
    finally:
      dbwrapperinitlock.release()
    self.initthread()
    # initialise self.db
    self.dblogin()
    # FIXME: fancy case change troubles...
    self.upper = upper
    self.lower = lower
    self.nonetoblank = nonetoblank
    self.dbtypenames = dbtypenames[self.DBTYPE]
    # record statistics for optimisation
    self.sqlstats = {}
    self.encoding = getattr(instance, "DBENCODING", "utf8")
    try:
      self.UTCClient = instance.UTCClient
      self.UTCServer = instance.UTCServer
    except:
      self.UTCClient = 0
      self.UTCServer = 0
    # set up caches
    self.cachetables = []
    self.generalcache = generalcache
    self.singlerowcaches = cidict.cidict()
    self.allrowscaches = cidict.cidict()
    if self.generalcache:
      self.singlerowcaches[''] = timecache.timecache(120)
      self.allrowscaches[''] = timecache.timecache(170)
    if cachetables is not None:
      for cachetable, expirytime in self.cachetables:
        self.cachetables.append(cachetable)
        self.singlerowcaches[cachetable] = TimeCache.timecache(expirytime)
        self.allrowscaches[cachetable] = TimeCache.timecache(expirytime)

  def initlocal(self):
    """initializes a thread-local self.local object and use it to create a local db object..."""
    if hasattr(threading, "local"):
      local = threading.local()
    else:
      local = LocalThreading()
    self.local = local
    dbprovider = getattr(self.instance, "DBPROVIDER", None)
    if self.DBTYPE == "sqlite" or (self.DBTYPE == "mysql" and not dbprovider):
      self.db = ThreadLocalDB(self)
    elif dbprovider and self.DBTYPE in ("mysql","access","sqlserver","oracle"):
      self.db = ThreadComDB(self)

  def getlocaldb(self):
    """finds a thread-local database (creating it by logging in if neccessary)"""
    if hasattr(self.local, "db"):
      return self.local.db
    self.dblogin()
    return self.local.db

  def initthread(self):
    """Finds whether CoInitialize has been called on this thread, and if not, call it"""
    name = threading.currentThread().getName()
    dbprovider = getattr(self.instance, "DBPROVIDER", None)
    if not (dbprovider and self.DBTYPE in ("mysql","access","sqlserver","oracle")):
        return
    if not hasattr(self.local, "CoInitCalled"):
      self.driver.CoInitializeEx(self.driver.COINIT_MULTITHREADED)
      self.local.CoInitCalled = True

  def __del__(self):
    """close the database when the object is destroyed"""
    self.dbclose()

  def readregistrysettings(self, regkeyname, usejsuitedrivers=False):
    """reads the latest settings from the registry key name given"""
    from jToolkit import winreg
    import win32con
    hklm_key = winreg.regkey(win32con.HKEY_LOCAL_MACHINE, "Software").childkey(regkeyname)
    hkcu_key = winreg.regkey(win32con.HKEY_CURRENT_USER, "Software").childkey(regkeyname)
    for reg_key in (hklm_key, hkcu_key):
      try:
        dbtype = reg_key.getvalue("DatabaseType")
      except AttributeError:
        continue
      dbtype = dbtype[0].strip("\x00")
      db_key = reg_key.childkey(dbtype)
      def getdbvalue(keyname):
        try:
          return db_key.getvalue(keyname)[0].strip("\x00")
        except AttributeError:
          return None
      self.instance.DBTYPE = dbtype.lower()
      self.instance.DBPROVIDER = getdbvalue("OLEDBDriver")
      if self.instance.DBPROVIDER is None:
        if usejsuitedrivers:
          self.instance.DBPROVIDER = "jSuite." + dbtype
        else:
          import ADOProviders
          self.instance.DBPROVIDER = getattr(ADOProviders, dbtype + "Provider", None)
      self.instance.DBNAME = getdbvalue("Database")
      self.instance.DBUSER = getdbvalue("Username")
      self.instance.DBHOST = getdbvalue("Server")
      encpassword = getdbvalue("Password")
      if encpassword and regkeyname in ('jBrowser', 'jLogbook'):
        from jToolkit import minicrypt
        self.instance.DBPASSWORD = minicrypt.decrypt(encpassword, self.instance.DBUSER + self.instance.DBNAME + self.instance.DBHOST + dbtype)
      else:
        self.instance.DBPASSWORD = encpassword

  def clearcache(self, cachetables):
    """clears all the caches for the given sql command"""
    if self.generalcache:
      self.singlerowcaches[''].clear()
      self.allrowscaches[''].clear()
    for cachetable in cachetables:
      # TODO: handle ripple-through effects...
      if cachetable in self.cachetables:
        self.singlerowcaches[cachetable].clear()
        self.allrowscaches[cachetable].clear()

  def getcachetables(self, sql):
    """returns the list of cacheable tables that occur in the sql statement"""
    cachetables = []
    sql = sql.lower()
    for cachetable in self.cachetables:
      if sql.find(cachetable.lower()) != -1:
        cachetables.append(cachetable)
    return cachetables

  def getsinglerowcache(self, sql):
    """returns cached single row result for the sql statement"""
    cachetables = self.getcachetables(sql)
    cachedrow, description = None, None
    if len(cachetables) == 0:
      if self.generalcache:
        cachedrow, description = self.singlerowcaches[''].get(sql, (None, None))
    elif len(cachetables) == 1:
      cachedrow, description = self.singlerowcaches.get(cachetables[0], self.singlerowcaches.get('', {})).get(sql, (None, None))
    else:
      # TODO: check that it's the same for all of them
      cachedrow, description = self.singlerowcaches.get(cachetables[0], self.singlerowcaches.get('', {})).get(sql, (None, None))
    return cachedrow, description

  def setsinglerowcache(self, sql, cachedrow, description):
    """caches single row result for the sql statement"""
    cachetables = self.getcachetables(sql)
    if len(cachetables) == 0:
      if self.generalcache:
        self.singlerowcaches[''][sql] = (cachedrow, description)
    else:
      for cachetable in cachetables:
        if cachetable in self.cachetables:
          self.singlerowcaches[cachetables][sql] = (cachedrow, description)
        elif self.generalcache:
          self.singlerowcaches[''][sql] = (cachedrow, description)

  def getallrowscache(self, sql):
    """returns cached all rows result for the sql statement"""
    cachetables = self.getcachetables(sql)
    cachedrows, description = None, None
    if len(cachetables) == 0:
      if self.generalcache:
        cachedrows, description = self.allrowscaches[''].get(sql, (None, None))
    elif len(cachetables) == 1:
      cachedrows, description = self.allrowscaches.get(cachetables[0], self.allrowscaches.get('', {})).get(sql, (None, None))
    else:
      # TODO: check that it's the same for all of them
      cachedrows, description = self.allrowscaches.get(cachetables[0], self.allrowscaches.get('', {})).get(sql, (None, None))
    return cachedrows, description

  def setallrowscache(self, sql, cachedrows, description):
    """caches all rows result for the sql statement"""
    cachetables = self.getcachetables(sql)
    if len(cachetables) == 0:
      if self.generalcache:
        self.allrowscaches[''][sql] = (cachedrows, description)
    else:
      for cachetable in cachetables:
        if cachetable in self.cachetables:
          self.allrowscaches[cachetables][sql] = (cachedrows, description)
        elif self.generalcache:
          self.allrowscaches[''][sql] = (cachedrows, description)

  def importdriver(self):
    if self.DBTYPE == 'oracle':
      if hasattr(self.instance, 'NLS_LANG'):
        import os
        os.environ['NLS_LANG'] = self.instance.NLS_LANG
        self.errorhandler.logtrace("set NLS_LANG to %r" % self.instance.NLS_LANG)
      use_pyado = hasattr(self.instance, "DBPROVIDER")
      if use_pyado:
        try:
          self.driver, self.dberror = importPyADO()
        except ImportError:
          use_pyado = False
      if not use_pyado:
        self.driver, self.dberror = importcx_Oracle()
    elif self.DBTYPE in ('access', 'sqlserver'):
      self.driver, self.dberror = importPyADO()
    elif self.DBTYPE == 'postgres':
      self.driver, self.dberror = importpg()
    elif self.DBTYPE == 'mysql':
      use_pyado = hasattr(self.instance, "DBPROVIDER")
      if use_pyado:
        self.driver, self.dberror = importPyADO()
      else:
        self.driver, self.dberror = importmysql()
    elif self.DBTYPE == 'sqlite':
      self.driver, self.dberror = importsqlite()

  def dblogin(self):
    """Login to the database"""
    kwargs = {}
    extraparams = getattr(self.instance, "DBPARAMS", "").split(",")
    createdb = getattr(self.instance, "DBCREATE", None)
    if createdb == "ifmissing":
      kwargs["DBCREATE"] = createdb
    elif createdb is not None:
      kwargs["DBCREATE"] = prefs.evaluateboolean(createdb)
    self.convert_unicode_sql = False
    for extraparam in extraparams:
      if extraparam:
        kwargs[extraparam] = getattr(self.instance, extraparam, None)
    if self.DBTYPE == 'access':
      self.errorhandler.logtrace('dblogin: dbname = %s, dbuser = %s, dbprovider=%s' % \
        (self.instance.DBNAME, self.instance.DBUSER, self.instance.DBPROVIDER))
      self.db.db = self.driver.connect(None,database=self.instance.DBNAME,host=None,
        user=self.instance.DBUSER,password=self.instance.DBPASSWORD,provider=self.instance.DBPROVIDER, **kwargs)
    elif self.DBTYPE == 'oracle':
      if hasattr(self.instance, "DBPROVIDER"):
        # PyADO
        self.errorhandler.logtrace('dblogin: dbname = %s, dbuser = %s, dbname = %s, dbprovider=%s' % \
          (self.instance.DBNAME, self.instance.DBUSER, self.instance.DBNAME, self.instance.DBPROVIDER))
        self.db.db = self.driver.connect(None,database=self.instance.DBNAME,host=None,
          user=self.instance.DBUSER,password=self.instance.DBPASSWORD,provider=self.instance.DBPROVIDER, **kwargs)
      else:
        # cx_Oracle
        self.convert_unicode_sql = True
        if hasattr(self.instance, "DBDSN"):
          dsn = self.instance.DBDSN
          self.errorhandler.logtrace('dblogin: dsn = %s, dbuser = %s' % \
            (self.instance.DBDSN, self.instance.DBNAME))
        else:
          sid = self.instance.DBNAME
          host = getattr(self.instance, "DBHOST", None)
          port = getattr(self.instance, "DBPORT", 1521)
          self.errorhandler.logtrace('dblogin: dbname = %s, dbhost = %s, dbport = %s, dbuser = %s' % \
            (self.instance.DBNAME, host, port, DBUSER))
          if host is None or str(host) == "None":
            host = self.instance.DBNAME
          dsn = self.driver.makedsn(host, port, sid)
        self.db = self.driver.connect(user=self.instance.DBUSER,password=self.instance.DBPASSWORD,dsn=dsn,**kwargs)
    elif self.DBTYPE == 'sqlserver':
      self.convert_unicode_sql = True
      self.errorhandler.logtrace('dblogin: dbname = %s, dbhost = %s, dbuser = %s, dbprovider = %s' % \
        (self.instance.DBNAME, self.instance.DBHOST, self.instance.DBUSER, self.instance.DBPROVIDER))
      self.db.db = self.driver.connect(None,database=self.instance.DBNAME,host=self.instance.DBHOST,
        user=self.instance.DBUSER,password=self.instance.DBPASSWORD,provider=self.instance.DBPROVIDER,**kwargs)
    elif self.DBTYPE == 'postgres':
      self.errorhandler.logtrace('dblogin: dbname = %s, dbhost = %s, dbuser = %s' % \
        (self.instance.DBNAME, self.instance.DBHOST, self.instance.DBUSER))
      self.db = self.driver.connect(None,database=self.instance.DBNAME,host=self.instance.DBHOST,
        user=self.instance.DBUSER,password=self.instance.DBPASSWORD,**kwargs)
    elif self.DBTYPE == 'mysql':
      port = getattr(self.instance, "DBPORT", None)
      if port is None:
        port = os.getenv("MYSQL_TCP_PORT", None)
      if port is not None:
        kwargs["port"] = int(port)
      if hasattr(self.instance, "DBPROVIDER"):
        # PyADO
        self.errorhandler.logtrace('dblogin: dbname = %s, dbhost = %s, dbuser = %s, dbprovider=%s' % \
          (self.instance.DBNAME, self.instance.DBHOST, self.instance.DBUSER, self.instance.DBPROVIDER))
        self.db.db = self.driver.connect(None,database=self.instance.DBNAME,host=self.instance.DBHOST,
          user=self.instance.DBUSER,password=self.instance.DBPASSWORD,provider=self.instance.DBPROVIDER, **kwargs)
      else:
        self.errorhandler.logtrace('dblogin: dbname = %s, dbhost = %s, dbuser = %s' % \
          (self.instance.DBNAME, self.instance.DBHOST, self.instance.DBUSER))
        # Seems there's a small bug in MySQLdb which can mess with connecting to a remote host if it's given as a kwarg
        # This could be specific to a version of MySQLdb that nick has
        if not self.instance.DBHOST:
          self.local.db = self.driver.connect(db=self.instance.DBNAME,user=self.instance.DBUSER,passwd=self.instance.DBPASSWORD, **kwargs)
        else:
          self.local.db = self.driver.connect(db=self.instance.DBNAME,host=self.instance.DBHOST,
            user=self.instance.DBUSER,passwd=self.instance.DBPASSWORD, **kwargs)
    elif self.DBTYPE == 'sqlite':
      self.errorhandler.logtrace('dblogin: dbname = %s' % (self.instance.DBNAME))
      self.convert_unicode_sql = True
      self.local.db = self.driver.connect(self.instance.DBNAME, **kwargs)
      # self.driver.register_adapter("datetime", lambda x: Dates.pgdateparser.parse(x))
    self.isopen = True

  def dbclose(self, force=False):
    """closes the database connection if open (or force given)..."""
    if self.isopen or force:
      self.isopen = False
      self.db.close()

  def dbtable(self, tablename, columnlist, rowidcol, orderbycol):
    """returns a DBTable object for the given table"""
    return dbtable.DBTable(self, tablename, columnlist, rowidcol, orderbycol)

  def dbtypename(self, typename):
    """Returns a the proper text for the required variable type depending on the database"""
    return self.dbtypenames[typename.lower()]

  def dberrorrollback(self):
    """rollback on the database after an error"""
    unsupported = getattr(self.driver, 'NotSupportedError', self.dberror)
    try:
      self.db.rollback()
    except self.dberror:
      # since we're rolling back in response to an error, ignore this error
      pass

  def hack_statement(self, sql):
    """Adjust the SQL to work around any unusual/uncommon standards for various databases.
    For instance, MySQL needs backslashes escaped.
    Returns the adjusted statement"""
    if self.DBTYPE == 'mysql':
        sql = '\\\\'.join(sql.split('\\'))
    return sql

  def cursorexecute(self, sql):
    """constructs a database cursor and executes sql on it, returning the cursor"""
    cursor = self.db.cursor()
    if self.tracestatements:
      if isinstance(sql, unicode):
        self.errorhandler.logtrace("tracesql: sql=%r" % (sql))
      else:
        self.errorhandler.logtrace("tracesql: sql=%s" % (sql))
    sql = self.hack_statement(sql)
    cursor.execute(sql)
    return cursor

  def execute(self, sql):
    """execute a query, trap sql errors
    """
    if isinstance(sql, unicode) and self.convert_unicode_sql: sql = sql.encode(self.encoding)
    try:
      cursor = self.cursorexecute(sql)
      self.clearcache(self.getcachetables(sql))
      self.db.commit()
      return cursor
    except self.dberror:
      self.dberrorrollback()
      self.errorhandler.logerror("sql error executing query: " + str(sql) + ": " + self.errorhandler.exception_str())
      raise 

  def query(self, sql):
    """run a query, trap sql errors
    """
    if isinstance(sql, unicode) and self.convert_unicode_sql: sql = sql.encode(self.encoding)
    try:
      cursor = self.cursorexecute(sql)
      self.db.commit()
      return cursor
    except self.dberror:
      #import pdb
      #pdb.set_trace()
      self.dberrorrollback()
      self.errorhandler.logerror("sql error running query: " + str(sql) + ": " + self.errorhandler.exception_str())
      raise 

  def getaddcolumnsql(self, tablename, columnname, columntype):
    """returns the sql required to add a column of the given name and type to a table"""
    if self.DBTYPE == 'access':
      return "alter table %s add column %s %s" % (tablename, columnname, self.dbtypename(columntype))
    else:
      return "alter table %s add %s %s" % (tablename, columnname, self.dbtypename(columntype))

  def getdropcolumnsql(self, tablename, columnname):
    """returns the sql required to drop a column of the given name from a table"""
    # TODO: verify this works on each database...
    return "alter table %s drop column %s" % (tablename, columnname)
  
  def dbupperfn(self):
    """return a function that converts text to upper case"""
    if self.DBTYPE == 'access':
      return 'ucase'
    elif self.DBTYPE in ('sqlserver', 'oracle', 'postgres', 'mysql', 'sqlite'):
      return 'upper'
    else:
      raise ValueError, "unknown database type %r in dbupperfn" % (self.DBTYPE)

  def dblowerfn(self):
    """return a function that converts text to lower case"""
    if self.DBTYPE == 'access':
      return 'lcase'
    elif self.DBTYPE in ('sqlserver', 'oracle', 'postgres', 'mysql', 'sqlite'):
      return 'lower'
    else:
      raise ValueError, "unknown database type %r in dblowerfn" % (self.DBTYPE)

  def dbdateformatfn(self, expression, formatstr):
    """return an expression that formats the given expression with the given formatstr"""
    if self.DBTYPE == 'access':
      formatfnname = "format"
      dbdateformatsubst = dates.accessdateformatsubst
    elif self.DBTYPE == 'oracle':
      formatfnname = "to_char"
      dbdateformatsubst = dates.oracledateformatsubst
    elif self.DBTYPE == 'sqlserver':
      return dates.sqldateformatsubstfunction(expression, formatstr)
    elif self.DBTYPE == 'postgres':
      formatfnname = "to_char"
      dbdateformatsubst = dates.postgresdateformatsubst
    elif self.DBTYPE == 'mysql':
      formatfnname = "date_format"
      dbdateformatsubst = dates.mysqldateformatsubst
    elif self.DBTYPE == 'sqlite':
      raise NotImplementedError("SQLite does not support native date formatting")
    else:
      raise ValueError, "unknown database type %r in dblowerfn" % (self.DBTYPE)
    for key, value in dbdateformatsubst.iteritems():
      formatstr = formatstr.replace(key, value)
    formatstr = self.dbrepr(formatstr)
    return "%s(%s, %s)" % (formatfnname, expression, formatstr)

  def dbstrconcat(self, *strexprs):
    """returns an expression that concatenates all the string expressions in the list"""
    if self.DBTYPE == 'access':
      return " + ".join(strexprs)
    else:
      return " || ".join(strexprs)

  def dbstrequalityexpr(self, expr1, expr2):
    """return a sql expression that returns false if expr1 != expr2, true if expr1 == expr2
    note that expr1 and expr2 are sql expressions that are evaluated per row
    they must represent string values"""
    # most of these rely on a trick that multiplies substring indexes
    # only if expr1 == expr2 will both be a substring of the other
    if self.DBTYPE == 'access':
      return 'instr(%s, %s) * instr(%s, %s)' % (expr1, expr2, expr2, expr1)
    elif self.DBTYPE == 'sqlserver':
      return 'patindex(%s, %s) * patindex(%s, %s)' % (expr1, expr2, expr2, expr1)
    elif self.DBTYPE == 'oracle':
      return 'instr(%s, %s) * instr(%s, %s)' % (expr1, expr2, expr2, expr1)
    elif self.DBTYPE == 'postgres':
      return 'varchareq(%s, %s)' % (expr1, expr2)
    elif self.DBTYPE == 'mysql':
      return '(%s = %s)' % (expr1, expr2)
    elif self.DBTYPE == 'sqlite':
      return '%s == %s' % (expr1, expr2)
    else:
      raise ValueError, "unknown database type %r in dblowerfn" % (self.DBTYPE)

  def dbrepr(self, value, formattype = None, timeConvert=0):
    # currently, the griddisplayformat is used to format datetimestrings in logtable. It should NOT be
    #configured on string or text objects in categoryconf.
    
    if timeConvert == 1:    #Convert from server to client, for filtering
      totalConversionHours = self.UTCClient-self.UTCServer
    elif timeConvert == -1:   #Convert from client to server for insertion
      totalConversionHours = (self.UTCClient-self.UTCServer) * -1
    else:   #Don't convert
      totalConversionHours = 0
    if formattype is None or formattype == 'None': formattype = ''
    if value is None:
      return 'null'
    if isinstance(value, basestring) and formattype.lower() not in ('', 'attachment'):
      try:
        value = dates.parsedate(value, formattype)
        if value.year <= 1900:
          #strftime() (used somewhere down the line) doesn't like dates before 1900
          #Dates before 1900 probably aren't going to need timezone conversion anyway
          currentdate = dates.converttimezone(dates.currentdate(), totalConversionHours)
          value = value.replace(year=currentdate.year, month=currentdate.month, day=currentdate.day)
        value = dates.converttimezone(value, totalConversionHours)
      except:
        self.errorhandler.logerror("Error parsing date: value=%r, formattype=%r" % (value, formattype))
        raise
      return dates.dbdatestring(value, self.DBTYPE)
    elif type(value) == dates.date:
      value = dates.converttimezone(value, totalConversionHours)
      return dates.dbdatestring(value, self.DBTYPE)
    elif type(value).__name__ == 'DateTime':
      value = dates.converttimezone(value, totalConversionHours)
      return dates.dbdatestring(value, self.DBTYPE)
    elif type(value).__name__ == 'time':
      value = dates.converttimezone(value, totalConversionHours)
      return dates.dbdatestring(value, self.DBTYPE)
    # we know how to deal with basic strings...
    elif isinstance(value, str):
      return "'" + value.replace("'","''") + "'"
    elif isinstance(value, unicode):
      return "'" + value.replace("'","''") + "'"
    # we know how to deal with certain objects
    elif type(value) == types.InstanceType:
      if hasattr(value, 'dbrepr'):
        return value.dbrepr()
    elif isinstance(value, float):
      return repr(value)
    elif isinstance(value, int):
      return repr(value)
    elif isinstance(value, long):
      #we can convert a long to a string and sqlite will understand it
      if self.DBTYPE == 'sqlite':
        return "'%s'" % int(value)
      return repr(int(value))	# Try to convert a long to an int, so that databases can handle it
    elif isinstance(value, list):
      return self.dbrepr(self.encodelist(value, formattype), "")
    # otherwise try return repr(value) anyway
    self.errorhandler.logerror("unknown type in dbrepr: value=%r, type=%r" % (value, type(value)))
    return repr(value)

  def encodelist(self, value, formattype):
    """encodes the list as a comma-separated value"""
    # TODO: work out a cleaner way to handle this
    s = StringIO.StringIO()
    csvwriter = csv.writer(s)
    csvwriter.writerow(value)
    encoded = s.getvalue()
    if encoded.endswith("\n"): encoded = encoded[:-1]
    if encoded.endswith("\r"): encoded = encoded[:-1]
    return encoded

  def decodelist(self, value, format):
    """decodes the list from a comma-separated value"""
    csvreader = csv.reader([value])
    return csvreader.next()

  def insert(self, tablename, valuedict, formattypedict={}, timeConvert = 0): 
    """insert directly into a table, trap errors.
       typemap(key) is a function returning the formattype for the value...
    """
    values = []
    cols = []
    for key,value in valuedict.iteritems():
      col = key.upper()
      format = formattypedict.get(col, None)
      try:
        valuerepr = self.dbrepr(value, format, timeConvert)
      except Exception, e:
        raise ValueError("%s for key %r, value %r, format %r" % (e, key, value, format))
      values.append(valuerepr)
      cols.append(col)
    sql = "insert into "+tablename+"("+",".join(cols)+")"+" values("+",".join(values)+")"
    if isinstance(sql, unicode) and self.convert_unicode_sql: sql = sql.encode(self.encoding)
    try:
      cursor = self.cursorexecute(sql)
      self.clearcache([tablename])
      self.db.commit()
    except self.dberror:
      self.dberrorrollback()
      self.errorhandler.logerror("sql error in insert: "+tablename+", "+repr(valuedict)+": "\
        +"sql:"+sql+"\n"+self.errorhandler.exception_str())
      raise

  def update(self,tablename,keys,keyvalues,newvaluedict,formattypedict = {}, actiondict = {}, timeConvert = 0):
    """update directly into a table, trap errors.
       keys and keyvalues can either be single elements or sequences
    """
    if len(newvaluedict) == 0:
      # don't do anything if nothing is being changed...
      return
    updates = []
    for key, value in newvaluedict.iteritems():
      col = key.upper()
      valuerepr = self.dbrepr(value, formattypedict.get(col, None), timeConvert)
      action = actiondict.get(col, 'replace').lower()
      if action == 'replace':
        updates.append("%s=%s" % (key, valuerepr))
      elif action == 'append':
        # this is for appending to text fields...
        updates.append("%s=%s" % (key, self.dbstrconcat(key, "'\n'", valuerepr)))
      elif action == 'prepend':
        # this is for prepending to text fields...
        updates.append("%s=%s" % (key, self.dbstrconcat(valuerepr, "'\n'", key)))
      else:
        raise ValueError, "unknown action %r in update" % action
    sql = "update "+tablename+" set "+", ".join(updates)
    sql += " where " + self.multiequalsphrase(keys, keyvalues)
    if isinstance(sql, unicode) and self.convert_unicode_sql: sql = sql.encode(self.encoding)
    try:
      cursor = self.cursorexecute(sql)
      self.clearcache([tablename])
      self.db.commit()
    except self.dberror:
      self.dberrorrollback()
      self.errorhandler.logerror("sql error in update: "+tablename+", %r=%r"%(keys,keyvalues)+repr(newvaluedict)+": "\
        +"sql:"+sql+"\n"+self.errorhandler.exception_str())
      raise

  def delete(self,tablename,keys,keyvalues):
    """delete from a table, trap errors.
    """
    sql = "delete from "+tablename+" where "+self.multiequalsphrase(keys, keyvalues)
    if isinstance(sql, unicode) and self.convert_unicode_sql: sql = sql.encode(self.encoding)
    try:
      cursor = self.cursorexecute(sql)
      self.clearcache([tablename])
      self.db.commit()
    except self.dberror:
      self.dberrorrollback()
      self.errorhandler.logerror("sql error in delete: "+tablename+", %r=%r"%(keys,keyvalues)+": "\
        +"sql:"+sql+"\n"+self.errorhandler.exception_str())
      raise

  def _wrapreconnect(function):
    def safecall(*args, **kw):
      self = args[0]
      try:
        return apply(function, args, kw)
      except TypeError, e:
        # some database raises a TypeError on disconnection
        pass
      except self.dberror, e:
        unknownerror = False
        # unknown errors can be from database disconnection
        if hasattr(e, "args"):
          errorargs = e.args
          if isinstance(errorargs, tuple) and len(errorargs) == 4:
            if isinstance(errorargs[2], tuple) and len(errorargs[2]) == 6:
              hr, scode =  errorargs[0], errorargs[2][5]
              if hr == 0x80020009L and scode == 0x80004005L:
                unknownerror = True
        if not unknownerror:
          raise
      except:
        raise
      try:
        self.errorhandler.logtrace("caught error, attempting database reconnection: %s" % e)
        if hasattr(self.db, "isconnected"):
          self.errorhandler.logtrace("self.db.isconnected(): %s" % self.db.isconnected())
        self.dblogin()
        return apply(function, args, kw)
      except Exception, reconnecterror:
        self.errorhandler.logtrace("database reconnection failed: %s" % reconnecterror)
        raise e
    safecall.__doc__ = function.__doc__
    return safecall

  def _wraptimer(function):
    def timecall(self, *args, **kw):
      start_time = time.time()
      argstr = ", ".join([repr(arg) for arg in args]) + ", ".join(["%s=%r" % (kw, val) for kw, val in kw.iteritems()])
      # self.errorhandler.logtrace("about to call %s(%s)" % (function.__name__, argstr))
      result = function(self, *args, **kw)
      end_time = time.time()
      self.errorhandler.logtrace("call to %s(%s) took %0.2f seconds" % (function.__name__, argstr, end_time-start_time))
      return result
    timecall.__doc__ = function.__doc__
    return timecall

  # insert = _wraptimer(insert)
  # update = _wraptimer(update)
  # delete = _wraptimer(delete)
  # execute = _wraptimer(execute)
  # query = _wraptimer(query)

  cursorexecute = _wrapreconnect(cursorexecute)
 
  def runsql(self,sql):
    # TODO: this should be renamed to debug_printsql
    # to run a sql statement like insert / update, use execute
    # to run a query and get the results, use allrowdicts or other similar functions
    """run query sql and print out results"""
    dict = self.allrowdicts(sql)
    for row in dict:
      for field in row:
        print field + ":" + str(row[field]) + " ",
      print

  def decoderow(self, row):
    """decodes the row to unicode using the current encoding"""
    if self.DBTYPE == 'mysql':
      return row
    if not isinstance(row, list):
      row = [col for col in row]
    for colnum, col in enumerate(row):
      if isinstance(col, str):
        row[colnum] = col.decode(self.encoding)
    return row

  def singlerow(self, sql, withdescription=0):
    """runs sql and retrieves a single row"""
    cachedrow, description = self.getsinglerowcache(sql)
    if cachedrow is not None:
      cachedrow = self.fixdatetypes(cachedrow, description)
      cachedrow = self.timeConvert(cachedrow, description)
      if withdescription:
        return cachedrow, description
      return cachedrow
    t1 = time.time()
    cursor = self.query(sql)
    row = cursor.fetchone()
    # calculate stats...
    ms = (time.time() - t1) * 1000
    if sql not in self.sqlstats:
      self.sqlstats[sql] = timecache.timecache(300)
    self.sqlstats[sql][time.localtime(t1)] = (ms, None)
    # handle the result
    if row is None:
      # return None for each field
      row = [None] * len(cursor.description)
    row = self.decoderow(row)
    self.setsinglerowcache(sql, row, cursor.description)
    row = self.fixdatetypes(row, cursor.description)
    row = self.timeConvert(row, cursor.description)
    if withdescription:
      return row, cursor.description
    return row

  def singlevalue(self, sql):
    """runs sql and retrieves a single column from a single row"""
    row = self.singlerow(sql)
    return row[0]

  def allrows(self, sql, withdescription=0):
    """runs sql and retrieves all rows"""
    cachedrows, description = self.getallrowscache(sql)
    if cachedrows is not None:
      cachedrows = [self.fixdatetypes(cachedrow, description) for cachedrow in cachedrows]
      cachedrows = self.timeConvert(cachedrows, description)
      if withdescription:
        return cachedrows, description
      return cachedrows
    t1 = time.time()
    cursor = self.query(sql)
    rows = cursor.fetchall()
    # calculate stats...
    ms = (time.time() - t1) * 1000
    if sql not in self.sqlstats:
      self.sqlstats[sql] = timecache.timecache(300)
    self.sqlstats[sql][time.localtime(t1)] = (ms, len(rows))
    # handle the result
    rows = [self.decoderow(row) for row in rows]
    self.setallrowscache(sql, rows, cursor.description)
    rows = [self.fixdatetypes(row, cursor.description) for row in rows]
    rows = self.timeConvert(rows, cursor.description)
    if withdescription:
      return rows, cursor.description
    return rows

  def somerows(self, sql, minrows=None, maxrows=None, withdescription=0):
    """runs sql and retrieves some of the rows"""
    # note: since we can't skip rows using the Python DB-API, we just read them and discard...
    t1 = time.time()
    cursor = self.query(sql)
    if minrows is None and maxrows is None:
      rows = cursor.fetchall()
    elif minrows is None:
      rows = cursor.fetchmany(maxrows)
    elif maxrows is None:
      rows = cursor.fetchall()
      rows = rows[minrows:]
    else:
      rows = cursor.fetchmany(maxrows)
      rows = rows[minrows:]
    # calculate stats...
    ms = (time.time() - t1) * 1000
    if sql not in self.sqlstats:
      self.sqlstats[sql] = timecache.timecache(300)
    self.sqlstats[sql][time.localtime(t1)] = (ms, (minrows, maxrows))
    # handle the result
    rows = [self.decoderow(row) for row in rows]
    rows = [self.fixdatetypes(row, cursor.description) for row in rows]
    rows = self.timeConvert(rows, cursor.description)
    if withdescription:
      return rows, cursor.description
    return rows

  def singlerowdict(self, sql, keymap=None, valuemap=None):
    """runs sql, retrieves a row and converts it to a dictionary, using field names as keys
       mapping functions can be supplied for keys and values as keymap and valuemap"""
    row, description = self.singlerow(sql, 1)
    return self.row2dict(row, description, keymap, valuemap)

  def allrowdicts(self, sql, keymap=None, valuemap=None):
    """runs sql, retrieves all rows, converts to dictionaries, using field names as keys
       mapping functions can be supplied for keys and values as keymap and valuemap"""
    allrows, description = self.allrows(sql, 1)
    return [self.row2dict(row, description, keymap, valuemap) for row in allrows]

  def somerowdicts(self, sql, keymap=None, valuemap=None, minrow=None, maxrow=None):
    """runs sql, retrieves indicated rows, converts to dictionaries, using field names as keys
       mapping functions can be supplied for keys and values as keymap and valuemap"""
    somerows, description = self.somerows(sql, minrow, maxrow, 1)
    return [self.row2dict(row, description, keymap, valuemap) for row in somerows]

  def rows2dict(self, sql, keynamefield, valuefield, keymap=None, valuemap=None):
    """runs sql, converts cursor into a dictionary where each row of the cursor
       provides the keyname in one field (keynamefield), and the value in another field (valuefield)
       mapping functions can be supplied for keyfield values and valuefield values as keymap and valuemap
       note that keynamefield and valuefield will be used _after_ keymap has been applied
    """
    thisdict = {}
    manydicts = self.allrowdicts(sql, keymap, valuemap)
    for dict in manydicts:
      # we don't do the mapping again ; it's already done!
      thisdict[dict[keynamefield]] = dict[valuefield]
    return thisdict

  def equalsphrase(self, column, value):
    """returns an = phrase for a whereclause using dbrepr"""
    returnVal = column + "=" + self.dbrepr(value, timeConvert=1)
    return returnVal

  def multiequalsphrase(self, keys, keyvalues):
    if isinstance(keys, basestring):
      return self.equalsphrase(keys, keyvalues)
    else:
      if len(keys) == 1 and not isinstance(keyvalues, (tuple, list)):
        return self.equalsphrase(keys[0], keyvalues)
      else:
        if len(keys) != len(keyvalues):
          self.errorhandler.logtrace("multiequalsphrase: keys and keyvalues are of different lengths: %r, %r" % (keys, keyvalues))
        return " and ".join([self.equalsphrase(keys[n], keyvalues[n]) for n in range(len(keys))])

  def catclauses(self, clauselist, prefix="where"):
    """cat the clauses in the list into a string that can be used as a where clause"""
    validclauses = []
    for clause in clauselist:
      if clause is None: continue
      if isinstance(clause, list):
        clause = self.catclauses(clause, prefix=None)
      clause = clause.strip()
      if clause:
        validclauses.append("(" + clause + ")")
    if not validclauses:
      return " "
    else:
      combinedclause = " and ".join([clause for clause in validclauses]) + " "
      if prefix:
        combinedclause = " " + prefix + " " + combinedclause
      return combinedclause

  def fixdatetypes(self, row, description):
    # TODO: utilise this to do more type mappings? check if it would help
    if self.DBTYPE == 'postgres':
      # the PyGreSQL driver doesn't parse dates into objects, so we do it manually here...
      columntypes = [field[1] for field in description]
      if self.driver.DATETIME in columntypes:
        for i in range(len(description)):
          if columntypes[i] == self.driver.DATETIME:
            if isinstance(row[i], basestring):
              row[i] = dates.pgdateparser.parse(row[i])

    elif self.DBTYPE == 'sqlite':
      # parse dates into datetime objects
      columntypes = [field[1] for field in description]
      if self.driver.datetime in columntypes:
        for i in range(len(description)):
          if columntypes[i] == self.driver.datetime:
            value = row[i]
            if type(value).__name__ in ('time', 'Timestamp') and hasattr(value, 'year'):
              row[i] = dates.WinPyTimeToDate(value)

    elif self.DBTYPE != 'mysql':
      # parse dates into datetime objects
      columntypes = [field[1] for field in description]
      if self.driver.DATETIME in columntypes:
        for i in range(len(description)):
          if columntypes[i] == self.driver.DATETIME:
            value = row[i]
            if type(value).__name__ in ('time', 'Timestamp') and hasattr(value, 'year'):
              row[i] = dates.WinPyTimeToDate(value)
    return row

  def row2dict(self, row, description, keymap=None, valuemap=None):
    """converts a row to a dictionary, using field names as keys
       keys can be mapped through a function, keymap
       likewise values can be mapped through a function, valuemap
    """
    fieldnames = [field[0] for field in description]
    if keymap is None:
      if valuemap is None:
        dictresult = dict([(fieldnames[i],row[i]) for i in range(len(description))])
      else: # valuemap is not None
        dictresult = dict([(fieldnames[i],valuemap(row[i])) for i in range(len(description))])
    else: # keymap is not None
      if valuemap is None:
        dictresult = dict([(keymap(fieldnames[i]),row[i]) for i in range(len(description))])
      else: # valuemap is not None
        dictresult = dict([(keymap(fieldnames[i]),valuemap(row[i])) for i in range(len(description))])
    return dictresult

  def timeConvert(self, datadict, description):
    """shifts time between time zones"""
    if not isinstance(datadict, list) or self.UTCClient == self.UTCServer or not datadict:
      return datadict
    totalConversionHours = self.UTCClient-self.UTCServer
    singlerow = not isinstance(datadict[0], list)
    if singlerow:
      datadict = [datadict]
    columntypes = [field[1] for field in description]
    if self.driver.DATETIME in columntypes:
      # make a deep copy so we don't affect the cached datadict
      datadict = [row[:] for row in datadict]
      for i in range(len(description)):
        if columntypes[i] == self.driver.DATETIME:
          for row in datadict:
            datevalue = row[i]
            if isinstance(datevalue, (str, unicode)):
              datevalue = dates.pgdateparser.parse(datevalue)
            row[i] = dates.converttimezone(datevalue, totalConversionHours)
    if singlerow:
      return datadict[0]
    else:
      return datadict

  def listfieldnames(self,tablename):
      """returns a list of names of fields in tablename"""
      cursor = self.query("select * from %s where 1=0" % tablename)
      description = cursor.description
      return [field[0] for field in description]
      

# -*- coding: utf-8 -*-

"""PyADO: a Python Database API driver that wraps around Microsoft ADO
For Python DB-API Reference, see http://www.python.org/topics/database/DatabaseAPI-2.0.html
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

from ADOTypes import *
from ADOProviders import *
import os
import _PyADO

from threading import Lock
executeLock = Lock()

# TODO:
# --------------------------------------------------------------------
# Module              - paramstyle not yet determined
# Errors & Exceptions - still need to get done
# Connection Objects  - commit & rollback
# Cursor Objects      - description, rowcount, callproc, setinputsizes, setoutputsize
# Type Objects        - still need to get done (use mxDateTime)
# --------------------------------------------------------------------

CoInitialize = _PyADO.CoInitialize
CoInitializeEx = _PyADO.CoInitializeEx
error = _PyADO.error
COINIT_MULTITHREADED = _PyADO.COINIT_MULTITHREADED

def connect(dsn,user=None,password=None,host=None,database=None,provider=None,**kwargs):
    """Constructor for creating a connection to the database. Returns a Connection Object.
    
    It takes a number of parameters which are database dependent:
    dsn        Data source name as string
    user       User name as string (optional)
    password   Password as string (optional)
    host       Hostname (optional)
    database   Database name (optional)
    provider   OLE DB Provider name  (optional paramater, but required to work)"""
    NewConn = Connection()
    NewConn.connect(dsn,user=user,password=password,host=host,database=database,provider=provider,**kwargs)
    return NewConn

def create(dsn,user=None,password=None,host=None,database=None,provider=None):
    """Creates a new database (extension to DB-API). Returns a Connection object.
    
    It takes a number of parameters which are database dependent:
    dsn        Data source name as string
    user       User name as string (optional)
    password   Password as string (optional)
    host       Hostname (optional)
    database   Database name (optional)
    provider   OLE DB Provider name  (optional paramater, but required to work)"""
    NewConn = Connection()
    NewConn.create(dsn,user=user,password=password,host=host,database=database,provider=provider)
    return NewConn

# String constant stating the supported DB API level, currently 2.0
apilevel = '2.0'

# Integer constant stating the level of thread safety the interface supports.
threadsafety = 2  # Threads may share the module and connections. (guess)

# String constant stating the type of parameter marker formatting expected by the interface.
# since this is different for different providers, we need to work it out
paramstyle = 'pyformat'  # Python extended format codes, e.g. '...WHERE name=%(name)s'

# type objects. we can make these more complex later if neccessary
STRING = 1
BINARY = 2
NUMBER = 3
DATETIME = 4
ROWID = 5
UNKNOWN = 0 # we really shouldn't have this

class Connection:
    """PyADO Connection, follows DatabaseAPI-2.0
    
    __init__()
        Initialises the internal connection object using _PyADO
    connect(dsn,user,password,host,database,provider)
        open the connection. this is called from the connect function outside this class
      cursor()
        Return a new Cursor Object using the connection.
      close()
        Close the connection now (rather than whenever __del__ is called).
    commit() [not implemented]
         Commit any pending transaction to the database.
    rollback() [optional] [not implemented]
        Does a rollback."""

    def commit(self):
        """Commit any pending transaction to the database. [not implemented]"""
        pass

    def rollback(self):
        """Does a rollback. [not implemented]"""
        pass

    def __init__(self):
        """Initialises the internal connection object using _PyADO"""
        self.Conn = _PyADO.Connection()

    def isconnected(self):
        """non-DBAPI 2.0 function to check if the database is still connected"""
        return self.Conn.State == 1

    def connect(self, dsn,user=None,password=None,host=None,database=None,provider=None,**kwargs):
        """open the connection. this is called from the connect function outside this class"""
        # create if required...
        createdb = kwargs.get("DBCREATE", False)
        if createdb == "ifmissing":
          createdb = provider == AccessProvider and not os.path.exists(database)
          print "checking if database exists:", provider, database, createdb
        if createdb:
          return self.create(dsn, user=user,password=password, host=host, database=database, provider=provider, **kwargs)

        # currently don't do anything with dsn

        # check it's not already open
        if self.Conn.State == 1: self.Conn.Close()

          # Make connection with the given parameters. provider should be required
        if (provider <> None): self.Conn.Provider = str(provider)
        sqlserver = 0
        if (host <> None):
            # using SQL Server-style with Data Source=host and Initial Catalog=database
            try:
                if (database <> None): self.Conn.Properties("Initial Catalog").Value =  str(database)
                sqlserver = 1
            except _PyADO.pythoncom.com_error:
                # This error can happen because we're dealing with MySQL, not SQL Server
                pass
            if sqlserver:
                self.Conn.Properties("Data Source").Value = str(host)
            else:
                # Using MySQL-style with Data Source=database and Location=host
                self.Conn.Properties("Data Source").Value = str(database)
                self.Conn.Properties("Location").Value = str(host)
        else:
            # using Oracle-style with no host, Data Source=database
            if (database <> None): self.Conn.Properties("Data Source").Value = str(database)
        if (user <> None): self.Conn.Properties("User ID").Value = str(user)
        if (password <> None): self.Conn.Properties("Password").Value = str(password)
        for key, value in kwargs.iteritems():
          if (value <> None): setattr(self.Conn, key, str(value))

        # open the database (pass database, username and password again)
        if (sqlserver):
            # using SQL Server-style with Data Source=host and Initial Catalog=database
            self.Conn.Open(host,user,password)
        else:
            # using Oracle-style with no host, Data Source=database
            self.Conn.Open(database,user,password)

        # check whether it was Connected
        isConnected = (self.Conn.State == 1)
        # return whether this succeeded
        return isConnected

    def create(self, dsn,user=None,password=None,host=None,database=None,provider=None,**kwargs):
        """create a new database. this is called from the connect function outside this class"""
        # check it's not already open
        if self.Conn.State == 1: self.Conn.Close()
        catalog = _PyADO.Catalog()
        dsnparts = []
        # Make DSN with the given parameters. provider should be required
        if (provider <> None): dsnparts.append("Provider=%s" % str(provider))
        if (host <> None):
            # using SQL Server-style with Data Source=host and Initial Catalog=database
            dsnparts.append("Data Source=%s" % str(host))
            if (database <> None): dsnparts.append("Initial Catalog=%s" % str(database))
        else:
            # using Oracle-style with no host, Data Source=database
            if (database <> None): dsnparts.append("Data Source=%s" % str(database))
        # TODO: work out how to handle User ID and password...
        # if (user <> None): dsnparts.append("User ID=%s" % str(user))
        # if (password <> None): dsnparts.append("Password=%s" % str(password))
        for key, value in kwargs.iteritems():
          if key in "DBCREATE": continue
          if (value <> None): dsnparts.append("%s=%s" % (key, str(value)))
        if dsn:
          dsn = ";".join([dsn] + dsnparts)
        else:
          dsn = ";".join(dsnparts)
        print "creating database with dsn", dsn
        self.Conn = catalog.Create(dsn)

        # check whether it was Connected
        isConnected = (self.Conn.State == 1)
        # return whether this succeeded
        return isConnected

    def cursor(self):
        """Return a new Cursor Object using the connection."""
        return Cursor(self.Conn)

    def close(self):
        """Close the connection now (rather than whenever __del__ is called).
        The connection will be unusable from this point forward;
        an Error (or subclass) exception will be raised
        if any operation is attempted with the connection.
        The same applies to all cursor objects trying to use the connection."""

        self.Conn.Close()

fieldtypecodes = { \
  adBigInt: NUMBER,            # An 8-byte signed integer (DBTYPE_I8).
  adBinary: BINARY,            # A binary value (DBTYPE_BYTES).
  adBoolean: NUMBER,           # A Boolean value (DBTYPE_BOOL).
  adBSTR: STRING,              # A null-terminated character string (Unicode) (DBTYPE_BSTR).
  adChar: STRING,              # A String value (DBTYPE_STR).
  adCurrency: NUMBER,          # A currency value (DBTYPE_CY). 
# Currency is a fixed-point number with four digits to the right of the decimal point. 
# It is stored in an 8-byte signed integer scaled by 10,000.
  adDate: DATETIME,            # A Date value (DBTYPE_DATE). 
# A date is stored as a Double, the whole part of which 
# is the number of days since December 30, 1899, 
# and the fractional part of which is the fraction of a day.
  adDBDate: DATETIME,          # A date value (yyyymmdd) (DBTYPE_DBDATE).
  adDBTime: DATETIME,          # A time value (hhmmss) (DBTYPE_DBTIME).
  adDBTimeStamp: DATETIME,     # A date-time stamp (yyyymmddhhmmss + billionths/s) (DBTYPE_DBTIMESTAMP).
  adDecimal: NUMBER,           # An exact numeric value with a fixed precision and scale (DBTYPE_DECIMAL).
  adDouble: NUMBER,            # A double-precision floating point value (DBTYPE_R8).
  adEmpty: UNKNOWN,            # I HAVE NO IDEA
                               # No value was specified (DBTYPE_EMPTY).
  adError: UNKNOWN,            # I HAVE NO IDEA
                               # A 32-bit error code (DBTYPE_ERROR).
  adGUID: BINARY,              # THINK ABOUT THIS
                               # A globally unique identifier (GUID) (DBTYPE_GUID).
  adIDispatch: BINARY,         # THINK ABOUT THIS
                               # A pointer to an IDispatch interface on an OLE object (DBTYPE_IDISPATCH).
  adInteger: NUMBER,           # A 4-byte signed integer (DBTYPE_I4).
  adIUnknown: BINARY,          # THINK ABOUT THIS
                               # A pointer to an IUnknown interface on an OLE object (DBTYPE_IUNKNOWN).
  adLongVarBinary: BINARY,     # A long binary value (Parameter object only).
  adLongVarChar: STRING,       # A long String value (Parameter object only).
  adLongVarWChar: STRING,      # A long null-terminated string value (Parameter object only).
  adNumeric: NUMBER,           # An exact numeric value with a fixed precision and scale (DBTYPE_NUMERIC).
  adSingle: NUMBER,            # A single-precision floating point value (DBTYPE_R4).
  adSmallInt: NUMBER,          # A 2-byte signed integer (DBTYPE_I2).
  adTinyInt: NUMBER,           # A 1-byte signed integer (DBTYPE_I1).
  adUnsignedBigInt: NUMBER,    # An 8-byte unsigned integer (DBTYPE_UI8). 
  adUnsignedInt: NUMBER,       # A 4-byte unsigned integer (DBTYPE_UI4). 
  adUnsignedSmallInt: NUMBER,  # A 2-byte unsigned integer (DBTYPE_UI2). 
  adUnsignedTinyInt: NUMBER,   # A 1-byte unsigned integer (DBTYPE_UI1). 
  adUserDefined: UNKNOWN,      # THINK ABOUT THIS
                               # A user-defined variable (DBTYPE_UDT). 
  adVarBinary: BINARY,         # A binary value (Parameter object only).
  adVarChar: STRING,           # A String value (Parameter object only). 
  adVariant: UNKNOWN,          # An Automation Variant (DBTYPE_VARIANT). 
  adVarWChar: STRING,          # A null-terminated Unicode character string (Parameter object only). 
  adWChar: STRING              # A null-terminated Unicode character string (DBTYPE_WSTR). 
}

class Cursor:
    """PyADO cursor, which is used to manage the context of a fetch operation (DatabaseAPI-2.0)

    __init__(self, Conn)                constructor
    description                         sequence of column descriptions
    rowcount                            number of rows produced/affected by last executeXXX    [not implemented]
    callproc(procname[,parameters])     Call a stored database procedure with the given name   [optional] [not implemented]
    close()                             Close the cursor now (rather than whenever __del__ is called).
    execute(operation[,parameters])     Prepare and execute a database operation (query or command). [parameters not implemented]
    executemany(operation,seq_of_parameters) Execute multiple operations                      [optional]
    fetchone()                          Fetch next row of a query result set, return a single sequence
    fetchmany([size=cursor.arraysize])  Fetch the next set of rows of a query result, returning sequence of sequences
    fetchall()                          Fetch all remaining rows of a query result, returning sequence of sequences
    nextset()                           Skip to next result set                                [optional]
    arraysize                           number of rows to fetch with fetchmany. default 1
    setinputsizes(sizes)                used before a executeXXX() to predefine memory areas   [not implemented]
    setoutputsize(size[,column])        used before executeXXX() to set column buffer size     [not implemented]
    """
    def __init__(self, Conn):
        """Initialises the internal Recordset object from the Connection using _PyADO"""
        self.arraysize = 1
        self.PassConn = Conn
        self.rs = None
        self.Fields = None
        self.rsList = []
        self.rsListPos = 0
        self.description = []

    def execute(self, operation, parameters=None):
        """Prepare and execute a database operation (query or command).
        Parameters may be provided as sequence or mapping
        and will be bound to variables in the operation."""
        self.rs = None
        self.rsList = []
        self.rsListPos = 0
        if parameters is None:
            Query = operation
        else:
            Query = operation % parameters
        executeLock.acquire()
        try:
          try:
            command = _PyADO.Command()
            command.CommandText = operation
            if hasattr(self.PassConn, "CommandTimeout"):
              command.CommandTimeout = self.PassConn.CommandTimeout
            command.ActiveConnection = self.PassConn
            self.rs = command.Execute()
            self.rsList = [self.rs]
            self.rsListPos = 0
          except _PyADO.error, adoerror:
            try:
                hr, msg, exc, arg = adoerror
                if hr < 0:
                  hr = long(hr) + 0x100000000L
                if exc is None:
                  wcode, source, text, helpFile, helpId, scode = None, None, None, None, None, None
                else:
                  wcode, source, text, helpFile, helpId, scode = exc
                  if text is None:
                    text = _PyADO.pythoncom.GetScodeString(scode)
                  if scode < 0:
                    scode = long(scode) + 0x100000000L
                  if scode in _PyADO.errordict:
                    if text:
                      text += "\n" + _PyADO.errordict[scode]
                    else:
                      text = _PyADO.errordict[scode]
                  exc = wcode, source, text, helpFile, helpId, scode
                adoerror = _PyADO.error(hr, msg, exc, adoerror)
            except Exception, errorerror:
                raise adoerror
            raise adoerror
        finally:
          executeLock.release()
        # cache the fields. this must be done before describefields
        rsFields = self.rs.Fields
        if not hasattr(rsFields, "Count"):
          self.Fields = []
        else:
          self.Fields = [rsFields.Item(col) for col in range(rsFields.Count)] 
        # now describe the results
        self.description = self.describefields()

    def describefields(self):
        """Describes all the fields in the rowset.
        Returns a value which is assigned to self.description in execute"""
        description = []
        for col in range(len(self.Fields)):
            field = self.Fields[col]
            name = field.Name
            fieldtype = field.Type
            # options are STRING BINARY NUMBER DATETIME ROWID
            # we need to get rid of UNKNOWNs
            # the comments are from the ADO docs
            if fieldtype & adArray: # don't know what to do with arrays.
                # Joined in a logical OR together with another type to indicate
                # that the data is a safe-array of that type (DBTYPE_ARRAY).
                fieldtype = fieldtype & (~adArray)
            if fieldtype & adByRef: # get rid of this
                # Joined in a logical OR together with another type to indicate
                # that the data is a pointer to data of the other type (DBTYPE_BYREF).
                fieldtype = fieldtype & (~adByRef)
            if fieldtype == adVector: # don't know what to do with arrays.
                # Joined in a logical OR together with another type to indicate
                # that the data is a DBVECTOR structure, as defined by OLE DB,
                # that contains a count of elements
                # and a pointer to data of the other type (DBTYPE_VECTOR).
                fieldtype = fieldtype & (~adVector) 
            type_code = fieldtypecodes.get(fieldtype, UNKNOWN)
            internal_size = field.DefinedSize
            # this may sometimes fail, for example, if there is no record...
            try: 
              display_size = field.ActualSize
            except:
              # pretend it's what it's defined to be - best guess...
              display_size = internal_size
            precision = field.Precision
            try:
              scale = field.NumericScale
            except:
              # guess if error...
              scale = 0
            null_ok = field.Attributes & adFldMayBeNull
            # add this column to the description list
            description.append((name,type_code,display_size,internal_size,
                  precision,scale,null_ok))
        # return the list of all descriptions
        return description

    def close(self):
        """Close the cursor now (rather than whenever __del__ is called)."""
        # if called before Execute, will fail        
        self.rs.Close()

    def fetchone(self):
        """Fetch the next row of a query result set, returning a single sequence, or None when no more data is available"""
        # if called before Execute, will fail        
        if self.rs.EOF: return None
        row = [] 
        for col in range(len(self.Fields)):
            fieldvalue = self.Fields[col].Value
            row.append(fieldvalue)
        self.rs.MoveNext()
        return row

    def fetchall(self):
        """Fetch all (remaining) rows of a query result, returning them as a sequence of sequences (e.g. a list of tuples)."""
        # if called before Execute, will fail        
        rows = []
        # if we're at the end of the recordset, simply return the rows we have so far
        while not self.rs.EOF:
            # fetch the values for this row, and add the row to the list
            row = []
            for col in range(len(self.Fields)):
                value = self.Fields[col].Value
                row.append(value)
            rows.append(row)
            self.rs.MoveNext()
        return rows

    def fetchmany(self, size=None):
        """Fetch the next set of rows of a query result, returning a sequence of sequences (e.g. a list of tuples).
        An empty sequence is returned when no more rows are available."""
        # if called before Execute, will fail        
        if size == None: size = self.arraysize
        rows = []
        for rownumber in range(size):
            # if we're at the end of the recordset, simply return the rows we have so far
            if self.rs.EOF:
                return rows
            # fetch the values for this row, and add the row to the list
            row = []
            for col in range(len(self.Fields)):
                row.append(self.Fields[col].Value)
            rows.append(row)
            self.rs.MoveNext()
        return rows

    def executemany(self, operation, parameters=None):
        """Execute operation (query or command) against all parameter sequences or mappings
        found in the sequence seq_of_parameters."""
        size = len(parameters)
        self.rsList = []
        self.rsListPos = 0
        for rownumber in range(size):
            rs = _PyADO.Recordset()
            Query = operation % parameters[rownumber]
            executeLock.acquire()
            try:
              rs.Open(Query, ActiveConnection = self.PassConn)
            finally:
              executeLock.release()
            self.rsList.append(rs)
        self.rs = self.rsList[0]
        # cache the fields. this must be done before describefields
        rsFields = self.rs.Fields
        self.Fields = [rsFields.Item(col) for col in range(rsFields.Count)] 
        # initialize the description for the first rowset
        self.description = self.describefields()

    def nextset(self):
        """make the cursor skip to the next available set,
        discarding any remaining rows from the current set.
        If there are no more sets, returns None. Otherwise, returns true"""
        self.rsListPos += 1
        if self.rsListPos >= len(self.rsList):
            return None
        self.rs = self.rsList[self.rsListPos]
        # cache the fields. this must be done before describefields
        rsFields = self.rs.Fields
        self.Fields = [rsFields.Item(col) for col in range(rsFields.Count)] 
        # redo the description as this rowset might be different
        self.description = self.describefields()
        return 1
        # do we need this? in case it closes down?
        # if self.rs.State == 0: self.rs.Open()

    def getrowcount(self):
        # if called before Execute, will fail
        if self.rs.State == 0:
            executeLock.acquire()
            try:
              self.rs.Open()
            finally:
              executeLock.release()
            ret = self.rs.RecordCount
            self.rs.Close()
            return ret
        if self.rs.State != 0:
            return self.rs.RecordCount

    def __getattr__(self, Name):
        """Override the attribute rowcount, so we can have a read-only attribute that calls a procedure"""
        if Name in self.__dict__:
            return self.__dict__[Name]
        elif Name == 'rowcount':
            return self.getrowcount()

#Testing
def testcase(dsn,user=None,password=None,host=None,database=None,provider=None,sql=None, sqlBase=None, sqlParam=None):
    theConnection = connect(dsn,user=user,password=password,host=host,database=database,provider=provider)
    theCursor = theConnection.cursor()
    print "Execute Test:"
    theCursor.execute(sql)
    print theCursor.fetchone()
    print theCursor.fetchmany(100)
    print theCursor.fetchall()
    print theCursor.rowcount
    print "Executemany Test (list of parameters):"
    theCursor.executemany(sqlBase, sqlParam)
    while 1:
        print theCursor.fetchall()
        if theCursor.nextset() is None: break
    theCursor.close()
    theConnection.close()

def speedtest():
    import time
    import ADOProviders
    start = time.time()
    conn = connect(None, user="ameriven", password="ameriven", host="", provider=ADOProviders.OracleProvider)
    curs = conn.cursor()
    connected = time.time()
    curs.execute("select * from categorylists")
    executed1 = time.time()
    curs.fetchall()
    fetched1 = time.time()
    curs.execute("select * from categorylists")
    executed2 = time.time()
    curs.fetchall()
    fetched2 = time.time()
    conn.close()
    print """connect:   %0.3f
executed1: %0.3f
fetched1:  %0.3f
executed2: %0.3f
fetched2:  %0.3f""" % (-start+connected, -connected+executed1, -executed1+fetched1, -fetched1+executed2, -executed2+fetched2)

if __name__ == '__main__':
    import sys
    if '--speedtest' in sys.argv:
        speedtest()
        sys.exit()
    #database = 'C:\\Documents and Settings\\Administrator\\Desktop\\db1.mdb'    
    #sql = 'select * from jobs'
    #sqlBase = 'select * from %(tablename)s'
    #sqlParam = [{'tablename':'jobs'}, {'tablename':'runs'}]
    database = "D:\\Projects\\jSuiteAccess.mdb"
    sql = "select logtime,value001,quality001,value003,quality003,value005 from onesec"
    sqlBase = 'select count(*) from %(tablename)s'
    sqlParam = [{'tablename':'tag_storage_defs'}, {'tablename':'tag_ticker_cols'}, {'tablename':'onesec'}]
    testcase(dsn='dummy', user='Admin', password='',database=database, provider='Microsoft.Jet.OLEDB.4.0', sql=sql, sqlBase=sqlBase, sqlParam=sqlParam)


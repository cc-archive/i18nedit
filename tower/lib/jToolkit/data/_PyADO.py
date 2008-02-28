# -*- coding: utf-8 -*-

"""PyADO: a Python Database API driver that wraps around Microsoft ADO
For Python DB-API Reference, see http://www.python.org/topics/database/DatabaseAPI-2.0.html
_PyADO is a module that wraps the COM calls to speed them up
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

import pythoncom
import win32com.client
import imp
import os.path

def WriteADODBModule(classname, pyclassfile):
  from win32com.client import makepy
  makepy.GenerateFromTypeLibSpec(classname, pyclassfile, progressInstance=makepy.SimpleProgress(0))
  return pyclassfile

def ImportADODBFile(modulefilename):
  if not os.path.exists(modulefilename):
    return None
  try:
    ADODB = imp.load_module("jToolkit.data.ADODB", open(modulefilename, 'U'), modulefilename, (".py", "U", imp.PY_SOURCE))
  except ImportError:
    return None
  return ADODB

def ImportADODB():
  try:
    from jToolkit.data import ADODB
  except ImportError:
    ADODB = None
  if ADODB is None:
    try:
      ADODB = ImportADODBFile("ADODB.py")
    except ImportError:
      ADODB = None
  return ADODB

def CreateADODBModule():
  # get version from test connection
  print "creating jToolkit.data.ADODB class library to speed up database operations..."
  conn = win32com.client.Dispatch("ADODB.Connection")
  version = str(conn.Version).rstrip("0")
  # TODO: work out a real way to determine the Type Library name...
  classname = "Microsoft ActiveX Data Objects %s Library" % version
  if os.path.exists(__file__):
    pyclassfilename = os.path.join(os.path.dirname(__file__), 'ADODB.py')
  else:
    pyclassfilename = 'ADODB.py'
  pyclassfile = open(pyclassfilename, 'w')
  print "creating %s for %s" % (pyclassfilename, classname)
  WriteADODBModule(classname, pyclassfile)
  pyclassfile.close()
  if not os.path.getsize(pyclassfilename):
    print "ADO class creation unsuccessful... removing"
    os.remove(pyclassfilename)
  ADODB = ImportADODB()
  if ADODB is None:
    print "could not import ADODB module even after attempted recreation: running slowly..."
  return ADODB

# equivalent of 'from jToolkit.data import ADODB' but handle creation of the module too
ADODB = ImportADODB()
if ADODB is not None:
  if not hasattr(ADODB, "Connection"):
    print "Connection not found in jToolkit.data.ADODB: remove %s to recreate it" % ADODB.__file__
    ADODB = None
if ADODB is None:
  ADODB = CreateADODBModule()

CoInitialize = win32com.client.pythoncom.CoInitialize
CoInitializeEx = win32com.client.pythoncom.CoInitializeEx
error = pythoncom.error
COINIT_MULTITHREADED = 0

def ConvertErrorHeaders(errorheaders):
  result = []
  errors = []
  predefcomments = []
  for line in errorheaders.split("\n"):
    if not line.strip():
      result.append(line)
      predefcomments = []
    elif line.startswith("//"):
      comment = line.replace("//", "", 1)
      result.append("#" + comment)
      predefcomments.append(comment)
    elif line.startswith("#define"):
      parts = line.split()
      varname = parts[1]
      definition = " ".join(parts[2:])
      if definition.startswith("(") and definition.endswith(")"):
        definition = definition[1:-1]
      if definition.startswith("(HRESULT)"):
        definition = definition.replace("(HRESULT)", "", 1)
      if definition.startswith("0x") and definition.endswith("L"):
        errcode = eval(definition)
        errors.append((varname, predefcomments))
      else:
        definition = '"' + definition.replace('"', '\\"') + '"'
      result.append("%s = %s" % (varname, definition))
      predefcomments = []
  result.append("")
  result.append("errors = {")
  for varname, predefcomments in errors:
    result.append("  %s: %r," % (varname, varname + ":\n" + "\n".join(predefcomments)))
  result.append("}")
  return "\n".join(result)

def ConvertErrorHeaderFile(CHeaderFileName, PyHeaderFileName):
  try:
    CHeaderFile = open(CHeaderFileName, "r")
    pyerrors = ConvertErrorHeaders(CHeaderFile.read())
    PyHeaderFile = open(PyHeaderFileName, "w")
    PyHeaderFile.write(pyerrors)
    from jToolkit.data import oledberr
    return oledberr
  except Exception, e:
    print "exception converting error headers", e
    return None

try:
  from jToolkit.data import oledberr
except ImportError:
  __filedir__ = os.path.dirname(__file__)
  __oledberrh__ = os.path.join(__filedir__, "OLEDBERR.H")
  if os.path.exists(__oledberrh__):
    oledberr = ConvertErrorHeaderFile(__oledberrh__, os.path.join(__filedir__, "oledberr.py"))
  else:
    oledberr = None
if oledberr is None:
  errordict = {}
else:
  errordict = oledberr.errors

class ConnectionProperty(object):
  def __init__(self, Property):
    self.Property = Property
  def getValue(self):
    return self.Property.Value
  def setValue(self, newValue):
    self.Property.Value = newValue
  Value = property(getValue, setValue)

class Catalog(object):
  def __init__(self):
    self.Catalog = win32com.client.Dispatch("ADOX.Catalog")
  def Create(self, dsn):
    Conn = self.Catalog.Create(dsn)
    return Connection(Conn)

class Connection(object):
  def __init__(self, Conn=None):
    if Conn:
      self.Conn = Conn
      return
    try:
      if ADODB:
        self.Conn = ADODB.Connection()
      else:
        self.Conn = win32com.client.Dispatch("ADODB.Connection")
    except win32com.client.pythoncom.com_error, com_error:
      if com_error.args[0] == 0x800401f0L:
        # this is the COM not initialized problem
        raise WindowsError("COM not initialized")
      else:
        raise
  def Open(self, datasource, user, passwd):
    return self.Conn.Open(datasource, user, passwd)
  def Close(self):
    return self.Conn.Close()
  def getState(self):
    return self.Conn.State
  def getProvider(self):
    return self.Conn.Provider
  def setProvider(self, newProvider):
    self.Conn.Provider = newProvider
  def Properties(self, name):
    return ConnectionProperty(self.Conn.Properties(name))
  State = property(getState)
  Provider = property(getProvider, setProvider)

class RecordsetField(object):
  def __init__(self, Field):
    self.Field = Field
  def getValue(self):         return self.Field.Value
  def getName(self):          return self.Field.Name
  def getType(self):          return self.Field.Type
  def getDefinedSize(self):   return self.Field.DefinedSize
  def getActualSize(self):    return self.Field.ActualSize
  def getPrecision(self):     return self.Field.Precision
  def getNumericScale(self):  return self.Field.NumericScale
  def getAttributes(self):    return self.Field.Attributes
  Value = property(getValue)
  Name = property(getName)
  Type = property(getType)
  DefinedSize = property(getDefinedSize)
  ActualSize = property(getActualSize)
  Precision = property(getPrecision)
  NumericScale = property(getNumericScale)
  Attributes = property(getAttributes)

class RecordsetFields(object):
  def __init__(self, Fields):
    self.Fields = Fields
  def getCount(self):
    return self.Fields.Count
  def Item(self, col):
    return RecordsetField(self.Fields.Item(col))
  Count = property(getCount)

class Recordset(object):
  def __init__(self):
    if ADODB:
      self.rs = ADODB.Recordset()
    else:
      self.rs = win32com.client.Dispatch("ADODB.Recordset")
  def Open(self, operation, ActiveConnection):
    return self.rs.Open(operation, ActiveConnection.Conn)
  def Close(self):
    return self.rs.Close()
  def MoveNext(self):
    return self.rs.MoveNext()
  def getEOF(self):
    return self.rs.EOF
  def getRecordCount(self):
    return self.rs.RecordCount
  def getFields(self):
    return RecordsetFields(self.rs.Fields)
  EOF = property(getEOF)
  RecordCount = property(getRecordCount)
  Fields = property(getFields)

class Command(object):
  def __init__(self):
    if ADODB:
      self.command = ADODB.Command()
    else:
      self.command = win32com.client.Dispatch("ADODB.Command")
  def Cancel(self):
    return self.command.Cancel()
  def Execute(self):
    rowset, result = self.command.Execute()
    return rowset
  def getActiveConnection(self):
    return self.command.ActiveConnection
  def setActiveConnection(self, Connection):
    self.command.ActiveConnection = Connection.Conn
  def getCommandText(self):
    return self.command.CommandText
  def setCommandText(self, commandtext):
    self.command.CommandText = commandtext
  def getCommandTimeout(self):
    return self.command.CommandTimeout
  def setCommandTimeout(self, commandtimeout):
    self.command.CommandTimeout = commandtimeout
  ActiveConnection = property(getActiveConnection, setActiveConnection)
  CommandText = property(getCommandText, setCommandText)
  CommandTimeout = property(getCommandTimeout, setCommandTimeout)


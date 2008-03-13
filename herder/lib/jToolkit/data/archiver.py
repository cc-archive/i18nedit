# -*- coding: utf-8 -*-

# This file provides classes for exporting and importing database information
# into/from XML

from jToolkit.data import database
from jToolkit.data import dates
from jToolkit import prefs
from jToolkit import errors
import os
import sys
from jToolkit import serviceerrors
from elementtree import ElementTree
from cStringIO import StringIO
from xml.dom import minidom
import zipfile

def toupper(value):
  return value.upper()

def ConvertValue(value, typename=None):
    if value == 'None' or value is None:
        return None
    if typename == "string":
        return value
    if typename == "integer":
        return int(value)
    if typename == "float":
        return float(value)
    if typename == "datetime":
        return dates.parsedate(value, '%m/%d/%y %H:%M:%S')
    if value.startswith("-"):
        noneg = value[1:]
    else:
        noneg = value
    if noneg.isdigit():
        return int(value)
    if noneg.lower() == "1.#qnan" or noneg.lower() == "1.#inf" or noneg.lower() == "1.#ind":
        return None
    pfloat = noneg.split('.')
    if len(pfloat) == 2 and pfloat[0].isdigit() and pfloat[1].isdigit():
      return float(value)
    try:
      date = dates.parsedate(value, '%m/%d/%y %H:%M:%S')
      return date
    except dates.ParseError, dates.TypeError:
      pass
    
    return value


def FindDateFromPeriod(number, units):
    """This function subtracts a period from the current date and returns it"""
    currentdate = dates.currentdate()

    if units == 'minutes':
        specDate = currentdate - dates.datetimedelta(minutes = number)
    elif units == 'hours':
        specDate = currentdate - dates.datetimedelta(hours = number)
    elif units == 'days':
        specDate = currentdate - dates.datetimedelta(days = number)
    elif units == 'months':
        years = number / 12
        months = number % 12
        if currentdate.month - months < 1:
            years = years + 1
            months = months - 12
        specDate = currentdate.replace(year = currentdate.year - years, month = currentdate.month - months)
    elif units == 'years' or units == "":
        specDate = currentdate.replace(year = currentdate.year - number)
    else:
        raise ValueError("Invalid units specification: %d %s" % (number, units))

    return specDate            

def unzipAndParse(filename):
    """Takes a zipped filename, returns an XML Tree"""
    zipFile = zipfile.ZipFile(filename, compression=zipfile.ZIP_DEFLATED)
    contents = zipFile.read(os.path.basename(filename[:-4]))
    zipFile.close()
    return ElementTree.parse(StringIO(contents))

xmlns_dt = "uuid:C2F41010-65B3-11d1-A29F-00AA00C14882"
xmlns_rs = "urn:schemas-microsoft-com:rowset"
xmlns_s = "uuid:BDC6E3F0-6DA3-11d1-A2A3-00AA00C14882"
xmlns_z = "#RowsetSchema"
typemap = {'int':'number','float':'double','dateTime':'datetime','string':'string'}

class TableExporter:
    def __init__(self, errorhandler=None):
        """constructs the jHistExporter..."""
        if errorhandler is None:
            self.errorhandler = errors.ConsoleErrorHandler()
        else:
            self.errorhandler = errorhandler

        #Get the config
        self.defaultprefsfile, self.prefsfilename = self.getprefsfilenames()
                  
        self.InitialiseConfig()
        self.CreateErrorHandlers()
        self.LoadDatabaseConfig()

        # set up the list of changed files
        self.ChangedFiles = []

    def InitialiseConfig(self):
        self.config = prefs.PrefsParser()
        self.errorhandler.logtrace("Reading default preferences from "+self.defaultprefsfile)
        self.config.parsefile(self.defaultprefsfile)
        if os.path.exists(self.prefsfilename):
            self.errorhandler.logtrace("Reading preferences from "+self.prefsfilename)
            self.config.parsefile(self.prefsfilename)

    def CreateErrorHandlers(self):
        errorhandlers = [self.errorhandler]
        if hasattr(self.config, "mailerrors"):
            if not hasattr(self, "transfer"):
                self.errorhandler.logerror("Mail error reporting not supported without Transfer server")
            else:
                self.mailerrorhandler = serviceerrors.ForwardMailErrorHandler(self.config.mailerrors, transferAgent=self.transfer)
                errorhandlers.append(self.mailerrorhandler)
        if hasattr(self.config, "fileerrors"):
            self.fileerrorhandler = errors.ErrorHandler(self.config.fileerrors)
            errorhandlers.append(self.fileerrorhandler)
        self.errorhandler = errors.TeeErrorHandler(*errorhandlers)

    def LoadDatabaseConfig(self): 
        DatabaseConfig = self.GetDatabaseConfigInfo()
        #Set the date formatting text
        # FIXME: Replace this with dbdateformatfn
        if DatabaseConfig.DBTYPE == 'access':
            self.dateformatstr = "format(logtime, 'YYYYMMDD')"
            self.datetimeformatstr = "format(logtime, 'YYYYMMDD_HH')"
        elif DatabaseConfig.DBTYPE == 'sqlserver':
            self.dateformatstr = "convert(char(8), logtime, 112)"
            self.datetimeformatstr = "convert(char(8), logtime, 112)+'_'+convert(char(2), logtime, 8)"
        elif DatabaseConfig.DBTYPE in ['oracle','postgres']:
            self.dateformatstr = "to_char(logtime, 'YYYYMMDD')"
            self.datetimeformatstr = "to_char(logtime, 'YYYYMMDD_HH24')"
        elif DatabaseConfig.DBTYPE == 'mysql':
            self.dateformatstr = "DATE_FORMAT(logtime, '%Y%m%d')"
            self.datetimeformatstr = "DATE_FORMAT(logtime, '%Y%m%d_%H')"
        try:
            self.db = database.dbwrapper(DatabaseConfig, errorhandler=self.errorhandler, generalcache=False)
        except:
            self.errorhandler.logerror(self.errorhandler.traceback_str())
            sys.exit(1)

    def getprefsfilenames(self):
        """Returns the default prefs file name, and the prefs file name"""
        raise NotImplementedError("TableExporter.getprefsfilenames()")

    def GetDatabaseConfigInfo(self):
        raise NotImplementedError("TableExporter.GetDatabaseConfigInfo()")
      
    def GetExportDirectory(self):
        raise NotImplementedError("TableExporter.GetExportDirectory()")

    def CreateColumnSchema(self, description, schemaParent):
        """Returns the column schema from the description returned by db.allrows"""
        # Start column definition
        ColumnSchema = ElementTree.SubElement(schemaParent,'s:Schema')
        ColumnSchema.set('id','RowsetSchema')
        Columns = ElementTree.SubElement(ColumnSchema, 's:ElementType')
        Columns.set('name','row')
        Columns.set('content','eltOnly')

        # description is an array of tuples
        # each tuple describes a column
        for colnum, coldesc in enumerate(description):
            colName = str(coldesc[0]).upper()
            colNullable = coldesc[6] > 0
            colDatatype = coldesc[1]
            colDatalength = coldesc[3]
            colPrecision = coldesc[4]
            colScale = coldesc[5]

            # Principal description
            ColDesc = ElementTree.SubElement(Columns, 's:AttributeType')
            ColDesc.set('name',colName)
            ColDesc.set('rs:number',str(colnum+1))
            if colNullable:
                ColDesc.set('rs:nullable','true')
            ColDesc.set('rs:writeunknown','true')

            # Data description
            ColData = ElementTree.SubElement(ColDesc, 's:datatype')
            if colDatatype == self.db.driver.STRING:
                ColData.set('dt:type','string')
                ColData.set('rs:dbtype','str')
            elif colDatatype == self.db.driver.NUMBER:
                if colDatalength == 4:
                    ColData.set('dt:type','int')
                elif colDatalength == 8:
                    ColData.set('dt:type','float')
                else:
                    self.errorhandler.logerror('Unhandled numerical tye of length %d' % colDatalength)
                ColData.set('rs:precision',str(colPrecision))
                ColData.set('rs:fixedlength','true')
            elif colDatatype == self.db.driver.DATETIME:
                ColData.set('dt:type','dateTime')
                ColData.set('rs:dbtype','timestamp')
                ColData.set('rs:scale',str(colScale))
                ColData.set('rs:precision',str(colPrecision))
                ColData.set('rs:fixedlength','true')
            ColData.set('dt:maxlength',str(colDatalength))
            if not colNullable:
                ColData.set('rs:maybenull','false')

        # This should conclude the description of columns
        return ColumnSchema

    def WriteData(self, SQLStatement, filename, compress=False):
        # Create root element
        XMLTree = ElementTree.Element('xml')
        # Set namespaces
        XMLTree.set('xmlns:s','uuid:BDC6E3F0-6DA3-11d1-A2A3-00AA00C14882')
        XMLTree.set('xmlns:dt','uuid:C2F41010-65B3-11d1-A29F-00AA00C14882')
        XMLTree.set('xmlns:rs','urn:schemas-microsoft-com:rowset')
        XMLTree.set('xmlns:z','#RowsetSchema')

        # Get rows and descriptions
        rows, description = self.db.allrows(SQLStatement,1)
        colnames = [str(coldesc[0]) for coldesc in description]
        self.CreateColumnSchema(description, XMLTree)

        # Actual row data gets written here
        Data = ElementTree.SubElement(XMLTree, 'rs:data')
        for row in rows:
           Row = ElementTree.SubElement(Data, 'z:row')
           for colnum, column in enumerate(colnames):
               Row.set(column.upper(), str(row[colnum]))

        filePrefix = self.GetExportDirectory()
        fullname = os.path.join(filePrefix, filename)

        tree = ElementTree.ElementTree(XMLTree)
        if compress:
            # If the name ends with .zip, we want to chop this off the filename
            # Otherwise, we want to add it on to the fullname
            if fullname[-4:] == '.zip':
              filename = filename[:-4]
            else:
              fullname += '.zip'
            self.errorhandler.logtrace("writing %s as %s" % (fullname, filename))
            zipFile = zipfile.ZipFile(fullname, 'w', zipfile.ZIP_DEFLATED)
            XML = StringIO()
            tree.write(XML)
            zipFile.writestr(str(filename), XML.getvalue())
            zipFile.close()
        else:
            fp = open(str(fullname),'w')
            UglyXML = StringIO()
            tree.write(UglyXML)
            prettyXML = minidom.parseString(UglyXML.getvalue())
            fp.write(prettyXML.toprettyxml())
            fp.close()

    def ReadNumRows(self, filename, compressed=False):
        if compressed:
            tree = unzipAndParse(filename)
        else:
            tree = ElementTree.parse(open(filename))

        treeRoot = tree.getroot()
        rowset = treeRoot.find(str(ElementTree.QName(xmlns_rs,"data")))
        if not rowset:
            return 0

        rows = rowset.findall(str(ElementTree.QName(xmlns_z,"row")))
        return len(rows)
            
class TableImporter:
    def __init__(self, config, errorhandler=None):
        """constructs the jHistImportManager..."""
        if errorhandler is None:
            self.errorhandler = errors.ConsoleErrorHandler()
        else:
            self.errorhandler = errorhandler
        #Get the config
        self.config = config
        DatabaseConfig = self.GetDatabaseConfigInfo()
        #Set the date formatting text
        if DatabaseConfig.DBTYPE == 'access':
            self.dateformatstr = "format(logtime, 'YYYYMMDD')"
            self.datetimeformatstr = "format(logtime, 'YYYYMMDD_HH')"
        elif DatabaseConfig.DBTYPE == 'sqlserver':
            self.dateformatstr = "convert(char(8), logtime, 112)"
            self.datetimeformatstr = "convert(char(8), logtime, 112)+'_'+convert(char(2), logtime, 8)"
        elif DatabaseConfig.DBTYPE in ['oracle','postgres']:
            self.dateformatstr = "to_char(logtime, 'YYYYMMDD')"
            self.datetimeformatstr = "to_char(logtime, 'YYYYMMDD_HH24')"
        self.db = database.dbwrapper(DatabaseConfig, errorhandler=self.errorhandler, generalcache=False)
        # set up the list of changed files
        self.instdir = self.GetStorageDirectory()
    
    def GetDatabaseConfigInfo(self):
        raise NotImplementedError("TableImporter.GetDatabaseConfigInfo()")
      
    def GetStorageDirectory(self):
        raise NotImplementedError("TableImporter.GetStorageDirectory()")

    def CheckTable(self, tableName, tableXML, IDColumns, checkMod=True):
        #First, check for existence of table
        columnSchema = tableXML.find(str(ElementTree.QName(xmlns_s,"Schema")))
        columns = self.CheckTableStructure(tableName, columnSchema, checkMod)
        if not columns:
            self.errorhandler.logtrace("Creating table %s" % tableName)
            columns = self.CreateTableFromSchema(tableName, columnSchema)

        rowSet = tableXML.find(str(ElementTree.QName(xmlns_rs,"data")))
        # self.errorhandler.logtrace("checking table %s" % tableName)
        for row in rowSet.findall("{%s}row" % xmlns_z):
            IDValues = dict([(ID, row.get(ID.upper())) for ID in IDColumns])
            IDConditions = ["%s = %s" % (ID, self.db.dbrepr(ConvertValue(IDValues[ID], columns[ID.lower()]))) for ID in IDColumns]
            rowSQL = "SELECT * FROM %s WHERE " % tableName
            rowSQL += " AND ".join(IDConditions)
            rowdict = self.db.singlerowdict(rowSQL, toupper)
            self.CheckAndModifyRow(tableName, row, IDColumns, rowdict, columns, checkMod)

    def CheckAndModifyRow(self, table, XMLEquiv, IDColumns, rowdict, coltypedict, checkMod=True):
        """Checks to see if rows are the same.  If not, modifies the row accordingly.
           If the rowdict is not given, adds the row."""
        # TODO: Add formattedtype stuff for dates
        cols = XMLEquiv.keys()
        if not rowdict[IDColumns[0].upper()]:
            values = {}
            for col in cols:
                values[col.lower()] = ConvertValue(XMLEquiv.get(col), coltypedict[col.lower()])
            self.db.insert(table, values)
        elif checkMod:
            modified = 0
            for col in cols:
                if str(rowdict[col]) != XMLEquiv.get(col):
                    modified = 1
                    break
            if modified:
                values = {}
                for col in cols:
                    if col.lower() not in IDColumns:
                        values[col.lower()] = ConvertValue(XMLEquiv.get(col), coltypedict[col.lower()])
                self.db.update(table, IDColumns, [ConvertValue(XMLEquiv.get(ID.upper()), coltypedict[ID.lower()]) for ID in IDColumns], values)

    def RecreateTable(self, tableName, tableXML, whereClause=''):
        self.db.execute("DELETE FROM "+tableName + whereClause)
        rowSet = tableXML.find(str(ElementTree.QName(xmlns_rs,"data")))
        for row in rowSet.findall("{%s}row" % xmlns_z):
            cols = row.keys()
            values = {}
            for col in cols:
                values[col.lower()] = ConvertValue(row.get(col))
            try:
                self.db.insert(tableName, values)
            except Exception, e:
                self.errorhandler.logerror("Error inserting row into table %s: %s" % (tableName, e))

    def CreateTableFromSchema(self, tableName, columnSchema, primaryKeys=None):
      """Creates an event manager table"""
      columns = {}
      if primaryKeys is None:
        primaryKeys = []
      primaryKeys = [key.upper() for key in primaryKeys]
      types = self.db.dbtypenames
      elements = columnSchema.find(str(ElementTree.QName(xmlns_s,"ElementType")))
      SQL = "CREATE TABLE "+tableName+" ("
      for attribute in elements.findall("{%s}AttributeType" % xmlns_s):
        name = attribute.get("name")
        datatypeElem = attribute.find(str(ElementTree.QName(xmlns_s,"datatype")))
        genericdatatype = typemap[datatypeElem.get(ElementTree.QName(xmlns_dt,"type"))]
        datatype = types[genericdatatype]
        SQL += "%s %s" % (name, datatype)
        columns[name.lower()] = genericdatatype
        if name in primaryKeys:
          SQL += " NOT NULL"
        SQL += ", "
      if primaryKeys != []:
        SQL += "PRIMARY KEY (%s), " % ','.join(primaryKeys)
      SQL = SQL[:-2] + ")"
      self.db.execute(SQL)
      return columns

    def CheckTableStructure(self, tableName, columnSchema, checkMod):
      # First, get ourselves a rowset
      backtypemap = dict([(v, k) for k, v in self.db.dbtypenames.items()])
      SQL = "SELECT * FROM "+tableName+" WHERE 0 = 1"
      try:
        rows, description = self.db.allrows(SQL,1)
      except:
        return None

      # In this case, don't check full structure
      if not checkMod:
        return dict([(coldesc[0].lower(), backtypemap[coldesc[1].lower()]) for coldesc in description])

      # colnames are the names of the columns from the database
      # The second value in the tuple denotes a column which is there
      colnames = dict([(str(coldesc[0].lower()),False) for coldesc in description])

      # descnames are the column names in the schema
      descnames = {}
      
      types = self.db.dbtypenames
      elements = columnSchema.find(str(ElementTree.QName(xmlns_s,"ElementType")))
      for attribute in elements.findall("{%s}AttributeType" % xmlns_s):
        name = attribute.get("name").lower()
        datatypeElem = attribute.find(str(ElementTree.QName(xmlns_s,"datatype")))
        datatype = types[typemap[datatypeElem.get(ElementTree.QName(xmlns_dt,"type"))]]
        if not colnames.has_key(name):
          descnames[name] = (False, datatype)
        else:
          descnames[name] = (True, datatype)
          colnames[name] = True

      # Drop unused columns
      for column in colnames.keys():
        if colnames[column] == False:
          self.errorhandler.logtrace("Dropping unused column %s from table %s" % (column,tableName))
          SQL = "ALTER TABLE "+tableName+" DROP COLUMN "+column
          self.db.execute(SQL)

      # Add new columns
      for column in descnames.keys():
        if descnames[column][0] == False:
          self.errorhandler.logtrace("Adding new column %s to table %s" % (column, tableName))
          SQL = "ALTER TABLE %s ADD %s %s" % (tableName, column, descnames[column][1])
          self.db.execute(SQL)
                                              
      return dict([(key.lower(), backtypemap[descnames[key][1].lower()]) for key in descnames.keys()])


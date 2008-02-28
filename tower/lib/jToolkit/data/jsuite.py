# -*- coding: utf-8 -*-

"""wraps jSuite tables, like the jSuite OLE DB driver does
except this one does it by simply constructing the query requried given the columns and the table etc
see http://www.sjsoft.com/ for more information"""

# Copyright 2004 St James Software
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

from jToolkit.data import database
from jToolkit.data import dbtable

def strfilter(str):
  """filters non-alphanumeric chars, replaces them with underscore"""
  fstr = ""
  for c in str:
    if c.isalnum(): fstr += c
    else: fstr += "_"
  return fstr

def strmatch(string1, string2):
  """non-case-sensitive compare of alphanumeric chars only"""
  strip1 = ""
  strip2 = ""
  for c in string1:
    if c.isalnum(): strip1 += c.lower()
  for c in string2:
    if c.isalnum(): strip2 += c.lower()
  return strip1 == strip2

def normalizename(tagname):
  """this makes sure the tagname is also a valid column name"""
  if not (tagname[:1].isalpha() or tagname[:1] == "_"):
    tagname = "t" + tagname
  return tagname

class jsuitedbwrapper(database.dbwrapper):
  """this is a wrapper around dbwrapper which modifies the queries, to handle historical data"""
  def __init__(self, instance, *args, **kwargs):
    """initialises the jsuitedbwrapper class"""
    database.dbwrapper.__init__(self, instance, *args, **kwargs)

  def jsuitequery(self, columns, table, wherecond=""):
    """returns a query given a list of columns, a table, and a where clause"""
    newcolumns = [strfilter(column) for column in columns]
    # if we are using one of our own OLE DB providers, we don't need to wrap the query
    if self.driver.__name__.endswith('PyADO') and self.instance.DBPROVIDER.startswith("jSuite."):
      return self.nowrapquery(newcolumns,table,wherecond)
    else:
      return self.wrapquery(newcolumns,table,wherecond)

  def nowrapquery(self, columns, table, wherecond=""):
    """simple constructs a query without any history data wrapping"""
    if len(wherecond.strip()) > 0:
      whereclause = " where "+wherecond
    else:
      whereclause = ""
    return "select "+",".join(columns)+" from "+table+whereclause

  def gettagname(self, column):
    """returns the actual tagname for a given column name"""
    # handle quality as though it were a value (same col)
    column = column.lower()
    if column.lower().endswith('_quality'):
      return column[:column.rfind('_quality')]
    else:
      return column

  def gettagsource(self, tagname):
    """returns the tag source identifier for the given tagname"""
    sql = "select name, tagsource from tag_storage_defs"
    cursor = self.query(sql)
    morerows = 1
    while morerows:
      row = cursor.fetchone()
      if row is None:
        morerows = 0
      else:
        name, tagsource = row
        if strmatch(name, tagname):
          cursor.close()
          return tagsource
    cursor.close()
    return None

  def tagexists(self, table, tagname):
    """checks whether the tag is valid for the given table"""
    ticker, col = self.gettickercol(table, tagname)
    if ticker is None:
      return False
    else:
      return True

  def gettickercol(self, table, tagname):
    """returns the ticker and col for the given tagname in the given table"""
    tagsource = self.gettagsource(tagname)
    if tagsource is None:
      return None, None
    # TODO: check case sensitivity requirements
    sql = "select ticker, col from tag_ticker_cols " + \
      "where hist_mgr_num = (select hist_mgr_num from hist_mgr where file_name = '%s') " % table + \
      "and tagsource = '%s' and validto is null" % tagsource
    cursor = self.cursorexecute(sql)
    row = cursor.fetchone()
    cursor.close()
    if row is None:
      return None, None
    else:
      ticker, col = row
      return ticker, col

  def wrapquery(self, columns, table, wherecond=""):
    """wraps a query by creating a subselect that extracts the required history data..."""
    select = ""
    fromclause = " from "
    whereclause = " where "
    subselect = ""
    tickers = []
    tickercolumns = []
    tickercolumnmap = {}
    tagnames = []
    useslogtime = 0
    for column in columns:
      if column == 'logtime':
        useslogtime = 1
        tagnames.append(column)
      else:
        tagname = self.gettagname(column)
        addticker = 1
        addcolumn = 1
        ticker,col = self.gettickercol(table,tagname)
        # normalize after we've found the ticker and column so it doesn't affect the search
        tagname = normalizename(tagname)
        tagnames.append(tagname)
        try:
          ticker,col = int(ticker), int(col)
        except:
          raise KeyError("error finding ticker and column for tagname %s in table %s" % (tagname, table))
        if ticker in tickers: 
          addticker = 0
          if (ticker,col) in tickercolumns:
            if tagname in tickercolumnmap[ticker, col]:
              addcolumn = 0
        if addticker:
          if len(tickers) > 0:
            fromclause += ", "
          fromclause += "%s %s%03d" % (table,table,ticker)
          if len(tickers) > 0:
            whereclause += " and "
          whereclause += "%s%03d.ticker = %d" % (table,ticker,ticker)
          if len(tickers) > 0:
            whereclause += " and %s%03d.logtime = %s%03d.logtime" % (table,ticker,table,tickers[0])
          tickers.append(ticker)
        if addcolumn:
          tickercolumns.append((ticker,col))
          if (ticker, col) in tickercolumnmap:
            tickercolumnmap[ticker, col].append(tagname)
            print "warning: same ticker and column accessed under multiple names: %d, %d, %r" % (ticker, col, tickercolumnmap[ticker, col])
          else:
            tickercolumnmap[ticker, col] = [tagname]
          if len(select) > 0:
            select += ", "
          # note: for access & sqlserver, need columnwrap [ ] around column name
          select += "%s%03d.value%03d as %s" % (table,ticker,col,tagname)
          # always put quality in the subquery...
          select += ", %s%03d.quality%03d as %s" % (table,ticker,col,tagname+"_quality")
                
    subselect = "(select "
    if useslogtime:
      if len(tickers) > 0:
        t0 = tickers[0]
      else:
        t0 = 0
        fromclause += "%s %s%03d" % (table,table,0)
	whereclause += "%s%03d.ticker = %d" % (table,0,0)
      subselect += "%s%03d.logtime as logtime" % (table,t0)
      if len(tickercolumns) > 0:
        subselect += ", "
    if len(tickercolumns) == 0 and not useslogtime:
      # not doing anything, no subselect will be created
      subselect = table
    else:
      subselect += select + fromclause + whereclause + ") " + table
    if len(wherecond.strip()) > 0:
      whereclause = " where "+wherecond
    else:
      whereclause = ""
    sqlquery = "select "+",".join(tagnames)+" from "+subselect+whereclause
    return sqlquery

class jSuiteTable(dbtable.DBTable):
  def __init__(self, db, tablename, columnlist, rowidcols, orderbycols):
    dbtable.DBTable.__init__(self, db, tablename, columnlist, rowidcols, orderbycols)
    self.tablename = "(%s) %s" % (db.jsuitequery(self.columnlist, tablename), tablename)
  def getsqlcolumns(self):
    tagnames = [normalizename(column) for column in self.columnlist]
    return ", ".join(tagnames)
  def addrow(self, argdict):
    raise NotImplementedError("can't insert into jHistorian row")
  def modifyrow(self, argdict):
    raise NotImplementedError("can't modify jHistorian row")
  def deleterow(self, argdict):
    raise NotImplementedError("can't delete jHistorian row")
  def createtable(self):
    raise NotImplementedError("can't create jHistorian table")
  def droptable(self):
    raise NotImplementedError("can't drop jHistorian table")
  def denormalizenames(self, rows):
    for row in rows:
      for column in self.columnlist:
        tagname = normalizename(column)
        if tagname != column:
          if tagname in row:
            row[column] = row.pop(tagname)
    return rows
  def gettablerows(self, filter = None):
    return self.denormalizenames(super(jSuiteTable, self).gettablerows(filter))
  def getsometablerows(self, minRow = None, maxRow = None, filter = None):
    return self.denormalizenames(super(jSuiteTable, self).getsometablerows(minRow, maxRow, filter))
  def getsomerecord(self, filter = None):
    rowid, record = super(jSuiteTable, self).getsomerecord(filter)
    return rowid, self.denormalizenames([record])[0]



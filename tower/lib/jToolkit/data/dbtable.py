#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""dbtable is a module that simplifies accessing database tables"""

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

class DBTable(object):
  """DBTable is an abstraction of a table and its related data"""
  def __init__(self, db, tablename, columnlist, rowidcols, orderbycols):
    """initialises the DBTable
    columnlist is a list of (columnname, columntype) tuples
    rowidcols and orderbycols can either be a single column name string or a list of them"""
    self.db = db
    self.tablename = tablename
    self.columnlist = [column[0] for column in columnlist]
    self.columntypes = dict([(column[0], column[1]) for column in columnlist])
    self.rowidcols = rowidcols
    if isinstance(self.rowidcols, basestring): self.rowidcols = [self.rowidcols]
    self.orderbycols = orderbycols
    if isinstance(self.orderbycols, basestring): self.orderbycols = [self.orderbycols]

  def getrowid(self, argdict):
    """retrieves the rowid from the arguments"""
    rowid = [argdict.get(rowidcol, None) for rowidcol in self.rowidcols]
    if len(self.rowidcols) == 1:
      return rowid[0]
    else:
      if reduce(int.__and__, [value is None for value in rowid]):
        return None
      else:
        return tuple(rowid)

  def rowidclause(self, rowid):
    """returns a where clause that matches the rowid"""
    if len(self.rowidcols) == 1:
      return self.db.equalsphrase(self.rowidcols[0], rowid)
    else:
      return " and ".join([self.db.equalsphrase(self.rowidcols[n], rowid[n]) for n in range(len(self.rowidcols))])

  def rowidparamstring(self, rowid):
    """returns a param string (for a url) that matches the rowid"""
    if len(self.rowidcols) == 1:
      if isinstance(rowid, unicode): rowid = rowid.encode(self.db.encoding)
      return "%s=%s" % (self.rowidcols[0], rowid)
    else:
      newrowid = []
      for n in range(len(rowid)):
        if isinstance(rowid[n], unicode): newrowid.append(rowid[n].encode(self.db.encoding))
        else: newrowid.append(rowid[n])
      return "&".join(["%s=%s" % (self.rowidcols[n], rowid[n]) for n in range(len(self.rowidcols))])

  def orderbyclause(self):
    """returns the order by clause"""
    if len(self.orderbycols) > 0:
      return " order by " + ",".join(self.orderbycols)
    else:
      return ""

  def getsqlcolumns(self):
    """returns the list of columns joined with commas (for sql statements)"""
    return ", ".join(self.columnlist)

  def getrecord(self, rowid):
    """retrieves the record corresponding to the given rowid"""
    sql = "select %s from %s where %s" % (self.getsqlcolumns(), self.tablename, self.rowidclause(rowid))
    record = self.db.singlerowdict(sql, self.db.lower, self.db.nonetoblank)
    for key, value in record.iteritems():
      if value is None: record[key] = ''
    return record

  def rowidexists(self, rowid):
    """returns where a record exists with the given rowid"""
    sql = "select count(*) from %s where %s" % (self.tablename, self.rowidclause(rowid))
    count = int(self.db.singlevalue(sql))
    return count > 0

  def filtermatchessome(self, filter):
    """returns whether any rows exist for the given filter"""
    sql = "select count(*) from %s %s" % (self.tablename, self.getfilterclause(filter))
    count = int(self.db.singlevalue(sql))
    return count > 0

  def getdefaultrecord(self):
    """retrieves a default record for new categories"""
    # if sensible values are needed here, this method can be overridden
    return dict([(column, '') for column in self.columnlist])

  def getfilterclause(self, filter):
    """returns a where clause for the given filter"""
    if filter is None:
      return " "
    elif isinstance(filter, basestring):
      return filter
    else:
      return self.db.catclauses([filter.getfilterclause(self.db)])

  def getsomerecord(self, filter = None):
    """retrieves a single rowid & record when you don't know which one you want..."""
    sql = "select %s from %s %s %s" % (self.getsqlcolumns(), self.tablename, self.getfilterclause(filter), self.orderbyclause())
    record = self.db.singlerowdict(sql, self.db.lower, self.db.nonetoblank)
    rowid = self.getrowid(record)
    return rowid, record

  def gettablerows(self, filter = None):
    """retrieves all the rows in the table"""
    sql = "select %s from %s %s %s" % (self.getsqlcolumns(), self.tablename, self.getfilterclause(filter), self.orderbyclause())
    return self.db.allrowdicts(sql, self.db.lower, self.db.nonetoblank)

  def countrows(self, filter = None):
    """counts the number of rows in the table matching the filter"""
    sql = "select count(*) from %s %s" % (self.tablename, self.getfilterclause(filter))
    return int(self.db.singlevalue(sql))

  def getsometablerows(self, minRow = None, maxRow = None, filter = None):
    """retrieves all the rows in the table"""
    sql = "select %s from %s %s %s" % (self.getsqlcolumns(), self.tablename, self.getfilterclause(filter), self.orderbyclause())
    return self.db.somerowdicts(sql, self.db.lower, self.db.nonetoblank, minrow=minRow, maxrow=maxRow)

  def addrow(self, argdict):
    """add the row to the table"""
    valuesdict = cidict.filterdict(cidict.cidict(argdict), self.columnlist)
    self.db.insert(self.tablename, valuesdict)

  def modifyrow(self, argdict):
    """modify the row in the table"""
    rowid = self.getrowid(argdict)
    if rowid is None:
      raise TypeError, "rowid is None in modifylog"
    valuesdict = self.getrecord(rowid)
    newvaluesdict = cidict.filterdict(argdict, valuesdict)
    updatedict = cidict.subtractdicts(newvaluesdict, valuesdict)
    self.db.update(self.tablename, self.rowidcols, rowid, updatedict)

  def deleterow(self, argdict):
    """delete the row in the table"""
    rowid = self.getrowid(argdict)
    if rowid is None:
      raise TypeError, "rowid is None in deletelog"
    self.db.delete(self.tablename, self.rowidcols, rowid)

  def createtable(self):
    """creates the table represented by self, using tablename and columnlist and returning success"""
    sql = "create table %s (" % self.tablename
    sql += ", ".join([column+" "+self.db.dbtypename(self.columntypes[column]) for column in self.columnlist])
    sql += ")"
    try:
      self.db.execute(sql)
      return 1
    except Exception:
      return 0

  def droptable(self):
    """drops the table represented by self, using tablename and returning success"""
    sql = "drop table %s" % self.tablename
    try:
      self.db.execute(sql)
      return 1
    except Exception:
      return 0



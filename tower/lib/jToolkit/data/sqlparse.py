#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""SQL parser for OLE DB driver etc"""

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

from jToolkit import sparse

SQLkeywords = ['select','from','where','insert','delete','modify','order','by','as']

def mungetagname(tagname):
    """takes a tag name and replaces all non-alphanumeric characters with a _"""
    return "".join([c.isalnum() and c.lower() or '_' for c in tagname])    

def findTablesAndColumns(input):
    """Takes a SQL statement and returns all possible table names and column names

    Returns a list of two lists - the first list is of tables, the second of columns"""
    parser = sparse.SimpleParser()
    tokens = parser.tokenize(input)

    tables = {}
    columns = []
    inFrom = 0
    for tokennum, token in enumerate(tokens):
        #Check to see it starts with an acceptable character
        if not (token[0].isalpha() or token[0] == '_'):
            continue        #We don't do anything with tokens not starting with a letter
        
        if token == 'from':
            inFrom = 1
            continue

        if token in SQLkeywords:        #Only relevance of other clauses for the moment is that they end a from clause
            inFrom = 0      #if it's not in keywords, it won't get to this line
        else:
            if inFrom:
                # TODO: handle subselects, get table names properly in that case...
                tables[token] = parser.findtokenpos(tokennum)
            else:
                columns.append(token)

    return [tables,columns]

historytables = {}
historytags = {}

def modifySqlStatement(sql, tables, columns):
  """create a new sql statement with subselects to read information out of history tables"""
  tablenumbers = {}
  tabletickers = {}
  tableselects = {}
  # make a simple list of the tables...
  for tablename in tables:
    tablenumber = historytables.get(tablename.strip().lower(), None)
    if tablenumber is not None:
      tablenumbers[tablenumber] = tablename
      tabletickers[tablenumber] = {}
  # go through all the column names and see which tickers and columns are needed for each table
  for columnname in columns:
    tagname = mungetagname(columnname)
    for tablenumber in tablenumbers:
      tickercol = historytags.get((tagname, tablenumber))
      if tickercol is not None:
        ticker, col = tickercol
        if ticker not in tabletickers[tablenumber]:
          tabletickers[tablenumber][ticker] = [(columnname, col)]
        else:
          tabletickers[tablenumber][ticker].append((columnname, col))
  # create all the selects that will replace a table name
  for tablenumber, tablename in tablenumbers.iteritems():
    tickers = tabletickers[tablenumber]
    cols = []
    subselects = []
    wheres = []
    masterticker = tickers.iterkeys().next()
    for ticker, pairs in tickers.iteritems():
      renamecolumns = ", ".join(["value%03d as %s" % (col, columnname) for (columnname, col) in pairs])
      tickerselect = "(select logtime, %s from %s where ticker = %d) %s%03d" % \
        (renamecolumns, tablename, ticker, tablename, ticker)
      subselects.append(tickerselect)
      cols.extend(["%s%03d.%s" % (tablename, ticker, columnname) for (columnname, col) in pairs])
      wheres.append("%s%03d.logtime = %s%03d.logtime" % (tablename, ticker, tablename, masterticker))
    tableselects[tablename] = "(select %s%03d.logtime, %s from %s where %s) %s" % \
      (tablename, masterticker, ", ".join(cols), ", ".join(subselects), " and ".join(wheres), tablename)
  # splice the selects in place of the table names...
  tablepositions = dict([(position, tablename) for (tablename, position) in tables.iteritems()])
  tableorder = tablepositions.keys()
  tableorder.sort()
  newsql = ""
  sqlpos = 0
  for position in tableorder:
    tablename = tablepositions[position]
    tableselect = tableselects[tablename]
    newsql += sql[sqlpos:position]
    newsql += tableselect
    sqlpos = position + len(tablename)
  newsql += sql[sqlpos:]
  return newsql

def readhistorytables(infile):
  """reads the list of history tables from a tab-delimited file"""
  for line in infile.xreadlines():
    tablenumber, tablename = line.strip().split('\t')
    historytables[tablename.strip().lower()] = int(tablenumber)

def readhistorytags(infile):
  """reads the list of history tags from a tab-delimited file"""
  for line in infile.xreadlines():
    tagname, tablenumber, ticker, col = line.strip().split('\t')
    historytags[(mungetagname(tagname), int(tablenumber))] = (int(ticker), int(col))

if __name__ == '__main__':
  import sys
  lookupmgrs = open('mgrs', 'r')
  readhistorytables(lookupmgrs)
  lookupmgrs.close()
  lookuptags = open('tags', 'r')
  readhistorytags(lookuptags)
  lookuptags.close()
  for line in sys.stdin.xreadlines():
    tables, columns = findTablesAndColumns(line)
    sql = line.strip()
    newsql = modifySqlStatement(sql, tables, columns)
    print "sql: ", sql
    print "tables: ", repr(tables)
    print "columns: ", repr(columns)
    print "newsql: ", newsql


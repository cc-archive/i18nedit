# -*- coding: utf-8 -*-
""" This module holds the TableLayout and TableCell classes
    They are used to intelligent layout widgets in cells in a table...
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

from jToolkit.widgets import widgets

class TableCell(widgets.ContentWidget):
  def __init__(self, contents, newattribs={}, rowspan=1, colspan=1):
    widgets.ContentWidget.__init__(self, 'td', contents)
    self.attribs = {'type':'td', 'rowspan':rowspan, 'colspan':colspan}
    self.overrideattribs(newattribs)
    self.hidden = 0
    self.width = 0
    self.isempty = 0

  def gethtml(self):
    if self.hidden:
      return ""
    else:
      return widgets.ContentWidget.gethtml(self)
    
class TableLayout(widgets.Widget):
  # maintains a dictionary of cells in rows, indexed by row number and column number
  def __init__(self, newattribs = {}):
    widgets.Widget.__init__(self, "TABLE")
    self.attribs = {'cellspacing':'1', 'cellpadding':'1'}
    self.overrideattribs(newattribs)
    self.rowsdict = {}
    
  def hasrow(self, rownum):
    return rownum in self.rowsdict

  def setrow(self, rownum):
    self.rowsdict[rownum] = {}

  def getrow(self, rownum):
    return self.rowsdict.get(rownum, {})
  
  def hascell(self, rownum, colnum):
    return self.hasrow(rownum) and colnum in self.getrow(rownum)

  def setcell(self, rownum, colnum, value):
    """sets the cell in rownum, colnum position to value"""
    # add the row if it doesn't yet exist
    if not self.hasrow(rownum):
      self.setrow(rownum)
    self.getrow(rownum)[colnum] = value

  def delcell(self, rownum, colnum):
    """removes the cell in rownum, colnum position"""
    if not self.hasrow(rownum):
      raise KeyError, "row %d does not exist" % rownum
    else:
      del self.getrow(rownum)[colnum]

  def getcell(self, rownum, colnum):
    """returns the cell in position rownum, colnum"""
    cell = self.getrow(rownum).get(colnum, None)
    if cell is None:
      return self.newemptycell()
    else:
      return cell

  def newemptycell(self):
    emptycell = TableCell('')
    emptycell.width = 0
    emptycell.isempty = 1
    return emptycell
    
  def maxrowspan(self, row):
    if len(row) == 0: return 0
    return max([cell.attribs['rowspan'] for cell in row.itervalues()])

  def rowmaxcolnum(self, row):
    if len(row) == 0: return 0
    return max([col + cell.attribs['colspan']-1 for col, cell in row.iteritems()])

  def minrownum(self):
    if len(self.rowsdict) == 0: return 0
    return min(self.rowsdict.iterkeys())

  def maxrownum(self):
    if len(self.rowsdict) == 0: return 0
    return max([rownum + self.maxrowspan(row)-1 for rownum, row in self.rowsdict.iteritems()])

  def rowrange(self):
    return range(self.minrownum(), self.maxrownum()+1)

  def mincolnum(self):
    if len(self.rowsdict) == 0: return 0
    return min([min(row.iterkeys()) for row in self.rowsdict.itervalues()])

  def maxcolnum(self):
    if len(self.rowsdict) == 0: return 0
    return max([self.rowmaxcolnum(row) for row in self.rowsdict.itervalues()])

  def colrange(self):
    return range(self.mincolnum(), self.maxcolnum()+1)

  def getrowcontents(self, rownum):
    contentslist = [self.getcell(rownum, colnum).gethtml() for colnum in self.colrange()]
    # TODO: investigate ways to neaten this up while still preventing ASCII decoding error...
    typelist = [type(p) for p in contentslist]
    if unicode in typelist and str in typelist:
      for n in range(len(contentslist)):
        if isinstance(contentslist[n], str):
          contentslist[n] = contentslist[n].decode('utf8')
    return "<tr>" + "".join(contentslist) + "</tr>\r"
    
  def getcontents(self):
    contentslist = [self.getrowcontents(rownum) for rownum in self.rowrange()]
    # TODO: investigate ways to neaten this up while still preventing ASCII decoding error...
    typelist = [type(p) for p in contentslist]
    if unicode in typelist and str in typelist:
      for n in range(len(contentslist)):
        if isinstance(contentslist[n], str):
          contentslist[n] = contentslist[n].decode('utf8')
    return "".join(contentslist)

  def rowempty(self, rownum):
    """returns whether this row is empty (contains no non-empty cells)"""
    for colnum in self.colrange():
      if self.hascell(rownum, colnum) and not self.getcell(rownum, colnum).isempty:
        return 0
    return 1

  def colempty(self, colnum):
    """returns whether this column is empty (contains no non-empty cells)"""
    for rownum in self.rowrange():
      if self.hascell(rownum, colnum) and not self.getcell(rownum, colnum).isempty:
        return 0
    return 1

  def adjustrowspan(self, rownum, deletedrownum):
    """adjusts all the rowspans for this rownum to reflect the fact that deletedrownum is gone"""
    for colnum in self.colrange():
      if self.hascell(rownum, colnum):
         cell = self.getcell(rownum, colnum)
         if cell.attribs['rowspan'] > deletedrownum - rownum:
           cell.attribs['rowspan'] -= 1

  def adjustcolspan(self, colnum, deletedcolnum):
    """adjusts all the colspans for this colnum to reflect the dact that deletedcolnum is gone"""
    for rownum in self.rowrange():
      if self.hascell(rownum, colnum):
         cell = self.getcell(rownum, colnum)
         if cell.attribs['colspan'] > deletedcolnum - colnum:
           cell.attribs['colspan'] -= 1

  def removerow(self, rownum):
    """removes the row from the table, shrinking other rownums, and adjusting rowspans..."""
    if rownum in self.rowsdict:
      del self.rowsdict[rownum]
    for otherrownum in self.rowrange():
      # adjust rowspans for rows before this one
      if not otherrownum in self.rowsdict:
        continue
      if otherrownum < rownum:
        # do a general check to see if this is neccessary at all for this row
        if self.maxrowspan(self.rowsdict[otherrownum]) > rownum - otherrownum:
          self.adjustrowspan(otherrownum, rownum)
      elif otherrownum > rownum:
        # shift row one up...
        self.rowsdict[otherrownum-1] = self.rowsdict[otherrownum]
        del self.rowsdict[otherrownum]

  def removecol(self, colnum):
    """removes the column from the table, shrinking other colnums, and adjusting colspans..."""
    for rownum in self.rowrange():
      if self.hascell(rownum, colnum):
        self.delcell(rownum, colnum)
    for othercolnum in self.colrange():
      # adjust colspans for cols before this one
      if othercolnum < colnum:
        self.adjustcolspan(othercolnum, colnum)
      elif othercolnum > colnum:
        # shift col one up...
        for rownum in self.rowrange():
          if self.hascell(rownum, othercolnum):
            cell = self.getcell(rownum, othercolnum)
            self.delcell(rownum, othercolnum)
            self.setcell(rownum, othercolnum-1, cell)

  def shrinkrange(self):
    """removes all the empty rows and columns, reducing the range..."""
    if len(self.rowsdict) == 0: return
    # detect which rows are empty
    emptyrows = []
    for rownum in self.rowrange():
      if self.rowempty(rownum):
        emptyrows.append(rownum)
    # remove the rows, adjusting for the rows that have already been removed...
    adjustment = 0
    for rownum in emptyrows:
      self.removerow(rownum-adjustment)
      adjustment += 1
    # detect which columns are empty
    emptycols = []
    for colnum in self.colrange():
      if self.colempty(colnum):
        emptycols.append(colnum)
    # remove the colums, adjusting for the colums that have already been removed...
    adjustment = 0
    for colnum in emptycols:
      self.removecol(colnum-adjustment)
      adjustment += 1

  def fillemptycells(self, emptycellmaker=None):
    if emptycellmaker is None:
      emptycellmaker = self.newemptycell
    for rownum in self.rowrange():
      for colnum in self.colrange():
        if not self.hascell(rownum, colnum):
          self.setcell(rownum, colnum, emptycellmaker())

  def mergeduplicates(self, excluderows=[], emptycellmaker=None):
    """merge cells that are the same object..."""
    if emptycellmaker is None:
      emptycellmaker = self.newemptycell
    for colnum in self.colrange():
      lastcell = None
      for rownum in self.rowrange():
        if rownum in excluderows:
          # allows us to skip the title etc
          continue
        cell = self.getcell(rownum, colnum)
        if cell == lastcell and lastcell is not None:
          lastcell.attribs['rowspan'] += 1
          self.setcell(rownum, colnum, emptycellmaker())
        else:
          lastcell = cell
        
  def hidecoveredcells(self):
    """hide blank cells that are underneath another cell with rowspan/colspan"""
    self.fillemptycells()
    for rownum in self.rowrange():
      for colnum in self.colrange():
        cell = self.getcell(rownum,colnum)
        if not cell.hidden:
          for blankrowoffset in range(0,cell.attribs['rowspan']):
            for blankcoloffset in range(0,cell.attribs['colspan']):
              # don't overwrite the current cell!
              if blankrowoffset != 0 or blankcoloffset != 0:
                self.hidecell(rownum+blankrowoffset, colnum+blankcoloffset)

  def hidecell(self, rownum, colnum):
    cell = self.getcell(rownum, colnum)
    cell.hidden = 1

  def rowwidth(self, rownum):
    width = 0
    for cell in self.getrow(rownum).itervalues():
      width += getattr(cell, 'width', 0)
    return width

  def maxwidth(self):
    return max([self.rowwidth(rownum) for rownum in self.rowrange()])

  def calcweights(self):
    # calculate column widths for all the cells
    maxwidth = self.maxwidth()
    for rownum in self.rowrange():
      for colnum in self.colrange():
        cell = self.getcell(rownum, colnum)
        if cell.width != 0:
          width=100.0*cell.width/maxwidth
          styleattribs = {'width':'%d%%' % int(width)}
          cell.overrideattribs({'style':styleattribs})


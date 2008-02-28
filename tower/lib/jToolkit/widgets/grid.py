#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""grid module: responsible for building up grid widgets"""

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
from jToolkit.widgets import table
from jToolkit import cidict
from jToolkit.data import dates
import types

class GridCategory:
  def __init__(self, name, title, display, storageformat, displayformat, col, pctwidth, mergecells, mainarea, attribs = {}):
    self.name = name
    self.title = title
    self.display = display
    self.mainarea = mainarea
    self.storageformat = storageformat
    self.displayformat = displayformat
    self.col = col
    self.pctwidth = pctwidth
    self.width = None
    self.mergecells = mergecells
    self.attribs = attribs

  def gettitlecellwidget(self):
    """returns the title cell for this category, using the self.width"""
    titlestyle = {'font-weight':'bold'}
    return table.TableCell(self.title, newattribs={'width':'%f%%' % self.width,'style':titlestyle})

  def valuetostring(self, value):
    """based on the category, returns value as a string that can be displayed"""
    # TODO: look at combining this and other methods with FormCategory...
    if self.storageformat in ['TEXT','STRING']:
      if value is None:
        return ''
      else:
        return value
    elif self.storageformat in ['INTEGER', 'DECIMAL']:
      return str(value)
    elif self.storageformat == 'DATETIME':
      return dates.formatdate(value, self.displayformat)
    elif value is None:
      return ''
    else:
      return value

  def getcellwidget(self, obj, style, href, hreftarget):
    """returns a widget for a cell"""
    text = self.valuetostring(obj)
    if href is None:
      contents = text
    else:
      contents = widgets.Link(href, text, {'target':hreftarget,'style':style})
    self.attribs.update({'valign':'top','style':style})
    return table.TableCell(contents, newattribs=self.attribs)

  def canmerge(self, widget1, widget2):
    """checks whether we can merge these cells..."""
    if not self.mergecells:
      return False
    if type(widget1) == type(widget2):
      if type(widget1) == types.InstanceType:
        if widget1.__class__ == widget2.__class__:
          # now we can compare
          if isinstance(widget1, table.TableCell):
            # match cells if the contents match and the attributes match
            return self.canmerge(widget1.contents, widget2.contents) and widget1.attribs == widget2.attribs
          elif isinstance(widget1, widgets.Link):
            # merge if contents are the same, even if links are different
            # the links are usable from another row
            return self.canmerge(widget1.contents, widget2.contents)
          else:
            # unknown class...
            return 0
        else:
          # mismatched class
          return 0
      elif isinstance(widget1, basestring):
        return widget1 == widget2
      else:
        # unknown type
        return 0
    else:
      # mismatched types
      return 0

  def gethtmlstyle(self, textcolor, backcolor, font):
    style = {}
    style['color'] = widgets.getrgb(textcolor, '&H000000')
    style['background-color'] = widgets.getrgb(backcolor, '&HFFFFFF')
    if font is not None:
      fontstyles = font.lower().split()
      for fontstyle in fontstyles:
        if fontstyle == 'bold': style['font-weight'] = 'bold'
        if fontstyle == 'italic': style['font-style'] = 'italic'
    return style

class GridDivision(widgets.Division):
  """this division class is used to do layout tricks to be wider than the screen"""
  def __init__(self, gridwidget):
    widthstr = '%d%%' % gridwidget.pctwidth
    widgets.Division.__init__(self, newattribs={'style':{'width':widthstr}}, contents=gridwidget)

class Grid(table.TableLayout):
  def __init__(self, categories, fillincolumn=None):
    table.TableLayout.__init__(self, newattribs = {'width':'100%','border':'1','cellspacing':'0'})
    self.pctwidth = 100
    self.categories = categories
    self.fillincolumn = fillincolumn
    self.balancewidths()

  def addtitlerow(self):
    """Add the title row cells"""
    for category in self.categories:
      if category.display:
        titlecell = category.gettitlecellwidget()
        self.addcell(0, category, titlecell)

  def balancewidths(self):
    """calculate the width of each of the columns"""
    # summarize widths...
    mainfixedpctwidth = 0
    suppfixedpctwidth = 0
    for category in self.categories:
      if category.display:
        if category.pctwidth == 0: category.pctwidth = 10
        if category.mainarea:
          mainfixedpctwidth += category.pctwidth
        else:
          suppfixedpctwidth += category.pctwidth
    extrapctwidth = 100 - mainfixedpctwidth
    if extrapctwidth >= 0:
      totalpctwidth = 100 + suppfixedpctwidth
    else:
      totalpctwidth = 100 + suppfixedpctwidth - extrapctwidth
      extrapctwidth = 0
    self.pctwidth = totalpctwidth
    # add the title cells...
    for category in self.categories:
      if category.display:
        if category.name == self.fillincolumn:
          category.width = (category.pctwidth + extrapctwidth) * 100.0 / totalpctwidth
        else:
          category.width = category.pctwidth * 100.0 / totalpctwidth

  def addcell(self, rownum, category, value):
    """adds a cell to the grid"""
    # see if this should be merged with the above cell...
    if self.hascell(rownum-1, category.col):
      cellabove = self.getcell(rownum-1, category.col)
      if category.canmerge(value, cellabove):
        # at the moment, duplicate objects, later, replace them...
        value = cellabove
    table.TableLayout.setcell(self, rownum, category.col, value)

class SimpleGridCategory(GridCategory):
  """a GridCategory that handles coloring..."""
  def __init__(self, name, title, tooltip, colnum, colordict, isheading, display, storageformat='TEXT'):
    if storageformat == 'DATETIME':
      displayformat = '%y-%m-%d %H:%M:%S'
    else:
      displayformat = ''
    GridCategory.__init__(self, name, title, display=display, storageformat=storageformat, displayformat=displayformat,
                          col=colnum, pctwidth=10, mergecells=0, mainarea=1)
    self.tooltip = tooltip
    self.colorcategory = None
    self.colordict = colordict
    if isheading:
      self.backcolor = '&HD0D0D0'
      self.font = 'bold'
    else:
      self.backcolor = '&HFFFFFF'
      self.font = ''

  def setcolorcategory(self, colorcategory):
    """sets which category the color of this one will be based on"""
    self.colorcategory = colorcategory

  def gettitlecellwidget(self):
    """returns the title cell for this category, using the given width"""
    titlestyle = self.gethtmlstyle('&H660000', self.backcolor, 'bold')
    titlelink=widgets.Tooltip(self.tooltip, self.title)
    attribs={'width': '%f%%' % self.width, 'style': titlestyle,'valign': 'top'}
    return table.TableCell(titlelink, newattribs=attribs)

  def gettextcolor(self, row):
    """returns textcolor based on the value of this category in given row"""
    obj = row[self.name]
    return self.colordict.get(str(obj),None)

  def getwidget(self, row, href, hreftarget):
    """simply returns a widget for this category"""
    obj = row[self.name]
    obj = self.valuetostring(obj)
    if obj is None:
      text = ''
    elif isinstance(obj, unicode):
      text = obj.encode('utf8')
    else:
      text = str(obj)
    if text == '':
      text = '&nbsp;'
    if self.colorcategory is not None:
      textcolor = self.colorcategory.gettextcolor(row)
    else:
      textcolor = '&H000000'
    style = self.gethtmlstyle(textcolor, self.backcolor, self.font)
    style['text-decoration'] = 'none'
    # we need to set the style in both objects otherwise the link style can override it
    if href is None:
      contents = text
    else:
      contents = widgets.Link(href, text, {'target':hreftarget,'style':style})
    return table.TableCell(contents, newattribs={'valign':'top','style':style})

class SimpleGrid(Grid):
  """a grid with common methods for config pages"""
  def __init__(self, gridtable, columnlist, hrefbase=None, hreftarget='', colordefs={}, colordeps={}, \
               headingcolumns=(), hidecolumns=(), filter=None, gridcategory=SimpleGridCategory,newattribs={}):
    self.hrefbase = hrefbase
    self.hreftarget = hreftarget
    self.gridtable = gridtable
    self.columnlist = columnlist
    self.colordefs = colordefs
    self.colordeps = colordeps
    self.headingcolumns = headingcolumns
    self.hidecolumns = hidecolumns
    self.filter = filter
    self.gridcategory = gridcategory
    Grid.__init__(self, self.getcolumns())
    self.overrideattribs(newattribs)
    self.makegrid()

  enabled, disabled = '&H000000', '&H808080'
  booleancolors = cidict.cidict({'false':disabled, 'true':enabled})

  def getcolumns(self):
    """gets the columns for the grid (columns of categoryconf)..."""
    columns = []
    columndict = {}
    colnum = 0
    for name, title, tooltip in self.columnlist:
      colnum += 1
      colordict = self.colordefs.get(name,{})
      isheading = name in self.headingcolumns
      display = name not in self.hidecolumns
      storageformat = self.gridtable.columntypes.get(name, 'TEXT').upper()
      column = self.gridcategory(name, title, tooltip, colnum, colordict, isheading, display, storageformat)
      columns.append(column)
      columndict[name] = column
    for colorcolumnname, depcolumnnames in self.colordeps.iteritems():
      colorcolumn = columndict[colorcolumnname]
      for depcolumnname in depcolumnnames:
        depcolumn = columndict[depcolumnname]
        depcolumn.setcolorcategory(colorcolumn)
    return columns

  def makegrid(self):
    """makes up the grid - retrieves rows, adds them, and adjusts the grid"""
    self.addtitlerow()
    self.addrows()
    self.shrinkrange()
    # in case we missed any out...
    self.fillemptycells()
    self.mergeduplicates([0])
    self.hidecoveredcells()
    self.calcweights()

  def addrows(self):
    """gets all the database rows from the table and adds cells for each one to the grid"""
    self.getrows()
    for row in self.tablerows:
      self.addrow(row)

  def addrow(self, row):
    """adds all the cells for a row to the grid"""
    href = None
    if self.hrefbase is not None:
      rowid = self.gridtable.getrowid(row)
      href = self.hrefbase
      if '?' in href:
        href += "&"
      else:
        href += "?"
      href += 'action=view&' + self.gridtable.rowidparamstring(rowid)
      if self.page:
        href += '&page=%d' % self.page
    rownum = self.maxrownum() + 1
    for category in self.categories:
      if not category.display: continue
      widgetcell = category.getwidget(row, href, self.hreftarget)
      self.addcell(rownum, category, widgetcell)

  def handlepageargs(self):
    """handle arguments that select the current page"""
    page = self.attribs.get('page', 0)
    try:
      page = int(page)
    except:
      if page.lower() == 'all':
        page = 0
      else:
        page = 1
    self.page = page
    self.numrowsinpage = self.attribs.get('numrowsinpage',20)

  def getrows(self):
    """retrieves the appropriate rows from the database"""
    self.handlepageargs()
    if self.page == 0:
      minrow, maxrow = None, None
    else:
      minrow, maxrow = (self.page-1)*self.numrowsinpage, self.page*self.numrowsinpage
      if minrow < 0: minrow = 0
      # if maxrow > len(alllogrows): maxrow = len(alllogrows)
    if minrow != None and maxrow != None:
      self.tablerows = self.gridtable.getsometablerows(minrow,maxrow,self.filter)
      if len(self.tablerows) < maxrow-minrow:   #End of table
        self.tableEnded = 1
      else:
        self.tableEnded = 0
    else:
      self.tablerows = self.gridtable.gettablerows(self.filter)

  def getpagelink(self, pagehref, pagenum, pagetext=None):
    """returns a widget that links to a particular page"""
    if pagetext is None:
      pagetext = "Page %d" % pagenum
    if pagenum == self.page:
      pagetext = "<font color='red'><b>%s</b></font>" % pagetext
    return widgets.Link(pagehref+"&page=%d" % pagenum, pagetext)

  def getpagelinks(self):
    """returns a widget that links to other pages of this grid"""
    self.numpages = (self.gridtable.countrows(self.filter) + self.numrowsinpage - 1) / self.numrowsinpage
    currentpage = "Page %d of %d. " % (self.page, self.numpages)
    pagehref = "?"
    if self.filter is not None:
      pagehref += self.filter.getfilterparams()
    first, last, next, previous = "First", "Last", "Next", "Previous"
    if self.page == 0:
      currentpage = "Showing all records"
      pages = [(1, first), (self.numpages, last)]
    elif self.numpages > 1:
      pages = []
      if 1 == self.page-1:
        pages.append((1, first+"/"+previous))
      else:
        pages.append((1, first))
        if self.page-1 > 1:
          pages.append((self.page-1, previous))
      if self.page+1 == self.numpages:
        pages.append((self.page+1, next+"/"+last))
      else:
        if self.page+1 < self.numpages:
          pages.append((self.page+1, next))
        pages.append((self.numpages, last))
    else:
      pages = []
    pagelinks = [self.getpagelink(pagehref, pagenum, pagetext) for pagenum, pagetext in pages]
    return widgets.Division(contents=widgets.Paragraph(contents=[currentpage, pagelinks]), id="toolbar")

class NumberGridCategory(SimpleGridCategory):
    """A grid category that handles numbers"""
    def valuetostring(self, value):
      if self.storageformat in ['DECIMAL', 'DOUBLE'] and isinstance(value, (int, float)):
        return "%.3f" % value
      else:
        return SimpleGridCategory.valuetostring(self, value)


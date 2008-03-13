#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""convert HTML to Excel spreadsheets using the DOM and pyXLWriter
"""

# Copyright 2005 St James Software
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

# from jToolkit.xml.fixminidom import minidom
from xml.dom import minidom
try:
  from cStringIO import StringIO
except ImportError:
  from StringIO import StringIO
try:
  import pyXLWriter
except ImportError, e:
  pyXLWriter = None
  pyXLWriterImportError = e

class DOM2xls:
  def __init__(self, sourcedom):
    self.sourcedom = sourcedom
    self.celltext = {}
    self.colors = {}
    self.newcolor = 8
  def makeformat(self, baseformat=None, **properties):
    """makes an excel format"""
    format = self.workbook.add_format()
    if baseformat:
      format.assign(baseformat)
    format.set_properties(**properties)
    return format
  def getcolor(self, colorstring):
    """makes an excel colour out of the format string"""
    colorstring = colorstring.lower().encode("utf-8")
    if colorstring in self.colors:
      return self.colors[colorstring]
    excelcolor = self.workbook.set_custom_color(self.newcolor, colorstring)
    self.colors[colorstring] = self.newcolor
    self.newcolor += 1
    return excelcolor
  def convertnode(self, worksheet, row, col, node, format=None):
    # ancestry = ""
    # parentnode = node
    # while parentnode:
    #   ancestry = parentnode.nodeName + " > " + ancestry
    #   parentnode = parentnode.parentNode
    # print ancestry, row, col
    # handle formatting
    if isinstance(node, minidom.Element) and node.hasAttribute("bgcolor"):
      bgcolor = node.getAttribute("bgcolor")
      excelbgcolor = self.getcolor(bgcolor)
      format = self.makeformat(format, bg_color=excelbgcolor)
    # handle various node types
    if node.nodeType == minidom.Node.DOCUMENT_NODE:
      for childnode in node.childNodes:
        row, col = self.convertnode(worksheet, row, col, childnode)
      return row, col
    elif node.nodeName in ("html", "body", "form"):
      for childnode in node.childNodes:
        row, col = self.convertnode(worksheet, row, col, childnode)
      return row, col
    elif node.nodeName == "head":
      return row, col
    elif node.nodeType == minidom.Node.TEXT_NODE:
      if node.data.strip():
        textdata = node.data.encode("utf-8")
        textdata = textdata.replace("\n", "")
        if (row, col) in self.celltext:
          textdata = self.celltext[row, col] + " " + textdata
        self.celltext[row, col] = textdata
        worksheet.write([row, col], textdata, format)
      return row, col
    elif node.nodeName == "input":
      textdata = node.getAttribute("value").replace("\n", " ")
      if textdata.strip():
        textdata = textdata.encode("utf-8")
        textdata = textdata.replace("\n", "")
        if (row, col) in self.celltext:
          textdata = self.celltext[row, col] + " " + textdata
        self.celltext[row, col] = textdata
        worksheet.write([row, col], textdata, format)
      return row, col
    elif node.nodeName in ("b", "i", "u"):
      newformat = {"b": "bold", "i": "italic", "u": "underline"}[node.nodeName]
      format = self.makeformat(format, **{newformat: 1})
      for childnode in node.childNodes:
        row, col = self.convertnode(worksheet, row, col, childnode, format)
      return row, col
    elif node.nodeName in ("div", "p", "span", "tbody", "textarea"):
      for childnode in node.childNodes:
        row, col = self.convertnode(worksheet, row, col, childnode, format)
      row += 1
      return row, col
    elif node.nodeName == "table":
      childrow, childcol = row, col
      for childnode in node.childNodes:
        childrow, childcol = self.convertnode(worksheet, childrow, childcol, childnode, format)
      return childrow, col
    elif node.nodeName == "tr":
      if node.hasAttribute("rowspan"):
        rowspan = int(node.getAttribute("rowspan").strip())
      else:
        rowspan = 1
      childrow, childcol = row, col
      for childnode in node.childNodes:
        childrow, childcol = self.convertnode(worksheet, childrow, childcol, childnode, format)
      row += rowspan
      return row, col
    elif node.nodeName == "td":
      if node.hasAttribute("colspan"):
        colspan = int(node.getAttribute("colspan").strip())
      else:
        colspan = 1
      for childnode in node.childNodes:
        self.convertnode(worksheet, row, col, childnode, format)
      col += colspan
      return row, col
    elif node.nodeName == "img":
      textdata = node.getAttribute("alt").replace("\n", " ")
      if textdata.strip():
        textdata = textdata.encode("utf-8")
        textdata = textdata.replace("\n", "")
        if (row, col) in self.celltext:
          textdata = self.celltext[row, col] + " " + textdata
        self.celltext[row, col] = textdata
        worksheet.write([row, col], textdata, format)
      return row, col
    elif True:
      unknownformat = self.workbook.add_format(bold = 1, color = "blue")
      worksheet.write([row, col], node.nodeName.encode("utf-8"), unknownformat)
      xml = node.toxml().encode("utf-8").replace("\n", " ")
      worksheet.write([row, col+1], xml, format)
      row += 1
      childrow, childcol = row, col+1
      for childnode in node.childNodes:
        childrow, childcol = self.convertnode(worksheet, childrow, childcol, childnode)
      return childrow+1, col
    else:
      return row, col
  def convert(self, xlsfile):
    """converts the html to xls and writes to the given xls file (can be a filename or a real file or a StringIO)"""
    if pyXLWriter is None:
      raise ImportError("Could not import pyXLWriter: %s" % pyXLWriterImportError)
    self.workbook = pyXLWriter.Writer(xlsfile)
    worksheet = self.workbook.add_worksheet()
    self.convertnode(worksheet, 0, 0, self.sourcedom)
    self.workbook.close()

def html2xls(htmlfilename, xlsfile):
  htmlsource = open(htmlfilename).read()
  sourcedom = minidom.parseString(htmlsource)
  converter = DOM2xls(sourcedom)
  converter.convert(xlsfile)

def main():
  import sys
  import os
  htmlfilename = sys.argv[1]
  if len(sys.argv) > 2:
    xlsfilename = sys.argv[2]
  else:
    if htmlfilename.endswith(".htm"):
      xlsfilename = htmlfilename.replace(".htm", ".xls")
    elif htmlfilename.endswith(".html"):
      xlsfilename = htmlfilename.replace(".html", ".xls")
    else:
      xlsfilename = htmlfilename + ".xls"
  html2xls(htmlfilename, xlsfilename)

if __name__ == "__main__":
  main()


#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""form module: holds the classes that are responsible for building up forms"""

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
from jToolkit.widgets import spellui
from jToolkit.widgets import table
from jToolkit.widgets import thumbgallery
from jToolkit.data import dates
from jToolkit import attachments
import csv

class FormCategory:
  def __init__(self, formname, name, altname, label, value, usescript=0):
    self.formname = formname
    self.name = name
    if altname is None:
      self.altname = name
    else:
      self.altname = altname
    self.label = label
    self.options = []
    self.valuemaps = []
    self.value = value
    self.usescript = usescript
    self.valuemapisdict = 0

  def setposition(self, row, col, rowspan, colspan):
    """set the position of the widget"""
    self.row, self.col, self.rowspan, self.colspan = row, col, rowspan, colspan

  def setformatting(self, displayformat, storageformat, formatoptions):
    """sets various formatting options"""
    self.displayformat, self.storageformat, self.formatoptions = displayformat, storageformat, formatoptions
    
  def setdisplayoptions(self, mode, displaytype, alwaysallow):
    self.mode = mode
    self.readonly = (mode == 'view')
    self.displaytype = displaytype
    self.alwaysallow = alwaysallow

  def addoption(self, value, description):
    self.options.append((value, description))

  def addvaluemap(self, value, childrenmap):
    self.valuemaps.append((value, childrenmap))

  def getwidget(self):
    """returns the widget representing this form category"""
    if self.displaytype == 'hidden':
      return ""
    widget = None
    extras = []
    style = self.getstyle()
    if isinstance(self.value, list):
      valuestr = [self.valuetostring(subvalue) for subvalue in self.value]
    else:
      valuestr = self.valuetostring(self.value)
    if self.displaytype in ('attachment', 'imagesattachment') and self.mode == 'filter':
      self.options = [('', ''),
                      ('no', self.session.localize('No')),
                      ('yes', self.session.localize('Yes'))]
      self.displaytype = 'combo'
    elif self.displaytype == 'combo' and (self.mode == 'filter' or isinstance(valuestr, list)):
      self.displaytype = 'multicombo'
    if self.displaytype in ('combo', 'multicombo'):
      comboattribs = {'name':self.name,  'style':style}
      if self.usescript:
        comboattribs['onchange'] = self.name+'.handleselection()'
        comboattribs['onclick'] = self.name+'.handleclick()'
      if self.mode == 'view':
        widget = widgets.Input({'name':self.name, 'value':valuestr, 'style':style}, readonly=self.readonly)
      else:
        # if the value is a list it has to be a multicombo to display it
        # if it is in filter mode we want to be able to select multiple values too...
	if self.displaytype == 'multicombo':
          if isinstance(valuestr, list):
            comboattribs["value"] = valuestr
          else:
            csvreader = csv.reader([valuestr])
            comboattribs["value"] = csvreader.next()
          comboattribs["size"] = "5"
          widget = widgets.MultiSelect(comboattribs, options = self.options)
        else:
          comboattribs['value'] = valuestr
          widget = widgets.Select(comboattribs, options = self.options)
    elif self.displaytype == 'weblink':
      if (self.readonly or self.mode == "view") and (valuestr and valuestr.startswith("http://") or valuestr.startswith("ftp://")):
        widget = widgets.Link(valuestr, valuestr, {"target": "_blank"})
      else:
        widget = widgets.Input({'name':self.name, 'value':valuestr, 'style':style}, readonly=self.readonly)
    elif self.displaytype == 'update':
      widget =  widgets.Input({'name':self.name, 'value':valuestr, 'style':style}, readonly=self.readonly)
    elif self.displaytype == 'hiddenwidget':
      widget =  widgets.Input({'name':self.name, 'value':valuestr, 'style':style, 'type': 'hidden'}, readonly=self.readonly)
    elif self.displaytype == 'password':
      widget =  widgets.Input({'name':self.name, 'value':valuestr, 'style':style, 'type':'password'}, readonly=self.readonly)
    elif self.displaytype == 'text':
      widget = widgets.TextArea({'name':self.name, 'style':style, 'rows':self.rowspan}, readonly=self.readonly, contents=valuestr)
    elif self.displaytype == 'spelltext':
      widget = spellui.SpellCheckable({'name':self.name, 'style':style, 'rows':self.rowspan}, readonly=self.readonly, contents=valuestr)
    elif self.displaytype == 'imagesattachment':
      multiattachment = attachments.MultiAttachment(self.instance, encodedstring=self.value)
      widget = thumbgallery.ImageAttachmentsWidget(self.session, self.name, self.rowid, multiattachment, self.mode ,self.instance.gallerydir)
    elif self.displaytype in 'attachment':
      multiattachment = attachments.MultiAttachment(self.instance, encodedstring=self.value)
      widget = attachments.MultiAttachmentsWidget(self.session, self.name, self.rowid, multiattachment, self.mode)
    else:
      widget = 'displaytype:'+self.displaytype
    if getattr(self, 'invisible', False) and isinstance(widget, widgets.Widget):
      widget.attribs.setdefault('style', {})['visibility'] = 'hidden'
      self.label.attribs.setdefault('style', {})['visibility'] = 'hidden'
      # special attribute 
      widget.attribs["jtoolkit:onlyifvisible"] = 'true'
    if self.usescript:
      # add a script after the combo...
      script = widgets.Script('text/javascript', self.getcomboscript())
      extras.append(script)
    if extras:
      return widgets.PlainContents([widget, extras])
    else:
      return widget

  def getstyle(self):
    style = {'width':'100%'}
    for option, value in self.formatoptions.iteritems():
      if option == 'TEXTCOLOR':
        style['color'] = widgets.getrgb(value, '&H000000')
      elif option == 'BACKCOLOR':
        style['background-color'] = widgets.getrgb(value, '&HFFFFFF')
      elif option == 'FONT' and value is not None:
        fontstyles = value.lower().split()
        for fontstyle in fontstyles:
          if fontstyle == 'bold': style['font-weight'] = 'bold'
          elif fontstyle == 'italic': style['font-style'] = 'italic'
    return style

  def valuetostring(self, value):
    """based on the category, returns value as a string that can be displayed"""
    # TODO: look at combining this and other methods with GridCategory...
    if self.storageformat in ['TEXT','STRING']:
      if value is None:
        return ''
      elif isinstance(value, basestring):
        return value
      else:
        return str(value)
    elif self.storageformat in ['INTEGER', 'DECIMAL']:
      return str(value)
    elif self.storageformat == 'DATETIME':
      return dates.formatdate(value, self.displayformat)
    elif value is None:
      return ''
    elif isinstance(value, basestring):
      return value
    else:
      return str(value)

  def getcomboscript(self):
    # returns script that handles setting hierarchical values etc...
    # remember all the options...
    script = "var alloptions = {"
    # create a dictionary string for all the options
    optionvalues = [widgets.jsquote(value)+":"+widgets.jsquote(desc.strip()) for value,desc in self.options]
    script += ",".join(optionvalues)
    script += "}\r"
    # set all the valuemaps
    script += "var valuemaps = {"
    # create a dictionary string for all the valuemaps
    script += ",".join(["%s:{%s}" % (widgets.jsquote(value),valuemaps) for value,valuemaps in self.valuemaps])
    script += "}\r"
    # handle alternate name
    if self.name != self.altname:
      script += "document.%s.%s = document.%s.%s\r" % (self.formname, self.altname, self.formname, self.name)
    # initialize the object with methods etc...
    alwaysallow = widgets.jsquote(self.alwaysallow)
    clearonselect = getattr(self, "clearchildrenonselect", [])
    if clearonselect:
      clearonselect = "{" + ", ".join(["'%s': undefined" % child for child in clearonselect]) + "}"
    else:
      clearonselect = "undefined"
    script += "setupcombo(document.%s.%s, alloptions, valuemaps, %s, %d, 0, 0, %s)\r" \
            % (self.formname, self.name, alwaysallow, self.valuemapisdict, clearonselect)
    return script

class Form(table.TableLayout):
  """this is a generic form layout object"""
  def __init__(self, formname, categories, labelattribs = {}, widgetattribs = {}):
    table.TableLayout.__init__(self, newattribs={'width':'100%','border':'0'})
    self.formname = formname
    self.labelattribs = {'valign':'top'}
    self.widgetattribs = {'valign':'top'}
    self.labelattribs.update(labelattribs)
    self.widgetattribs.update(widgetattribs)
    self.categories = categories
    self.makeform()
    
  def makeform(self):
    # fill up the table with the categories' labels and widgets... 
    for categoryname, category in self.categories.iteritems():
      self.setcategorycells(category)
    self.hidecoveredcells()
    self.calcweights()

  def setcategorycells(self, category):
    """sets the cells for the given category object"""
    if category.displaytype != 'hidden':
      labelcell = table.TableCell(category.label, rowspan=category.rowspan, newattribs=self.labelattribs)
      labelcell.width = 1
      self.setcell(category.row, category.col*2-1, labelcell)
      widgetcell = table.TableCell(category.getwidget(), rowspan=category.rowspan, colspan=category.colspan*2-1, newattribs=self.widgetattribs)
      widgetcell.width = 2
      self.setcell(category.row, category.col*2, widgetcell)

class SimpleForm(widgets.Form):
  """base class viewing/editing form for config"""
  def __init__(self, record, formname, columnlist, formlayout, optionsdict, extrawidgets):
    self.record = record
    self.formname = formname
    self.columnlist = columnlist
    self.formlayout = formlayout
    self.optionsdict = optionsdict
    self.form = Form(self.formname, self.getcategories())
    self.form.shrinkrange()
    self.form.fillemptycells()
    widgetlist = [self.form] + extrawidgets
    attribs = {'name':self.formname, 'enctype': "multipart/form-data"}
    widgets.Form.__init__(self, contents = widgetlist, newattribs = attribs)

  def getcategories(self):
    """gets the categories for the form..."""
    categories = {}
    for name, title, tooltip in self.columnlist:
      value = self.record[name]
      label = widgets.Tooltip(tooltip, title)
      category = FormCategory(self.formname, name, None, label, value)
      category.setformatting(displayformat='',storageformat='TEXT',formatoptions={})
      if name in self.optionsdict:
        options = self.optionsdict[name]
        if value is None: value = ''
        if value.lower() not in [option.lower() for option in options]:
          options = [value] + options
        category.setdisplayoptions(mode='modify',displaytype='combo',alwaysallow=[])
        for option in options:
          category.addoption(option, option)
      elif name.lower().find('password') != -1:
        category.setdisplayoptions(mode='modify',displaytype='password',alwaysallow=[])
      else:
        category.setdisplayoptions(mode='modify',displaytype='update',alwaysallow=[])
      categories[name] = category
    self.arrange(categories)
    return categories

  def arrange(self, categories):
    for rownum, columns in self.formlayout.iteritems():
      colnum = 0
      for columnname in columns:
        colnum += 1
        if columnname is not None:
          category = categories[columnname]
          category.setposition(rownum,colnum,1,1)


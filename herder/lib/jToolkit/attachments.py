#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""attachments module handles all storing and retrieving of attachments, however that's done..."""

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

import types
import os
import os.path
from jToolkit.widgets import widgets
from jToolkit import pdffile

class AttachmentError(ValueError):
  """error indicating a problem with an attachment"""
  def __init__(self, message):
    self.message = message

class Attachment:
  # Attributes:
  # attachmentsdir
  # filename
  # content_type
  # contents
  # storedfilename
  def __init__(self, instance, field=None, encodedstring=None, filename=None, content_type = None):
    """initialize an Attachment, either from a field, an encodedstring or a filename"""
    self.instance = instance
    self.attachmentsdir = getattr(instance, 'attachmentsdir', None)
    self.reset()
    if field is not None:
      self.createfromfield(field, getattr(instance, 'maxattachmentsize', None))
    elif encodedstring is not None:
      self.decode(encodedstring)
    elif filename is not None:
      self.createfromfile(filename,content_type)

  def getbasefilename(self, filename):
    """gets the base of a filename in a platform independent way"""
    # IE submits the whole path. lets just get the filename in this case
    if "\\" in filename:
      filename = filename[filename.rfind("\\")+1:]
    if "/" in filename:
      filename = filename[filename.rfind("/")+1:]
    return filename

  def createfromfield(self, field, maxattachmentsize=None):
    """initialize the attachment from the given field (http)"""
    self.filename = self.getbasefilename(field.filename)
    self.content_type = field.type
    self.contents = field.value
    # TODO: put an error in the audit log...
    if maxattachmentsize:
      if len(self.contents) >= maxattachmentsize * 1024:
        raise AttachmentError, self.localize("attachment is too large")

  def createfromfile(self, filename, content_type):
    """initialize the attachment from the file with the given name and content_type"""
    self.filename = self.getbasefilename(filename)
    self.content_type = content_type
    self.contents = open(filename, 'rb').read()

  def decode(self, attachmentstring):
    """decodes the database value, simply breaking it up into parts..."""
    if attachmentstring.count("\n") >= 2:
      self.filename, content_type, self.storedfilename = attachmentstring.split("\n",2)
      self.content_type = str(content_type) # in case of unicode...
    else:
      self.reset()

  def encode(self, includequotes=True):
    """encode the attachment for storing in the database (a reference to the file & type)"""
    if len(self.filename) > 0:
      if isinstance(self.filename, str):
        encodedstring = self.filename.decode("utf8")
      else:
        encodedstring = self.filename
      encodedstring += "\n"+self.content_type+"\n"+self.storedfilename
      if includequotes:
        return "'" + encodedstring.replace("'","''") + "'"
      else:
        return encodedstring
    else:
      return None

  def localize(self, message):
    """dummy localize method..."""
    return message

  def isvalid(self):
    """returns whether this represents a valid attachment or not..."""
    return self.filename is not None

  def getcontents(self):
    """return the contents of the attachment, reading it from disk if neccessary"""
    if self.contents is not None:
      return self.contents
    elif self.storedfilename is not None:
      self.readcontents()
      return self.contents
    else:
      return None

  def fullstoredpath(self):
    """get the full path to the attachment file"""
    if self.attachmentsdir is None:
      raise ValueError("attachments dir not set...")
    if not os.path.isdir(self.attachmentsdir):
      os.mkdir(self.attachmentsdir)
    return os.path.join(self.attachmentsdir, self.storedfilename)

  def setstoragepath(self, attachmentsdir):
    """Sets instance.attachmentsdir"""
    self.attachmentsdir = attachmentsdir

  def readcontents(self):
    """reads contents out of the file storing this attachment"""
    f = open(self.fullstoredpath(), 'rb')
    self.contents = f.read()
    f.close()

  def savecontents(self, storedfilename):
    """saves contents to the given file, remembering it for the future..."""
    self.storedfilename = storedfilename
    f = open(self.fullstoredpath(), 'wb')
    f.write(self.contents)
    f.close()

  def append(self, extracontents, storedfilename = None):
    """append extracontents to the storedfilename (can specify file if neccessary)"""
    if storedfilename is not None: self.storedfilename = storedfilename
    f = open(self.fullstoredpath(), 'ab')
    if isinstance(extracontents, unicode):
      f.write(extracontents.encode('utf8'))
    else:
      f.write(extracontents)
    f.close()

  def deletefile(self, storedfilename = None):
    """deletes the attachment's file from the disk (can specify name if neccessary)"""
    if storedfilename is not None: self.storedfilename = storedfilename
    path = self.fullstoredpath()
    if os.path.exists(path):
      os.remove(path)

  def reset(self):
    """blanks out all the fields of this object"""
    self.filename = None
    self.content_type = None
    self.contents = None
    self.storedfilename = None

  def geturl(self, rowid, category):
    """returns a url that refers to this attachment"""
    filename = self.filename
    if filename is None:
      return 'attachments/missing'
    n = len(filename)
    while n > 0 and (filename[n-1].isalnum() or filename[n-1] in ' _.-'):
      n -= 1
    return "attachments/%s?rowid=%s&name=%s" % (filename[n:],rowid,category)

  def dbrepr(self):
    """how to represent this object for storing in the database"""
    encodedstring = self.encode()
    if encodedstring is None:
      return "null"
    elif isinstance(encodedstring, str):
      try:
        return encodedstring.decode("utf8")
      except LookupError:
        # this is to try and avoid an initialization problem in the codecs module
        # TODO: review this and remove it once the problem goes away
        return encodedstring.decode("utf8")
    elif isinstance(encodedstring, unicode):
      return encodedstring
    else:
      return str(encodedstring)

class MultiAttachment:
  def __init__(self, instance, fields=None, encodedstring=None, filenames=None):
    """initialize a MultiAttachment, either from fields, an encodedstring or a list of filenames"""
    self.attachmentsdir = getattr(instance, 'attachmentsdir', None)
    self.attachments = []
    self.instance = instance
    if fields is not None:
      for field in fields:
        attachment = Attachment(self.instance, field=field)
        self.addattachment(attachment)
    if encodedstring is not None:
      self.decode(encodedstring)
    if filenames is not None:
      for filename in filenames:
        attachment = Attachment(self.instance, filename=filename)
        self.addattachment(attachment)

  def addattachment(self, attachment):
    """adds the attachment to the multiattachment list"""
    self.attachments.append(attachment)

  def removeattachment(self, attachmentnum):
    """marks the attachment for removal"""
    self.attachments[attachmentnum] = False

  def decode(self, attachmentstring):
    """decodes the database value, simply breaking it up into parts..."""
    lines = attachmentstring.split("\n")
    while len(lines) >= 3:
      attachment = Attachment(self.instance, encodedstring="\n".join(lines[:3]))
      self.addattachment(attachment)
      lines = lines[3:]

  def encode(self, includequotes=True):
    """encode the attachment for storing in the database (a reference to the file & type)"""
    if self.attachments:
      encodedstring = ""
      encodedstring = "\n".join([attachment.encode(includequotes=False) for attachment in self.attachments if attachment != False])
      if not encodedstring:
        encodedstring = " "
      if includequotes:
        return "'" + encodedstring.replace("'","''") + "'"
      else:
        return encodedstring
    else:
      return None

  def savecontents(self, storedfilename):
    """saves contents to the given file, remembering it for the future..."""
    for attachmentnum, attachment in enumerate(self.attachments):
      # attachment.contents will be None if this field is unchanged
      if not attachment:
        continue
      if isinstance(attachment, AttachmentError):
        return attachment.message
      if attachment.contents is not None:
        attachment.savecontents("%s-%d" % (storedfilename, attachmentnum))

  def deletefile(self, storedfilename = None):
    """deletes the attachment's file from the disk (can specify name if neccessary)"""
    for attachmentnum, attachment in enumerate(self.attachments):
      if not attachment:
        continue
      if storedfilename is None:
        attachment.deletefile()
      else:
        attachment.deletefile("%s-%d" % (storedfilename, attachmentnum))

  def geturl(self, rowid, category, attachmentnum):
    """returns a url that refers to this attachment"""
    if not 0 <= attachmentnum < len(self.attachments):
      return 'attachments/missing'
    attachment = self.attachments[attachmentnum]
    if attachment:
      filename = attachment.filename
    else:
      filename = None
    if filename is None:
      return 'attachments/missing'
    n = len(filename)
    while n > 0 and (filename[n-1].isalnum() or filename[n-1] in ' _.-'):
      n -= 1
    return "attachments/%s?rowid=%s&attachmentnum=%d&name=%s" % (filename[n:],rowid,attachmentnum,category)

  def dbrepr(self):
    """how to represent this object for storing in the database"""
    encodedstring = self.encode()
    if encodedstring is None:
      return "null"
    elif isinstance(encodedstring, str):
      try:
        return encodedstring.decode("utf8")
      except LookupError:
        # this is to try and avoid an initialization problem in the codecs module
        # TODO: review this and remove it once the problem goes away
        return encodedstring.decode("utf8")
    elif isinstance(encodedstring, unicode):
      return encodedstring
    else:
      return str(encodedstring)

class MultiAttachmentsWidget(widgets.PlainContents):
  """
  an attachment field that is repeatable
  """

  def __init__(self, session, name, rowid, multiattachment, mode):
    """construct the widget displaying the attachments in multiattachment"""
    self.session = session
    self.name = name
    self.rowid = rowid
    self.multiattachment = multiattachment
    self.mode = mode
    contents = self.buildwidget()
    widgets.PlainContents.__init__(self, contents)

  def buildwidget(self):
    """gets the contents of the widget..."""
    links = self.getlinks()
    if self.mode in ("add", "modify"):
      javascript = widgets.Script("text/javascript", '', newattribs={'src':'js/attachments.js'})
      addlink = self.getselectbutton()
      return [javascript, links, addlink]
    elif self.mode == "view":
      if len(links):
        return links
      else:
        return self.session.localize('(no attachment)')

  def getlinks(self):
    """returns all the attachment links"""
    links = []
    if self.multiattachment.attachments:
      for attachmentnum, attachment in enumerate(self.multiattachment.attachments):
        if attachment.isvalid():
          link = self.getlink(attachmentnum, attachment)
          links.append(link)
    return links

  def getlink(self, attachmentnum, attachment):
    """gets the link to the attachment"""
    attachmentlink = self.multiattachment.geturl(self.rowid, self.name, attachmentnum)
    link = widgets.Link(attachmentlink, attachment.filename, {'target':'attachmentpage'})
    if self.mode in ("add", "modify"):
      removefield = widgets.Input({'type':'hidden', 'name': "%s.remove%d" % (self.name, attachmentnum), 'value':''})
      removelink = self.getremovelink()
      link = widgets.Paragraph([link, removefield, removelink])
    return link

  def getremovelink(self):
    """creates a link to remove an attachment - this must be positioned correctly in the form to find the attachment"""
    # TODO: rather pass the attachmentnum in so we find it without relying on form position
    javascriptcall = "MarkRemoved(this,\'%s\'); return false" % (self.name)
    removetext = self.session.localize("remove")
    removetooltip = self.session.localize("remove this attachment")
    restoretext = self.session.localize("restore")
    restoretooltip = self.session.localize("this attachment has been removed. click here to restore it")
    linkattribs = {"onClick": "javascript:%s" % javascriptcall, "title": removetooltip,
                   "removetext": removetext, "removetooltip": removetooltip,
                   "restoretext": restoretext, "restoretooltip": restoretooltip}
    return widgets.Link("#", removetext, linkattribs)

  def getselectbutton(self):
    """returns a button that lets the user select an attachment to upload"""
    newattachmentnum = len(self.multiattachment.attachments)
    javascriptcall = "if (this.fieldnumber == void(0)) { this.fieldnumber = %d }; " % (newattachmentnum)
    javascriptcall += "AddInput(this,\'%s\'); return false" % (self.name)
    attachtext = self.session.localize("attach a file")
    return widgets.Link("#", attachtext, {"onClick":"javascript:%s" % javascriptcall})

def isattachment(value):
  if type(value) == types.InstanceType:
    if isinstance(value, Attachment):
      return 1
    if isinstance(value, MultiAttachment):
      return 1
  return 0

def isattachmenterror(value):
  if type(value) == types.InstanceType:
    if isinstance(value, AttachmentError):
      return 1
  return 0

def getPDFContents(page):
  contents = ''
  if page['Kids'].value() is not None:
    for kid in page['Kids'].value():
      if kid['Contents'] is not pdffile.NullObj:
        contents += str(kid['Contents'].value()) + ' '
      contents += getPDFContents(kid)
  return contents

def extractPDFText(pdfcontents):
  # Takes decrypted PDF code and extracts the text
  # TODO: This could probably be done a lot more robustly with sparse
  contents = ''
  nextTd = pdfcontents.find('Td(')
  nextTc = pdfcontents.find('Tc(')

  if nextTd > nextTc and nextTc != -1:
    nextTag = nextTc
  else:
    nextTag = nextTd

  while nextTag != -1:
    pdfcontents = pdfcontents[nextTag+3:]
    contents += pdfcontents[:pdfcontents.index(')Tj')] + " "
    pdfcontents = pdfcontents[pdfcontents.index(')Tj')+3:]
    nextTd = pdfcontents.find('Td(')
    nextTc =  pdfcontents.find('Tc(')

    if nextTd > nextTc and nextTc != -1:
      nextTag = nextTc
    else:
      nextTag = nextTd

  return contents
    
def indexattachment(indexer, rowid, filename, stored_name, contenttype, contents, modify = 0):
  # TODO: There are only certain types of attachment we want to index
  # We should check contenttype here, and, if necessary, pass the contents to a parser to get the text out
  if indexer is not None:
    # First, parse the contents
    parsedcontents = indexer.decodeContents(contenttype, contents)
    if not parsedcontents:
      if contenttype[:4] == "text":
        parsedcontents = contents
      elif contents[1:4] == "PDF":
        if float(contents[5:8]) > 1.3:
          print "Cannot parse PDF %s: Format is too recent.  Please contact St. James Software about configuration options" % filename
	  parsedcontents = ""
        else:
          from cStringIO import StringIO
          pdf = pdffile.PDFFile()
          pdfcontents = StringIO(contents)
          pdf._load(pdffile.Tokeniser(pdffile.FileByteStream(pdfcontents)))
          parsedcontents = extractPDFText(getPDFContents(pdf.Root['Pages']))
      else:
        parsedcontents = ""
    if modify:
      print "Error: cannot modify attachments yet"
      #indexer.modifyDoc({'rowid':rowid},{'filename':filename, 'stored_name': stored_name, 'content-type': contenttype, 'contents': contents})
    else:
      indexer.indexFields({'filename':filename, 'stored_name': stored_name, 'content-type': contenttype, 'contents': parsedcontents, 'rowid': rowid})

def saveattachments(recorddict, rowid, originalvalues, indexer = None):
  """saves all valid attachments in the recorddict, using the given rowid"""
  emptykeys = []
  results = []
  for key, value in recorddict.iteritems():
    result = ""
    if isattachment(value):
      # only save non-empty attachments...
      if isinstance(value, Attachment):
        if len(value.filename) > 0:
          indexattachment(indexer, rowid, value.filename, rowid+'-'+key, value.content_type, value.contents, len(originalvalues) != 0)
          if originalvalues.has_key(key):
            multiattachment = MultiAttachment(value.instance, encodedstring=originalvalues[key])
            multiattachment.addattachment(value)
            result = multiattachment.savecontents(rowid+'-'+key)
          else:
            result = value.savecontents(rowid+'-'+key)
        else:
          # and remove empty ones from the dictionary
          emptykeys.append(key)
      elif isinstance(value, MultiAttachment):
        for i, attach in enumerate(value.attachments):
          if isinstance(attach, Attachment):
            if indexer is not None:
              indexattachment(indexer, rowid, attach.filename, rowid+'-'+key+'-'+str(i), attach.content_type, attach.contents, len(originalvalues) != 0)
        result = value.savecontents(rowid+'-'+key)
    elif isattachmenterror(value):
      # a return value signifies an error
      result = value.message
    results.append(result)
  # only do actual deletion here otherwise you confuse the loop...
  for key in emptykeys:
    del recorddict[key]
  # return any error messages joined together
  return "\n".join([result for result in results if result])

def deleteattachments(recorddict, rowid, searcher = None):
  """deletes all attachments in the recorddict from the disk, using the given rowid
  doesn't update the database (assumes the caller is responsible)"""
  for key, value in recorddict.iteritems():
    if isattachment(value):
      value.deletefile(rowid+'-'+key)
  if searcher:
    searcher.deleteDoc({'rowid':rowid})
    

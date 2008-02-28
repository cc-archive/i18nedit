#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Generate and display thumbnails and selection widgets for dealing with image galleries"""

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

import os
from jToolkit.widgets import table
from jToolkit.widgets import widgets
from jToolkit.web import server
from jToolkit import attachments

def ImportPIL():
  """Import PIL"""
  import Image
  Image.preinit()
  return Image

imageformats = {'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png', 'gif': 'image/png', 'bmp': 'image/bmp'}

# TODO: move this out of being a fully-blown server class

def ThumbnailServer(baseclass):
  class ThumbnailServer(baseclass):
    """the Server that serves the thumbnail pages"""
    def opensharedfolder(self, folderpath):
      """opens the shared folder and remembers the direct path"""
      if not hasattr(self, "sharedfolders"):
        self.sharedfolders = {}
      if folderpath in self.sharedfolders:
        return self.sharedfolders[folderpath]
      else:
        import os
        logondetails, folder = folderpath.split("@", 1)
        if "/" in logondetails:
          username, password = logondetails.split("/", 1)
          os.system("net use %s %s /user:%s" % (folder, password, username))
        else:
          os.system("net use %s %s" % (folder, logondetails))
        self.sharedfolders[folderpath] = folder
        return folder

    def getinstancefolder(self, foldername):
      """returns a folder name configured on the instance"""
      if hasattr(self.instance, foldername):
        folder = getattr(self.instance, foldername)
        if "@" in folder:
          folder = self.opensharedfolder(folder)
        return folder
      else:
        return None

    def getpage(self, pathwords, session, argdict):
      """return a page that will be sent to the user"""
      gallerydir = self.getinstancefolder("gallerydir")
      attachmentsdir = self.getinstancefolder("attachmentsdir")
      if pathwords == ['gallery.htm']:
        gtable = ThumbnailSelector(gallerydir, 'gallery', columns=3)
        submit = widgets.Input({'value':'finished','type':'submit'})
        return widgets.Form([gtable, submit])
      elif pathwords == ['selectimage.htm']:
        return ThumbnailSelectorPage(session, gallerydir, 'gallery', columns=3)
      elif pathwords[:1] == ['gallery']:
        pathwords = pathwords[1:]
        if KnownImageType(pathwords[-1]):
          if len(pathwords) >= 2 and pathwords[-2] == 'thumbnails':
            imagefilename = pathwords[:-2] + [pathwords[-1]]
            imagefilename = os.path.join(gallerydir, *imagefilename)
            ThumbFromImage(imagefilename)
          pic = widgets.PlainContents(None)
          pic.sendfile_path = os.path.join(gallerydir, *pathwords)
          pic.content_type = getcontenttype(pathwords[-1])
          return pic
        if pathwords[-1].endswith(".html"):
          imagefilename = pathwords[-1]
          imagefilename = imagefilename[:imagefilename.rfind(".html")]
          image = widgets.Image(imagefilename)
          backlink = "javascript:history.back(1)"
          backtext = widgets.Link(backlink, "Back")
          imagepage = widgets.Page(imagefilename, [backtext, "<br/>", image])
          return imagepage
      elif pathwords[:1] == ['attachment']:
        pathwords = pathwords[1:]
        if len(pathwords) >= 2 and pathwords[-2] == 'thumbnails':
          imagefilename = pathwords[:-2] + [pathwords[-1]]
          imagefilename = os.path.join(attachmentsdir, *imagefilename)
          ThumbFromImage(imagefilename)
          imagename = argdict.get('name', '')
          pic = widgets.PlainContents(None)
          pic.sendfile_path = os.path.join(attachmentsdir, *pathwords)
          pic.content_type = getcontenttype(imagename)
          return pic
      return super(ThumbnailServer, self).getpage(pathwords, session, argdict)
  return ThumbnailServer

class ThumbnailGallery(table.TableLayout):
  """
  a gallery of thumbnails
  """
  
  def __init__(self, folder, baseurl, rows=None, columns=None):
    """
    folder is the path of the images
    baseurl is the url to server the images on the server (absolute or relative to the current page)
    if rows is defined then the appropriate number of columns will be made
    if columns is defined then the appropriate number of rows will be made
    """

    table.TableLayout.__init__(self)

    #first create the thumbnails
    thumbs = ThumbsFromFolder(folder)
    
    if rows is not None:
      columns = len(thumbs)/rows
    
    if columns is not None:
      rows = len(thumbs)/columns

    thumbstack = thumbs
    for row in range(rows):
      for col in range(columns):
        image,thumb = thumbstack.pop()
        #assemble this part of the path into the right format for an image src
        thumbsrc = '/'.join([baseurl] + list(os.path.split(thumb)))
        imagesrc = '/'.join([baseurl] + list(os.path.split(image)))
        pic = widgets.Image(thumbsrc)
        link = widgets.Link(imagesrc, [pic, image], {'target':'jlogbookimagepreview'})
        self.setcell(row,col,table.TableCell(link))

class ThumbnailSelector(table.TableLayout):
  """
  a gallery widget where thumbnails can be selected
  """
  
  def __init__(self, folder, baseurl, rows=None, columns=None):
    """
    folder is the path of the images
    baseurl is the url to server the images on the server (absolute or relative to the current page)
    if rows is defined then the appropriate number of columns will be made
    if columns is defined then the appropriate number of rows will be made
    """
    
    table.TableLayout.__init__(self, {'border':1,
                                      'style':"border-collapse: collapse;",
                                      'width=':'100%',
                                      'cellspacing':10,
                                      'cellpadding':10})
    #first create the thumbnails, and make them relative to the folder
    if not folder.endswith(os.sep):
      folder += os.sep
    thumbs = [(image.replace(folder, "", 1), thumb.replace(folder, "", 1)) for image,thumb in ThumbsFromFolder(folder)]
    if rows is not None:
      columns = (len(thumbs)+rows-1)/rows
    
    if columns is not None:
      rows = (len(thumbs)+columns-1)/columns

    checkboxcounter = 0
    for row in range(rows):
      for col in range(columns):
        checkboxcounter += 1
        thumbid = row*columns+col
        if thumbid >= len(thumbs):
          continue
        image,thumb = thumbs[thumbid]
        #assemble this part of the path into the right format for an image src
        thumbsrc = '/'.join([baseurl] + list(os.path.split(thumb)))
        imagesrc = '/'.join([baseurl] + list(os.path.split(image)))
        pic = widgets.Image(thumbsrc,{'border':1})
        link = widgets.Link(imagesrc, [pic, image], {'target':'jlogbookimagepreview'})
        checkbox = widgets.Input({'type':'checkbox',
                                  'value':"%s"%image,
                                  'name':"checkbox%i"%checkboxcounter,
                                  'thumbsrc':thumbsrc})
        self.setcell(row,col,table.TableCell([checkbox,link],{'valign':'bottom'}))

class ThumbnailSelectorPage(widgets.Page):
  """
  This creates a page that can be opened from another window, select thumbnails, and return them to the main form
  """
  def __init__(self, session, folder, baseurl, rows=None, columns=None):
    """
    constructs the thumbnail selector page
    """
    selector = ThumbnailSelector(folder, baseurl, rows, columns)
    javascript = widgets.Script("text/javascript", """
    function updatemainform(thumbnailform)
    {
      var attachmentnum=0;
      for (i=0;i<thumbnailform.elements.length;i++)
      {
        if (thumbnailform.elements[i].checked)
        {
          attachmentnum += 1;
          //for each checked item create a new hidden input element in the calling form, just above the button
          //note: selectbutton was stored in this window in the onclick method of the button
          var checkbox = thumbnailform.elements[i];
          var imagename = checkbox.value;
          var thumbsrc = checkbox.getAttribute('thumbsrc');

          var newhtml = "<input type=hidden"+
                        " name='"+(window.categoryname + attachmentnum)+
                        "' value='" + imagename + "'>";
          
          //now insert a thumbnail (we get the src for the thumbnail from the checkbox)
          newhtml += "<img src='" + thumbsrc + "'> " + imagename + " ";

          //append a link to remove the paragraph containing the thumbnail
          newhtml += "<a href='#' onclick='this.parentNode.parentNode.removeChild(this.parentNode);return false'>" +
                     "%s</a>";

          selectbutton.addattachment(newhtml);
        }
      }
    }
    """ % session.localize("remove"))
    submit = widgets.Input({'value':'Finished','type':'button','onclick':'updatemainform(this.form) ; window.close()'})
    selectorform = widgets.Form([selector,
                                widgets.PlainContents('<br>'),
                                widgets.ContentWidget('center',submit)])
    widgets.Page.__init__(self, contents=[javascript, selectorform])
    
class ImageAttachmentsWidget(attachments.MultiAttachmentsWidget):
  """
  an attachments field that contains image and selects them from the thumbnail gallery
  """
  def __init__(self, session, name, rowid, multiattachment, mode, folder):
    #create a link that spawns file inputs
    self.folder = folder
    attachments.MultiAttachmentsWidget.__init__(self, session, name, rowid, multiattachment, mode)

  def getlink(self, attachmentnum, attachment):
    """
    gets the link to the attachment
    (overrides MultiAttachmentsWidget)
    """
    attachmentlink = self.multiattachment.geturl(self.rowid, self.name, attachmentnum)

    #create the thumbnail
    image = attachment.fullstoredpath()
    folder = os.path.dirname(image)
    if not folder.endswith(os.sep):
      folder += os.sep
    thumb = getthumbnailpath(image)
    image = image.replace(folder, "", 1)
    thumb = thumb.replace(folder, "", 1)
    thumbsrc = '/'.join(['attachment'] + list(os.path.split(thumb))) + '?name=%s' % attachment.filename
    pic = widgets.Image(thumbsrc,{'border':1})

    link = widgets.Link(attachmentlink, [pic,attachment.filename], {'target':'attachmentpage'})
    if self.mode in ("add", "modify"):
      removefield = widgets.Input({'type':'hidden', 'name': "%s.remove%d" % (self.name, attachmentnum), 'value':''})
      javascriptcall = "MarkRemoved(this,\'%s\'); return false" % (self.name)
      removelink = self.getremovelink()
      link = widgets.Paragraph([link, removefield, removelink])
    return link

  def buildwidget(self):
    """gets the contents of the widget..."""
    links = self.getlinks()
    if self.mode in ("add", "modify"):
      javascript = widgets.Script("text/javascript", '', newattribs={'src':'js/attachments.js'})
      addlink = self.getselectbutton()
      return [javascript, links, addlink]
    elif self.mode == "view":
      if len(links):
        thumbnaillinks = []
        for link in links:
          thumbnaillinks.extend([link,"<br>"])
        return thumbnaillinks
      else:
        return self.session.localize('(no attachment)')
    elif self.mode == "filter":
      options = [('', ''),
                 ('no', self.session.localize('No')),
                 ('yes', self.session.localize('Yes'))]
      return widgets.Select({'name': self.name}, options)

  def getselectbutton(self):
    """returns a button that lets the user select the images to be attached..."""
    javascript = widgets.Script("text/javascript","""
    function addattachment(attachmenthtml)
    {
         var newparagraph = document.createElement("p");
         newparagraph.innerHTML = attachmenthtml;
         this.parentNode.insertBefore(newparagraph, this);
    }
    function PopupThumbnailSelectorPage(selectbutton){
      selectbutton.addattachment = addattachment;
      selectorwindow = window.open("selectimage.htm", "selectimages", "width=350,height=500,scrollbars=1");
      selectorwindow.selectbutton = selectbutton;
      selectorwindow.categoryname = \"%s\";
    }
    """ % self.name)
    input = widgets.Link('#', 'add images',
                        {'onclick':'PopupThumbnailSelectorPage(this);return false'})
    layer = widgets.Division(input)
    return widgets.PlainContents([javascript,layer])

def getext(filename):
  """returns the filename's extension without the ."""
  return os.path.splitext(filename)[1].replace(os.extsep, '', 1)

def KnownImageType(image):
  return getext(image).lower() in imageformats

def getcontenttype(image):
  return imageformats[getext(image).lower()]

def ThumbsFromFolder(folder):
  """
  Create a collection of thumbnail images from the images in folder
  Returns a list of (image,thumbnail) pairs where image and thumbnail are
  paths to the origional image and the created thumbnail
  """
  
  #make sure the folder exists
  if not os.path.isdir(folder):
    raise IOError("Image Folder is not a valid directory: %s" % folder)

  #read images in the folder into a list
  images = [os.path.join(folder,image) for image in os.listdir(folder) if KnownImageType(image)]
  thumbs = []
  for image in images:
    thumbs.append((image, getthumbnailpath(image)))
  return thumbs

def getthumbnailpath(imagepath, thumbnaildir=None):
  """find the path the thumbnail should be in..."""
  if thumbnaildir is None:
    thumbnaildir = os.path.join(os.path.dirname(imagepath), "thumbnails")
  return os.path.join(thumbnaildir, os.path.basename(imagepath))

def ThumbFromImage(image, size = (50,50), thumbnaildir=None):
  """
  Create a thumbnail from an image path
  Thumbnails will be saved in basedir/thumbnails if no other is specified
  Returns a (image,thumbnail) pair where image and thumbnail are
  paths to the origional image and the created thumbnail
  """
  Image = ImportPIL()

  if not os.path.exists(image):
    raise IOError("image does not exist: %s" % image)
  #make sure there's a folder for the thumbnail
  if thumbnaildir is None:
    thumbnaildir = os.path.join(os.path.dirname(image), "thumbnails")
  if not os.path.isdir(thumbnaildir):
    os.mkdir(thumbnaildir)
  thumbnail = os.path.join(thumbnaildir, os.path.basename(image))
  # check if we already have an image that's older
  if os.path.exists(thumbnail):
    imagemtime = os.stat(image)[os.path.stat.ST_MTIME]
    thumbmtime = os.stat(image)[os.path.stat.ST_MTIME]
    if imagemtime <= thumbmtime:
      return thumbnail
  #resize and save the image
  im = Image.open(image)
  im.thumbnail(size,Image.ANTIALIAS)
  im.save(thumbnail,im.format)
  return thumbnail


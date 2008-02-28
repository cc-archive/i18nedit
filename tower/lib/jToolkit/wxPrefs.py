#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""A preference file (see jToolkit.prefs) editor using wxPython"""

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

# TODO: Comments for the root node
# TODO: Copy/Cut and Paste

import wx
import wx.gizmos as  gizmos
import os
import types
import re
from jToolkit import prefs

LOCATION_BUTTON_STYLE = 1

class EditorFrame(wx.Frame):
    """
    the editor window
    """

    def __init__( self, parent, id, title, filename):
        """
        create the editor
        """

        wx.Frame.__init__(self,None,id,title,size=wx.Size(600, 500))

        #create the panel and sizer
        panel = wx.Panel(self,wx.NewId())
        sizer = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(sizer)

        self.filename = filename
        self.panel = panel

        #create the menu
        menu = wx.MenuBar()
        filemenu = wx.Menu()

        ID_OPEN = wx.NewId()
        filemenu.Append(ID_OPEN,'&Open','Opens a .prefs file')
        wx.EVT_MENU(self, ID_OPEN, self.Open)
        
        ID_SAVE = wx.NewId()
        filemenu.Append(ID_SAVE,'&Save','Saves the current .prefs file')
        wx.EVT_MENU(self, ID_SAVE, self.OnSave)

        ID_SAVE_AS = wx.NewId()
        filemenu.Append(ID_SAVE_AS,'Save &As...','Saves to a .prefs file')
        wx.EVT_MENU(self, ID_SAVE_AS, self.OnSaveAs)

        ID_EXIT = wx.NewId()
        exititem = filemenu.Append(ID_EXIT,'E&xit','Exits')
        wx.EVT_MENU(self, ID_EXIT, self.Exit)
        
        menu.Append(filemenu, "&File")
        self.SetMenuBar(menu)

        #the buttons sizer
        bsizer = wx.BoxSizer(wx.HORIZONTAL)

        #the buttons
        #if version 2.5.x
        bmp = wx.Image(os.path.join(ICON_LOCATION,'insert_table_row.png'),wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        button = BMPButton(panel,wx.NewId(),bmp,'Add Pref',name='ADD_PREF_BUTTON')
        bsizer.Add(button,0)
        wx.EVT_BUTTON(self,button.GetId(),self.OnAddPref)

        bmp = wx.Image(os.path.join(ICON_LOCATION,'folder_new.png'),wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        button2 = BMPButton(panel,wx.NewId(),bmp,'Add Section',name='ADD_SECTION_BUTTON')
        bsizer.Add(button2,0,wx.LEFT,5)
        wx.EVT_BUTTON(self,button2.GetId(),self.OnAddSection)

        bmp = wx.Image(os.path.join(ICON_LOCATION,'inline_table.png'),wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        button = BMPButton(panel,wx.NewId(),bmp,'Rename',name='RENAME_BUTTON')
        bsizer.Add(button,0,wx.LEFT,5)
        wx.EVT_BUTTON(self,button.GetId(),self.OnRename)

        bmp = wx.Image(os.path.join(ICON_LOCATION,'edit.png'),wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        editbutton = BMPButton(panel,wx.NewId(),bmp,'Edit Pref',name='EDIT_PREF_BUTTON')
        bsizer.Add(editbutton,0,wx.LEFT,5)
        wx.EVT_BUTTON(self,editbutton.GetId(),self.OnEditPref)

        bmp = wx.Image(os.path.join(ICON_LOCATION,'delete_table_row.png'),wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        button3 = BMPButton(panel,wx.NewId(),bmp,'Remove',name='REMOVE_BUTTON')
        bsizer.Add(button3,0,wx.LEFT,5)
        wx.EVT_BUTTON(self,button3.GetId(),self.OnRemove)

        sizer.Add(bsizer,0,wx.EXPAND | wx.ALL,5)

        #the tree
        self.tree = PrefsTree(panel,wx.NewId(),
                              style=wx.TR_DEFAULT_STYLE,
                              filename=filename)
        sizer.Add(self.tree,1,wx.EXPAND)

        sizer.Layout()

    def Exit(self,event):
        """
        exits the program
        """

        self.Destroy()

    def OnAddPref(self,event):
        """
        adds a new preference
        """

        tree = self.tree
        selected = tree.GetSelection()
        if selected.IsOk():
            tree.AddPref(selected)

    def OnAddSection(self,event):
        """
        adds a new section
        """

        selected = self.tree.GetSelection()
        if selected.IsOk():
            self.tree.AddSection(selected)

    def OnEditPref(self,event):
        """
        starts editing the selected item
        """

        tree = self.tree
        selected = tree.GetSelection()
        popup = tree.EditPref(selected)
        if popup.ShowModal() == wx.ID_OK:
            tree.SetPref(selected, popup.GetValue())
        
    def OnRemove(self,event):
        """
        removes a section or preference, depending on the selection
        """

        tree = self.tree
        selection = tree.GetSelection()
        if selection.IsOk():
            tree.Delete(selection)

    def OnRename(self,event):
        """
        when the rename button is clicked call rename
        """

        tree = self.tree
        selected = tree.GetSelection()
        tree.RenameItem(selected)
        
    def Open(self,event):
        """
        Opens a new prefs file
        """

        wildcard = "Prefs File (*.prefs)|*.prefs|" \
                   "All files (*.*)|*.*"

        dlg = wx.FileDialog(self, message="Choose a preferences file", defaultDir=os.getcwd(),
                            defaultFile="", wildcard=wildcard, style=wx.OPEN | wx.CHANGE_DIR)
        
        # Show the dialog and retrieve the user response. If it is the OK response, 
        # process the data.
        if dlg.ShowModal() == wx.ID_OK:

            #if one is already loaded, then destroy it
            if self.tree:
                self.tree.Destroy()
                
            path = dlg.GetPath()
            panel = self.panel
            filename = self.filename
            self.tree = PrefsTree(panel,wx.NewId(),style=wx.TR_DEFAULT_STYLE ,filename=path)

            sizer = self.panel.GetSizer()
            sizer.Add(self.tree,1,wx.EXPAND)
            sizer.Layout()
            self.SetTitle('Prefs Editor [%s]' % os.path.basename(path))

    def OnSave(self,event):
        """
        Saves the current prefs to a prefs file
        """

        filename = self.tree.GetFilename()
        if filename is not None:
            self.Save(filename)
        else:
            self.SaveAs()

    def OnSaveAs(self,event):
        """
        opens a dialog to save to a file
        """

        self.SaveAs()
        
    def Save(self,filename):
        """
        saves the preferences to the file, overwriting the file in the process
        """
        
        parser = self.tree.GetParser()
        text = parser.getsource()
        file = open(filename,'w')
        file.write(text)
        file.close()
        self.SetTitle('Prefs Editor [%s]' % os.path.basename(filename))
        
    def SaveAs(self):
        """
        opens a dialog to save to a file
        """

        wildcard = "Prefs File (*.prefs)|*.prefs|"     \
                   "All files (*.*)|*.*"


        dlg = wx.FileDialog(self, message="Save file as ...", defaultDir=os.getcwd(),
                            defaultFile="", wildcard=wildcard, style=wx.SAVE)

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.Save(path)
            self.tree.SetFilename(path)

class PrefsTree(gizmos.TreeListCtrl):
    """
    the tree (with columns) for displaying hierarchical preferences
    """

    def __init__(self, panel, id, pos=wx.DefaultPosition,size=wx.DefaultSize,
                 style=0, filename=None):
        gizmos.TreeListCtrl.__init__(self,panel,id,pos,size,style=style)

        self.parser = None
        self.filename = filename
        
        isz = (16,16)
        il = wx.ImageList(isz[0], isz[1])
        fldridx     = il.Add(wx.ArtProvider_GetBitmap(wx.ART_FOLDER,      wx.ART_OTHER, isz))
        fldropenidx = il.Add(wx.ArtProvider_GetBitmap(wx.ART_FILE_OPEN,   wx.ART_OTHER, isz))
        self.prefidx = il.Add(wx.ArtProvider_GetBitmap(wx.ART_REPORT_VIEW,wx.ART_TOOLBAR,isz))

        #the preference icon
        png = wx.Image(os.path.join(ICON_LOCATION,'kservices.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        self.prefidx = il.Add(png)

        #the root icon
        png = wx.Image(os.path.join(ICON_LOCATION,'doc.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        self.rooticon = il.Add(png)

        #section icons
        png = wx.Image(os.path.join(ICON_LOCATION,'folder.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        self.fldridx = il.Add(png)
        png = wx.Image(os.path.join(ICON_LOCATION,'folder_open.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        self.fldropenidx = il.Add(png)

        self.SetImageList(il)
        self.il = il

        #  create some columns
        self.AddColumn("Preference")
        self.AddColumn("Value")
        self.AddColumn("Comments")
        self.SetMainColumn(0) #  the one with the tree in it...
        self.SetColumnWidth(0, 150)
        self.SetColumnWidth(1, 220)
        self.SetColumnWidth(2, 220)

        if filename:
            file = open(filename, 'r')
            text = file.read()
            self.LoadPrefs(text,os.path.basename(filename))
            file.close()
        else:
            self.New()

        self.SetFocus()

        wx.EVT_TREE_SEL_CHANGED(self,self.GetId(),self.OnSelectionChanged)
        wx.EVT_TREE_ITEM_ACTIVATED(self,self.GetId(),self.OnActivate)
        wx.EVT_TREE_KEY_DOWN(self,self.GetId(),self.OnKeyDown)
        wx.EVT_RIGHT_DOWN(self.GetMainWindow(), self.OnRightDown)
        wx.EVT_LEFT_DOWN(self.GetMainWindow(), self.OnLeftDown)

    def AddPrefsNode(self,name,node,parent):
        """
        Adds a prefs node to the parent, then recursively adds all children of that node
        """

        child = self.AppendItem(parent, name)

        # if this is another subsection
        if isinstance(node,prefs.PrefNode):

            self.SetItemImage(child, self.fldridx, which = wx.TreeItemIcon_Normal)
            self.SetItemImage(child, self.fldropenidx, which = wx.TreeItemIcon_Expanded)

            self.SetPyData(child,node)
            generator = node.iteritems()
            for n,o in generator:
                self.AddPrefsNode(n,o,child)
            self.Expand(child)

            #check for comments
            comment = self.parser.getcomment(repr(node))
            if comment is not None:
                self.SetItemText(child,comment[1:],2)

        #if not then this is a preference
        else:

            self.SetItemImage(child, self.prefidx, which = wx.TreeItemIcon_Normal)
            self.SetItemImage(child, self.prefidx, which = wx.TreeItemIcon_Expanded)

            self.SetPyData(child,None)
            if type(node) is not types.StringType:
                self.SetItemText(child, repr(node), 1)
            else:
                self.SetItemText(child, node, 1)

            #check for comments
            #a parent is always a section, so get its label
            parentnode = self.GetPyData(parent)
            label = parentnode.getlabel()
            if len(label)>0:
                str = '.'.join([label,name])
            else:
                str = name
            comment = self.parser.getcomment(str)
            if comment is not None:
                self.SetItemText(child,comment[1:],2)

    def AddPref(self,parent):
        """
        Adds a new pref
        """

        #if data is none then we have selected a child node.
        #make all changes to its direct parent
        data = self.GetPyData(parent)
        if data is None:
            parent = self.GetItemParent(parent)
        
        item = self.AppendItem(parent,'New Preference')
        self.SetItemImage(item, self.prefidx, which = wx.TreeItemIcon_Normal)
        self.SetItemImage(item, self.prefidx, which = wx.TreeItemIcon_Expanded)

        self.Collapse(parent)
        self.Expand(parent)

        popup = self.EditLabel(item)
        #if the popup is cancelled then delete what we have just added
        if popup.ShowModal() == wx.ID_OK:
            value = popup.GetValue()
            self.SetItemText(item,value,0)

            editpopup = self.EditPref(item)
            if editpopup.ShowModal() == wx.ID_OK:
                value = editpopup.GetValue()
                self.SetPref(item, value)
                self.SortChildren(parent)
                self.SelectItem(item)

            else:
                gizmos.TreeListCtrl.Delete(self,item)

            editpopup.Destroy()

        else:
            gizmos.TreeListCtrl.Delete(self,item)
        popup.Destroy()

    def AddSection(self,parentitem):
        """
        adds a new section of prefs
        """

        data = self.GetPyData(parentitem)

        #if this is a leaf node then get its parent
        #you cant add a section to a leaf node
        if data is None:
            parentitem = self.GetItemParent(parentitem)

        child = self.AppendItem(parentitem, '')
        self.SetItemImage(child, self.fldridx, which = wx.TreeItemIcon_Normal)
        self.SetItemImage(child, self.fldropenidx, which = wx.TreeItemIcon_Expanded)

        #collapse and expand so that GetBoundingBox works correctly
        self.Collapse(parentitem)
        self.Expand(parentitem)

        popup = self.EditLabel(child)
        if popup.ShowModal() == wx.ID_OK:
            self.SetItemText(child, popup.GetValue(), 0)
            name = self.GetItemText(child,0)
            parent = self.GetPyData(parentitem)
            newnode = prefs.PrefNode(parent,name)
            parent.__dict__[name] = newnode
            self.SetPyData(child,newnode)

            #sort this section and select the new section
            self.SortChildren(parentitem)
            self.SelectItem(child)

        else:
            #use the base delete as we havn't added anything to the parser yet
            gizmos.TreeListCtrl.Delete(self,child)

    def Delete(self,item):
        """
        overrides the standard delete for TreeListCtrl so that
        the change to the tree is reflected in the parser
        """

        #do nothing if this is the root item or if this item is not valid
        if (self.GetRootItem() == item) or (not item.IsOk()):
            return
        
        data = self.GetPyData(item)

        #if data is a section
        if isinstance(data,prefs.PrefNode):

            parent = self.GetItemParent(item)
            parentnode = self.GetPyData(parent)
            delattr(parentnode,self.GetItemText(item,0))

        #if data is not a section then it is a pref
        else:
            parent = self.GetItemParent(item)
            node = self.GetPyData(parent)
            delattr(node,self.GetItemText(item,0))

        next = self.GetNextSibling(item)
        prev = self.GetPrevSibling(item)
        if next.IsOk():
            newitem = next
        elif prev.IsOk():
            newitem = prev
        else:
            newitem = self.GetItemParent(item)

        self.SelectItem(newitem)
        gizmos.TreeListCtrl.Delete(self,item)
        
    def EditLabel(self,item):
        """
        brings up a textctrl to edit the label of an item
        """

        self.EnsureVisible(item)

        #get the point for the text ctrl
        rect = self.GetBoundingRect(item,False)
        height = rect.GetHeight()
        point = rect.GetPosition()

        #modify x and y for the screen area
        point = self.ClientToScreen(point) + wx.Point(20,24)

        text = self.GetItemText(item,0)
        popup = EditLabelDialog(self,-1,text,item,point,
                                wx.Size(125,height),
                                wx.BORDER_SIMPLE|wx.STAY_ON_TOP,
                                '\D\w*')
        popup.Show(True)

        return popup
        
    def EditPref(self,item):
        """
        bings up a textctrl to change the value of a preference
        """

        #get the point for the text ctrl
        rect = self.GetBoundingRect(item)
        height = rect.GetHeight()
        y = rect.GetY()
        x = self.GetColumnWidth(0)
        point = wx.Point(x,y)

        #modify x and y for the screen area
        point = self.ClientToScreen(point) + wx.Point(0,24)

        text = self.GetItemText(item,1)
        popup = EditLabelDialog(self,-1,text,item,point,wx.Size(300,height),LOCATION_BUTTON_STYLE)

        return popup

    def GetFilename(self):
        """
        returns the name of this preferences file
        """

        return self.filename
    
    def GetParser(self):
        """
        returns the parser used for the prefs
        """

        return self.parser

    def HitTest( self, point ):
        w = self.GetMainWindow()
        return gizmos.TreeListCtrl.HitTest(self, self.ScreenToClient(w.ClientToScreen(point)))

    def LoadPrefs(self,text=None,filename='New'):
        """
        Loads a prefs file into the tree. If filename is not supplied then a barebones tree is created.
        """

        if filename != 'New':
            self.filename = filename
            
        # add items
        parser = prefs.PrefsParser()
        self.parser = parser

        if text is not None:
            parser.parse(text)

        self.root = self.AddRoot(os.path.basename(filename))
        self.SetPyData(self.root,parser.__root__)
        self.SetItemImage(self.root, self.rooticon, which = wx.TreeItemIcon_Normal)
        self.SetItemImage(self.root, self.rooticon, which = wx.TreeItemIcon_Expanded)
        self.SelectItem(self.root)

        generator = parser.iteritems()
        for name,obj in generator:
            if name is not '_setvalue':
                self.AddPrefsNode(name,obj,self.root)

        self.Expand(self.root)

    def New(self):
        """
        Creates a barebones prefs tree
        """
        self.LoadPrefs()
        
    def OnActivate(self,event):
        """
        When the user presses enter or double clicks on an item
        """

        item = event.GetItem()
        data = self.GetPyData(item)

        #if this is a leaf node
        if data is None:
            popup = self.EditPref(item)
            if popup.ShowModal() == wx.ID_OK:
                self.SetPref(item, popup.GetValue())

        event.Skip()

    def OnAddPref(self,event):
        """
        calls AddPref with the selected item
        """

        selected = self.GetSelection()
        self.AddPref(selected)
        
    def OnAddSection(self,event):
        """
        calls AddSection with the selected item
        """

        selected = self.GetSelection()
        self.AddSection(selected)
        
    def OnKeyDown(self,event):
        """
        when a key is pressed...
        """

        if event.GetKeyCode() == wx.WXK_DELETE:
            selected = self.GetSelection()
            self.Delete(selected)

        event.Skip()

    def OnLeftDown(self,event):
        """
        captures left mouse clicks and acts accordingly
        presently used for renaming things
        """

        #get the currently selected item
        selected = self.GetSelection()

        if selected == self.GetRootItem():
            event.Skip()
            return

        #get the item that was clicked on
        position = event.GetPosition()
        val1,val2,val3 = self.HitTest(position)
        item = val1
        flags = val2

        event.Skip()
        
    def OnRemove(self,event):
        """
        calls Delete with the selected item
        """

        selected = self.GetSelection()
        if selected.IsOk():
            self.Delete(selected)
        
    def OnRename(self,event):
        """
        calls RenameItem with the selected item
        """

        selected = self.GetSelection()
        self.RenameItem(selected)
        
    def OnRightDown(self,event):
        """
        brings up a popup menu
        """

        #select the item that was clicked on
        pt = event.GetPosition();
        item, flags, col = self.HitTest(pt)
        self.SelectItem(item)

        #dont act if this is the root item
        if item == self.GetRootItem():
            event.Skip()
            return

        # make a menu
        menu = wx.Menu()

        data = self.GetPyData(item)

        if isinstance(data,prefs.PrefNode):
            #a section
            parent = self.GetItemText(item)
        else:
            #a pref
            parentitem = self.GetItemParent(item)
            parent = self.GetItemText(parentitem)

        ADD_PREF_ID = wx.NewId()
        item = wx.MenuItem(menu, ADD_PREF_ID,"Add Pref to " + parent)
        bmp = wx.Image(os.path.join(ICON_LOCATION,'16x16','insert_table_row.png'),wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        item.SetBitmap(bmp)
        menu.AppendItem(item)
        wx.EVT_MENU(menu,ADD_PREF_ID,self.OnAddPref)

        ADD_SECTION_ID = wx.NewId()
        item = wx.MenuItem(menu, ADD_SECTION_ID,"Add Section to " + parent)
        bmp = wx.Image(os.path.join(ICON_LOCATION,'16x16','folder_new.png'),wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        item.SetBitmap(bmp)
        menu.AppendItem(item)
        wx.EVT_MENU(menu,ADD_SECTION_ID,self.OnAddSection)

        REMOVE_ID = wx.NewId()
        item = wx.MenuItem(menu, REMOVE_ID, "Remove")
        bmp = wx.Image(os.path.join(ICON_LOCATION,'16x16','delete_table_row.png'),wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        item.SetBitmap(bmp)
        menu.AppendItem(item)
        wx.EVT_MENU(menu,REMOVE_ID,self.OnRemove)

        RENAME_ID = wx.NewId()
        item = wx.MenuItem(menu, RENAME_ID, "Rename")
        bmp = wx.Image(os.path.join(ICON_LOCATION,'16x16','inline_table.png'),wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        item.SetBitmap(bmp)
        menu.AppendItem(item)
        wx.EVT_MENU(menu,RENAME_ID,self.OnRename)

        # Popup the menu
        point = event.GetPosition() + wx.Point(0,24)
        self.PopupMenu(menu, point)
        menu.Destroy()
        event.Skip()
        
    def OnSelectionChanged(self,event):
        """
        not yet implimented
        """

        button = wx.FindWindowByName('EDIT_PREF_BUTTON')
        item = event.GetItem()
        data = self.GetPyData(item)

        if isinstance(data,prefs.PrefNode):
            button.Enable(False)
            button.Refresh()
        else:
            button.Enable(True)
            button.Refresh()

        event.Skip()
            
    def RenameItem(self,item):
        """
        decides whether the item is a pref or a section and calls the appropriate funciton
        """

        popup = self.EditLabel(item)
        if popup.ShowModal() == wx.ID_OK:
            data = self.GetPyData(item)
            newname = popup.GetValue().replace(' ','_')
            if isinstance(data,prefs.PrefNode):
                #a section
                self.RenameSection(item,newname)

            else:
                #a pref
                self.RenamePref(item,newname)

            popup.Destroy()


    def RenamePref(self,item,newname):
        """
        renames a pref to newname in the tree and in the parser object
        """

        #rename a pref by creating a new object with the same value
        name = self.GetItemText(item,0)
        parent = self.GetItemParent(item)
        parentnode = self.GetPyData(parent)
        parentnode.renamepref(name,newname)

        #make the changes to the list too
        self.SetItemText(item,newname,0)
        
    def RenameSection(self,item,newname):
        """
        renames a section to newname by copying the old section and making a new one
        """
        node = self.GetPyData(item)
        parent = self.GetItemParent(item)
        parentnode = self.GetPyData(parent)
        copy = node.copy(parentnode,newname)
        parentnode.__dict__[newname] = copy
        oldname = self.GetItemText(item,0)
        delattr(parentnode,oldname)
        self.SetItemText(item,newname,0)
        self.SetPyData(item,copy)
        
    def SetFilename(self,filename):
        """
        sets the filename that this tree relates to
        """

        self.filename = filename
        root = self.root
        self.SetItemText(root,os.path.basename(filename))
        
    def SetPref(self,item,value):
        """
        Sets the value of a preference in the TreeListCtrl and in the parser object
        """

        #only act if item is a leaf node
        data = self.GetPyData(item)
        if data is not None:
            return

        self.SetItemText(item, value, 1)

        #some type testing must be done on the value
        if value.isdigit():
            value = int(value)
        elif value.lower() == 'false':
            value = False
        elif value.lower() == 'true':
            value = True

        parent = self.GetItemParent(item)
        node = self.GetPyData(parent)
        setattr(node,self.GetItemText(item,0),value)
            
        
class EditLabelDialog(wx.Dialog):
    """
    a very simple dialog that is used for changing the value of a pref
    """

    def __init__(self,parent,id,label,item,pos,size,style,validateExp=None):
        wx.Dialog.__init__(self,parent,id,'',pos,size,wx.BORDER_SIMPLE|wx.STAY_ON_TOP)

        self.SetSize(size)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(sizer)
        self.item = item
        self.listctrl = parent
        if validateExp:
            self.vexp = validateExp
        else:
            self.vexp = '.*'
        self.textcontrol = wx.TextCtrl(self,-1,label,style=wx.TE_PROCESS_ENTER)
        sizer.Add(self.textcontrol,1,wx.EXPAND)

        if style == LOCATION_BUTTON_STYLE:
##            bmp = wx.Image(os.path.join(ICON_LOCATION,'folder_yellow.png'),wx.BITMAP_TYPE_PNG).ConvertToBitmap()
            bmp = wx.ArtProvider_GetBitmap(wx.ART_FOLDER,wx.ART_OTHER, (16,16))
            locatebutton= BMPButton(self,wx.NewId(),bmp,'',padding=0)
            sizer.Add(locatebutton,0,wx.EXPAND)

            wx.EVT_KEY_DOWN(locatebutton,self.OnKeyDown)
            wx.EVT_BUTTON(locatebutton,locatebutton.GetId(),self.OnLocate)

        wx.EVT_TEXT_ENTER(self.textcontrol,self.textcontrol.GetId(), self.OnEnter)
        wx.EVT_CHAR(self.textcontrol,self.OnKeyDown)
        
    def GetItem(self):
        """
        returns the associated wxTreeListCtrl item 
        """

        return self.item

    def GetValue(self):
        """
        returns the value in the TextCtrl
        """

        return self.textcontrol.GetValue()

    def OnEnter(self,event):
        """
        when the enter key is pressed
        """

##        self.SetReturnCode(wx.ID_OK)
        self.EndModal(wx.ID_OK)

    def OnKeyDown(self,event):
        """
        a key is being pressed
        """

        key = event.GetKeyCode()
        
        if key == wx.WXK_ESCAPE:
            self.EndModal(wx.ID_CANCEL)

        if 0 < key < 256:
            index = self.textcontrol.GetInsertionPoint()
            value = self.textcontrol.GetValue()
            value = value[:index] + chr(key) + value[index:]
            matchobject = re.match(self.vexp,value)
            if matchobject is None:
                return

        event.Skip()

    def OnKillFocus(self,event):
        """
        This window is losing focus. Quick, do something!
        """

        #clicking away from the dialog is considered entering the value
        if not self.done:
            self.SetReturnCode(wx.ID_OK)
            self.Close()

    def OnLocate(self,event):
        """
        opens a dialog to find files and folders for the label
        """

        dialog = wx.FileDialog(self,'Choose a file',style=wx.OPEN)
        if dialog.ShowModal() == wx.ID_OK:
            path = dialog.GetPath()
            self.textcontrol.SetValue(path)
        dialog.Destroy()

class PrefsEditor(wx.App):
    """
    the main class that starts the editor
    """

    def OnInit(self):
        """
        wxWindows calls this method to initialize the application
        """
        import sys

        if len(sys.argv) > 1:
            frame = EditorFrame(None,-1,"Prefs Editor", sys.argv[1])
        else:
            frame = EditorFrame(None,-1,"Prefs Editor", None)

        frame.Show(True)

        # Return a success flag
        return True

class BMPButton(wx.Button):
    """
    an  button with a BMP graphic drawn next to the text
    """

    def __init__(self,parent,id,bmp,label,pos=wx.DefaultPosition,size=wx.DefaultSize,padding=30,name='BMPButton'):
        wx.Button.__init__(self,parent,id,'',pos,size,name=name)

        self.bmp = bmp
        self.text = label
        self.hindent = 6
        self.vindent = 6
        
        #get the width of the bitmap
        self.bmpwidth = bmp.GetWidth()

        #set the default size of the control
        if size == wx.DefaultSize:
            dc = wx.ClientDC(self)
            dc.SetFont(self.GetFont())
            width,height = dc.GetTextExtent(self.text)

            #a suggested default size that will be big enough to see everything
            size = wx.Size(bmp.GetWidth()+self.hindent*2+width+padding,max(height,bmp.GetHeight()+(self.vindent*2)))
            self.SetSize(size)

        wx.EVT_PAINT(self,self.OnPaint)

    def DrawContents(self,dc=None):
        """
        Draws the graphic and the text
        """

        bmp = self.bmp

        if dc is None:
            dc = wx.ClientDC(self)

        #get a nice point so the icon will be left-middle
        point = wx.Point(self.hindent,self.GetSize().y/2-bmp.GetHeight()/2)

        if not self.IsEnabled():
            img = wx.ImageFromBitmap(bmp)
            self.ShadeGrey(img)
            bmp = img.ConvertToBitmap()

        dc.DrawBitmap(bmp,point.x,point.y,True)

        #get a nice point for the text that that it is central in the remaining space
        dc.SetFont(self.GetFont())

        if not self.IsEnabled():
           dc.SetTextForeground(wx.Colour(201,199,186))

        width,height = dc.GetTextExtent(self.text)
        textspace = self.GetSize().x - (bmp.GetWidth() + self.hindent)
        point = wx.Point(bmp.GetWidth() + textspace/2 - width/2,self.GetSize().y/2-height/2)
        dc.DrawText(self.text,point.x,point.y)

    def MakeGrey( self, (r,g,b) , factor, maskColor ):
        """
        accepts a 3-tuple representing a colour, a factor
        by which a pixel will be affected, and a mask colour
        returns the modified colour
        """

        if (r,g,b) != maskColor:
            return map(lambda x: int((250 - x) * factor) + x, (r,g,b))
        else:
            return (r,g,b)

    def OnPaint(self,event):
        """
        Redraws the button
        """

        wx.CallAfter(self.DrawContents)
        event.Skip()
    def ShadeGrey( self, anImage ):
        """
        Accepts an image, which is modified to look greyed out
        """

        factor = 0.5        # 0 < f < 1.  Higher is grayer.
        if anImage.HasMask():
            maskColor = (anImage.GetMaskRed(), anImage.GetMaskGreen(), anImage.GetMaskBlue())
        else:
            maskColor = None
        data = map(ord, list(anImage.GetData()))

        for i in range(0, len(data), 3):
            pixel = (data[i], data[i+1], data[i+2])
            pixel = self.MakeGrey(pixel, factor, maskColor)
            for x in range(3):
                data[i+x] = pixel[x]
        anImage.SetData(''.join(map(chr, data)))
        
ICON_LOCATION = os.path.join(os.path.dirname(__file__), 'icons')

def run():
    #first things first, initialise image handlers
    wx.InitAllImageHandlers()
    #record the location of icons
    # create an instance of the application class
    app = PrefsEditor(0)
    # start processing events
    app.MainLoop()

if __name__ == "__main__":
    run()


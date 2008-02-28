#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""simple gui interfaces useful in installers for asking questions etc
supported are commandline, windows, Tk variants"""

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

class cmdline:
    """A command-line 'gui' interface"""
    def choosedirectory(self, title, initialdir):
        """asks the user for a directory"""
        path = raw_input(title + "[%s] " % initialdir)
        if path:
            return path
        else:
            return initialdir

    def askyesno(self, title, message):
        """asks the user a yes-no question"""
        print title
        response = raw_input(message + " ").lower()
        if response in ("y", "yes", "1", "t", "true"):
            return True
        elif response in ("n", "no", "0", "f", "false"):
            return False

    def displaymessage(self, title, message):
        """displays a message for the user"""
        print title
        print message

    def close(self):
        """closes the gui"""
        pass

class Tkgui:
    """A Tkinter-based gui interface"""
    def __init__(self):
        """This opens a gui interface if one is available"""
        # this code just hides the default Tk window
        from Tkinter import Tk
        self.root = Tk()
        self.root.withdraw()

    def choosedirectory(self, title, initialdir):
        """asks the user for a directory"""
        from tkFileDialog import askdirectory
        path = askdirectory(title=title, initialdir=initialdir, mustexist=1)
        return path

    def askyesno(self, title, message):
        """asks the user a yes-no question"""
        import tkMessageBox
        return tkMessageBox.askyesno(title, message)

    def displaymessage(self, title, message):
        """displays a message for the user"""
        import tkMessageBox
        tkMessageBox.showinfo(title, message)

    def close(self):
        """closes the gui"""
        if self.root is not None:
            self.root.quit()
            self.root.destroy()
            self.root = None

    def __del__(self):
        """make sure we're closed..."""
        self.close()

class win32nativegui(cmdline):
    """A native win32 gui"""
    def __init__(self):
        import win32com

    def choosedirectory(self, title, initialdir):
        """asks the user for a directory"""
        from win32com.shell import shell
        pidl, displayname, imagelist = shell.SHBrowseForFolder(0, None, title)
        path = shell.SHGetPathFromIDList(pidl)
        return path

    def askyesno(self, title, message):
        """asks the user a yes-no question"""
        import win32gui
        import win32con
        response = win32gui.MessageBox(0, message, title, win32con.MB_YESNO)
        if response == win32con.IDYES:
            return True
        elif response == win32con.IDNO:
            return False

    def displaymessage(self, title, message):
        """displays a message for the user"""
        import win32gui
        import win32con
        win32gui.MessageBox(0, message, title, win32con.MB_OK)

    def close(self):
        """closes the gui"""
        pass

guiclasses = (Tkgui, win32nativegui, cmdline)

def getgui(guioptions=None):
    """select an appropriate gui from the given options (in order of preference)"""
    if guioptions is None:
        guioptions = guiclasses
    for guiclass in guioptions:
       try:
           gui = guiclass()
           return gui
       except:
           pass

if __name__ == '__main__':
    import os
    for guiclass in guiclasses:
        print "testing",guiclass.__name__
        try:
            gui = guiclass()
        except Exception, error:
            print "couldn't use gui..."
            print error
            continue
        print "displaying message"
        gui.displaymessage("Title", "Testing displaymessage")
        response = gui.askyesno("Title", "Testing askyesno, what do you think?")
        print "yesno response:", response
        response = gui.choosedirectory("Testing choosedirectory", os.getcwd())
        print "dir response:", response


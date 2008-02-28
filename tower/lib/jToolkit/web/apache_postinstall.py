#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""a module that can reconfigure Apache after installation"""

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

from jToolkit import installgui
import os

def askForApacheDir(apachediroptions, gui):
    # try to ask for Apache directory
    if len(apachediroptions) > 0:
        # get the most recent version...
        versionnames = apachediroptions.keys()
        versionnames.sort()
        initialdir = apachediroptions[versionnames[-1]]
    else:
        initialdir = "C:/Program Files/Apache Group/Apache2"
    # TODO: let the user select the name from a list, or click browse to choose...
    return gui.choosedirectory(title = "Where is Apache installed?", initialdir = initialdir)

modifyquestion = """Do you want the installer to modify the Apache configuration file
%s
and change the DocumentRoot to %s?"""

missingconfmessage = """Could not find Apache configuration file:
%s
This may indicate an error in the Apache installation."""

def modifyApacheDocumentRoot(newdocroot, gui=None):
    """Makes neccessary changes to the Apache config file, using user input"""
    if gui is None:
      gui = installgui.getgui()
    try:
        from jToolkit.web import apacheconf
        apachediroptions = apacheconf.getApacheDirOptions()
        apachedir = askForApacheDir(apachediroptions, gui)
    except ImportError:
        gui.displaymessage("Error", "Could not load apache configuration module")
        return
    if not apachedir:
        gui.displaymessage("Error", "Could not find Apache directory")
        return
    conffile = os.path.join(apachedir, "conf", "httpd.conf")
    if not os.path.isfile(conffile):
        gui.displaymessage("Error", "File not found", missingconfmessage % conffile)
        return
    conf = apacheconf.ApacheConf(conffilename=conffile)
    if newdocroot is None or not os.path.isdir(newdocroot):
        try:
            olddocroot = conf.getdocumentroot()
        except:
            gui.displaymessage("Error", "Could not find Apache Document root. Cannot modify Apache configuration")
            return
        if gui.askyesno("Select Apache DocumentRoot?", "Do you want to select a new DocumentRoot for Apache?"):
            newdocroot = gui.choosedirectory(title = "Choose new Apache root directory", initialdir=olddocroot)
        else:
            return
    if gui.askyesno("Modify Apache Configuration File?", modifyquestion % (conffile, newdocroot)):
        bakfile = conffile + os.extsep + "bak"
        gui.displaymessage("Information", "Backing up %s to %s" % (conffile, bakfile))
        conf.savefile(conffilename = bakfile)
        conf.changedocumentroot(newdocroot)
        conf.savefile()


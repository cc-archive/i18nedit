#!/usr/bin/env python
 #
 # Copyright 2004 Apache Software Foundation 
 # 
 # Licensed under the Apache License, Version 2.0 (the "License"); you
 # may not use this file except in compliance with the License.  You
 # may obtain a copy of the License at
 #
 #      http://www.apache.org/licenses/LICENSE-2.0
 #
 # Unless required by applicable law or agreed to in writing, software
 # distributed under the License is distributed on an "AS IS" BASIS,
 # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
 # implied.  See the License for the specific language governing
 # permissions and limitations under the License.
 #
 # Originally developed by David Fraser of St James Software.
 #

"""
module for reading and modifying apache configuration files
"""

try:
    import win32api
except:
    win32api = None
try:
    import win32con
except:
    win32con = None

class regkey:
    """
    simple wrapper for registry functions that closes keys nicely...
    """
    def __init__(self, parent, subkeyname):
       self.key = win32api.RegOpenKey(parent, subkeyname)

    def childkey(self, subkeyname):
       try:
           return regkey(self.key, subkeyname)
       except win32api.error:
           return nullregkey()

    def subkeynames(self):
       numsubkeys = win32api.RegQueryInfoKey(self.key)[0]
       return [win32api.RegEnumKey(self.key, index) for index in range(numsubkeys)]

    def getvalue(self, valuename):
       try:
           return win32api.RegQueryValueEx(self.key, valuename)
       except win32api.error:
           raise AttributeError("Cannot access registry value %r" % (valuename))

    def __del__(self):
       if hasattr(self, "key"):
           win32api.RegCloseKey(self.key)

class nullregkey:
    """
    a registry key that doesn't exist...
    """
    def childkey(self, subkeyname):
        return nullregkey()

    def subkeynames(self):
        return []

    def getvalue(self, valuename):
        raise AttributeError("Cannot access registry value %r: key does not exist" % (valuename))

def getApacheDirOptions():
    """
    find potential apache directories in the registry...
    """
    if win32api is None or win32con is None:
        return {}
    versions = {}
    hklm_key = regkey(win32con.HKEY_LOCAL_MACHINE, "Software").childkey("Apache Group").childkey("Apache")
    hkcu_key = regkey(win32con.HKEY_CURRENT_USER, "Software").childkey("Apache Group").childkey("Apache")
    for apachekey in (hklm_key, hkcu_key):
        for versionname in apachekey.subkeynames():
            try:
                serverroot = apachekey.childkey(versionname).getvalue("ServerRoot")
            except AttributeError:
                continue
            versions[versionname] = serverroot[0]
    return versions

class ApacheConf:
    """
    An Apache configuration file
    """

    def __init__(self, confstring=None, conffile=None, conffilename=None):
        """
        build the conf file out of a string, file object or filename
        """
        self.lines = []
        self.context = {}
        if confstring is not None:
            self.filename = None
            self.parse(confstring)
        elif conffile is not None:
            self.filename = None
            confstring = conffile.read()
            self.parse(confstring)
        elif conffilename is not None:
            self.filename = conffilename
            conffile = open(conffilename, 'r')
            confstring = conffile.read()
            conffile.close()
            self.parse(confstring)

    def __str__(self):
        """
        converts the config object back to a config string
        """
        return "\n".join(self.lines)

    def savefile(self, conffile=None, conffilename=None):
        """
        Saves the configuration back to given file or filename (or self.filename if given in __init__)
        """
        confstring = str(self)
        if conffile is not None:
            conffile.write(confstring)
        elif conffilename is not None:
            conffile = open(conffilename, 'w')
            conffile.write(confstring)
            conffile.close()
        elif self.filename is not None:
            conffile = open(self.filename, 'w')
            conffile.write(confstring)
            conffile.close()
        else:
            raise IOError("Must give filename to save to")

    def parse(self, confstring):
        """
        Parse the given configuration string
        """
        self.lines = confstring.split("\n")
        currentcontext = []
        continuation = ""
        for linenum, line in enumerate(self.lines):
            self.context[linenum] = currentcontext[:]
            if line.endswith("\\"):
                continuation += line[:-1]
                continue
            if continuation:
                line = continuation + line
                continuation = ""
            if self.iscomment(line):
                continue
            line = line.strip()
            if line.startswith('</') and line.endswith('>'):
                # end of context
                line = line[2:-1]
                if currentcontext[-1][0] != line:
                  print "funny end=%s, context=%s" % (line, currentcontext[-1][1])
                else:
                  currentcontext.pop()
            elif line.startswith('<') and line.endswith('>'):
                # start of context
                line = line[1:-1]
                tagname = line.split()[0]
                currentcontext.append((tagname, line))

    def iscomment(self, line):
        """
        Returns whether or not the line is a comment
        """
        return line.strip().startswith('#')

    def search(self, directive, context=None):
        """
        Searches for the given directive, returning a list of matching line numbers
        """
        linenums = []
        for linenum, line in enumerate(self.lines):
           if self.iscomment(line):
               continue
           if context is not None and not self.matchcontext(linenum, context):
               continue
           line = line.strip()
           parts = line.split()
           if parts and parts[0].lower() == directive.lower():
               linenums.append(linenum)
        return linenums

    def matchcontext(self, linenum, context):
        """
        Returns whether the line number context matches the given context
        """
        context = [(directive.lower(), line.strip()) for directive, line in context]
        linecontext = self.context[linenum]
        linecontext = [(directive.lower(), line.strip()) for directive, line in linecontext]
        return linecontext == context

    def insertline(self, linenum, line):
        """
        Inserts a line at the given line number
        """
        for linenum in range(len(self.lines), linenum, -1):
            self.context[linenum] = self.context[linenum-1]
        self.lines.insert(linenum-1, line)

    def addmodule(self, modulename, modulefile):
        """
        Adds a LoadModule directive for the module if there isn't one already
        """
        # find all the LoadModule lines
        loadmodulelines = self.search("LoadModule", context=[])
        # check to see if the module is already listed
        for linenum in loadmodulelines:
           line = self.lines[linenum]
           parts = line.strip().split()
           if len(parts) < 3:
               # this is actually an error in the config file
               continue
           if parts[1] == modulename and parts[2] == modulefile:
               # the module is already listed
               return
        # fine the last one
        loadmodulepos = max(loadmodulelines)
        # TODO: handle line endings
        loadmoduleline = "LoadModule %s %s" % (modulename, modulefile)
        self.insertline(loadmodulepos + 1, loadmoduleline)

    def getdocumentroot(self, context=None):
        """
        Finds the DocumentRoot value
        """
        docrootlines = self.search("DocumentRoot", context)
        if len(docrootlines) != 1:
            print docrootlines
            raise ValueError("Error: unable to find DocumentRoot")
        docrootline = self.lines[docrootlines[0]]
        return docrootline.strip()[len("DocumentRoot"):].strip()

    def getdirectorycontext(self, directory):
        """
        Returns a Directory context that can be used for searching
        """
        return [("Directory", "Directory %s" % directory)]

    def changedocumentroot(self, newdocumentroot):
        """
        Changes the DocumentRoot value and any associated Directory settings
        """
        docrootlines = self.search("DocumentRoot", [])
        if len(docrootlines) != 1:
            raise ValueError("Error: unable to find DocumentRoot")
        docrootline = self.lines[docrootlines[0]]
        docroot = docrootline.strip()[len("DocumentRoot"):].strip()
        docrootline = "DocumentRoot %s" % newdocumentroot
        self.lines[docrootlines[0]] = docrootline
        directorylines = self.search("<Directory")
        for linenum in directorylines:
            directoryline = self.lines[linenum].strip()
            if not directoryline.endswith(">"): continue
            directoryline = directoryline[1:-1].strip()
            if directoryline[len("Directory"):].strip() == docroot:
                directoryline = self.lines[linenum].replace(docroot, newdocumentroot, 1)
                self.lines[linenum] = directoryline
        
if __name__ == '__main__':
    import sys
    def showerror(message):
        print >>sys.stderr, message
    conf = ApacheConf(conffile=sys.stdin)
    # steps for basic modpython
    conf.addmodule("python_module", "modules/mod_python.so")
    docroot = conf.getdocumentroot()
    docrootcontext = conf.getdirectorycontext(docroot)
    allowoverridelines = conf.search("AllowOverride", docrootcontext)
    if len(allowoverridelines) != 1:
        showerror("Error: unable to find unique AllowOverride for Directory %s" % docroot)
    else:
        allowoverrideline = conf.lines[allowoverridelines[0]]
        overrides = allowoverrideline.lower().split()[1:]
        if not "all" in overrides or "fileinfo" in overrides:
            if "none" in overrides:
                indent = len(allowoverrideline) - len(allowoverrideline.lstrip())
                allowoverrideline = allowoverrideline[:indent] + "AllowOverride FileInfo"
            else:
                allowoverrideline = allowoverrideline.rstrip() + " FileInfo"
        conf.lines[allowoverridelines[0]] = allowoverrideline
    # steps for jToolkit
    conf.changedocumentroot('"/var/local/www/html/"')
    conf.savefile(conffile=sys.stdout)


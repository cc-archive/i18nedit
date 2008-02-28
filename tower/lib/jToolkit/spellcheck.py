#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""simple python wrapper for aspell"""

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
try:
    import subprocess
except ImportError:
    subprocess = None

class SpellingError(Exception):
    pass

def find_aspell():
    """
    Locate Aspell's executables in the system.
    """
    aspellname = "aspell"
    if os.name == "nt":
        aspellname += os.extsep + "exe"
    for path in os.environ.get('PATH', None).split(os.pathsep):
        if os.path.exists(os.path.join(path, aspellname)):
            return os.path.join(path, aspellname)
    # try check in the registry otherwise...
    if os.name == "nt":
        from jToolkit import winreg
        import win32con
        hklm_key = winreg.regkey(win32con.HKEY_LOCAL_MACHINE, "Software").childkey("Aspell")
        hkcu_key = winreg.regkey(win32con.HKEY_CURRENT_USER, "Software").childkey("Aspell")
        for aspell_key in (hklm_key, hkcu_key):
            try:
                path = aspell_key.getvalue("Path")
            except AttributeError:
                continue
            path = path[0]
            if os.path.exists(os.path.join(path, aspellname)):
                return os.path.join(path, aspellname)
    # this will just look in the current directory
    if os.path.exists(aspellname):
        return aspellname
    else:
        raise SpellingError("Could not find aspell executable")

def have_checker():
    """tests whether a spell checker is present"""
    try:
        find_aspell()
        return True
    except SpellingError:
        return False

def run_aspell(text, lang=None):
    """runs aspell on the given text, returning output and error_output"""
    aspellexe = find_aspell()

    # open a pipe to aspell, feed in the text to be checked, and get the result
    args = ['"%s"' % aspellexe, '-a']
    if lang:
        args.append("--lang=%s" % lang)
    if isinstance(text, unicode):
        text = text.encode('utf-8')
        # TODO: we can do this only if aspell supports --encoding (e.g. version 0.50, not version 0.33!)
        # args.append("--encoding=utf-8")
    command = " ".join(args)
    if subprocess:
        PIPE = subprocess.PIPE
        process = subprocess.Popen(command, stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=True)
        input,output,error = process.stdin,process.stdout,process.stderr
    else:
        input,output,error = os.popen3(command)
    if text:
        input.write('!\n') # put aspell into terse mode (so no *'s)
        input.write(text)
    input.close()
    results = output.read()
    output.close()
    if isinstance(results, str):
        results = results.decode('utf-8')
    error_results = error.read()
    error.close()
    if isinstance(error_results, str):
        error_results = error_results.decode('utf-8')
    return results, error_results

lang_cache = {}
def can_check_lang(lang=None, cache=True):
    """checks whether the given language can be spellchecked"""
    if not have_checker():
        return False
    if cache and lang in lang_cache:
      return lang_cache[lang]
    results, error_results = run_aspell("", lang)
    can_check = not error_results
    if cache:
      lang_cache[lang] = can_check
    return can_check

def check(text=None,lang=None):
    """
    performs a spell check on the text and returns a list of tuples in the form
    (word,index,[suggestions])

    note:
    words in the returns sequence occur in the same order as they were found in the text
    """
    results, error_results = run_aspell(text, lang)
    if error_results.strip():
        raise IOError("error running aspell:\n"+error_results)
    # split it up and get rid of all those empty lines
    parts = [part.strip() for part in results.split('\n') if len(part.strip()) > 0]
    if len(parts):
        del parts[0] # the first line is always rubish

    # get all the mistakes into a nice list of tuples
    start=0
    mistakes = []
    for part in parts:
        if part[0] == '&':
            front,back = part.split(':')
            word,resultcount,indentlocation = front.split()[1:]
            suggestions = back.replace(' ','').split(',')
            index = text.find(word,start)
            lineno = text[:index].count('\n')+1
            start = index+1
            mistakes.append((word,index,suggestions))
        if part[0] == '#' and len(part[0].strip()) > 1:
            print part[0]
            word,indentlocation = part[0].split()[1:]

    return mistakes


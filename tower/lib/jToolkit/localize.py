#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""extends the standard Python gettext classes
allows multiple simultaneous domains... (makes multiple sessions with different languages easier too)"""

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

import gettext
import locale
import os.path
from errno import ENOENT
from jToolkit import languagenames

class ManyTranslations(gettext.NullTranslations):
  """this proxies to many translations"""
  def __init__(self, translations=None):
    """Takes an optional sequence of translations."""
    gettext.NullTranslations.__init__(self)
    if translations is None:
      self.translations = []
    else:
      self.translations = translations

  def gettext(self, message):
    """gets the translation of the message by searching through all the domains"""
    for translation in self.translations:
      tmsg = translation._catalog.get(message, None)
      if tmsg is not None:
        return tmsg
    return message

  def ngettext(self, singular, plural, n):
    """gets the plural translation of the message by searching through all the domains"""
    for translation in self.translations:
      if not hasattr(translation, "plural"):
        continue
      plural = translation.plural
      tmsg = translation._catalog[(singular, plural(n))]
      if tmsg is not None:
        return tmsg
    if n == 1:
      return singular
    else:
      return plural

  def ugettext(self, message):
    """gets the translation of the message by searching through all the domains (unicode version)"""
    for translation in self.translations:
      tmsg = translation._catalog.get(message, None)
      # TODO: we shouldn't set _charset like this. make sure it is set properly
      if translation._charset is None: translation._charset = 'UTF-8'
      if tmsg is not None:
        if isinstance(tmsg, unicode):
          return tmsg
        else:
          return unicode(tmsg, translation._charset)
    return unicode(message)

  def ungettext(self, singular, plural, n):
    """gets the plural translation of the message by searching through all the domains (unicode version)"""
    for translation in self.translations:
      if not hasattr(translation, "plural"):
        continue
      plural = translation.plural
      tmsg = translation._catalog.get((singular, plural(n)), None)
      # TODO: we shouldn't set _charset like this. make sure it is set properly
      if translation._charset is None: translation._charset = 'UTF-8'
      if tmsg is not None:
        if isinstance(tmsg, unicode):
          return tmsg
        else:
          return unicode(tmsg, translation._charset)
    if n == 1:
      return unicode(singular)
    else:
      return unicode(plural)

def getinstalledlanguages(localedir):
  """looks in localedir and returns a list of languages installed there"""
  languages = []
  def visit(arg, dirname, names):
    if 'LC_MESSAGES' in names:
      languages.append(os.path.basename(dirname))
  os.path.walk(localedir, visit, None)
  return languages

def getlanguagenames(languagecodes):
  """return a dictionary mapping the language code to the language name..."""
  return dict([(code, languagenames.languagenames.get(code, code)) for code in languagecodes])

def findmany(domains, localedir=None, languages=None):
  """same as gettext.find, but handles many domains, returns many mofiles (not just one)"""
  mofiles = []
  if languages is None:
    languages = getinstalledlanguages(localedir)
  for domain in domains:
    mofile = gettext.find(domain, localedir, languages)
    mofiles.append(mofile)
  return mofiles

def translation(domains, localedir=None, languages=None, class_=None):
  """same as gettext.translation, but handles many domains, returns a ManyTranslations object"""
  if class_ is None:
    class_ = gettext.GNUTranslations
  mofiles = findmany(domains, localedir, languages)
  # we'll just use null translations where domains are missing ; this code will refuse to
  # if None in mofiles:
  #   missingindex = mofiles.index(None)
  #   raise IOError(ENOENT, 'No translation file found for domain', domains[missingindex])
  translations = []
  for mofile in mofiles:
    if mofile is None:
      t = gettext.NullTranslations()
      t._catalog = {}
    else:
      key = os.path.abspath(mofile)
      t = gettext._translations.get(key)
      if t is None:
        t = gettext._translations.setdefault(key, class_(open(mofile, 'rb')))
    translations.append(t)
  return ManyTranslations(translations)
    
def getdefaultlanguage(languagelist):
  """tries to work out the default language from a list"""
  def reducelocale(locale):
    pos = locale.find('_')
    if pos == -1:
      return locale
    else:
      return locale[:pos]
  currentlocale, currentencoding = locale.getlocale()
  try:
    defaultlocale, defaultencoding = locale.getdefaultlocale()
  except ValueError:
    defaultlocale, defaultencoding = None, None
  if len(languagelist) > 0:
    if currentlocale is not None:
      if currentlocale in languagelist:
        return currentlocale
      elif reducelocale(currentlocale) in languagelist:
        return reducelocale(currentlocale)
    if defaultlocale is not None:
      if defaultlocale in languagelist:
        return defaultlocale
      elif reducelocale(defaultlocale) in languagelist:
        return reducelocale(defaultlocale)
    return languagelist[0]
  else:
    # if our language list is empty, we'll just ignore it
    if currentlocale is not None:
      return currentlocale
    elif defaultlocale is not None:
      return defaultlocale
    return None


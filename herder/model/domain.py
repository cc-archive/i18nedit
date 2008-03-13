import os
import babel.messages.pofile

from pylons import config

import language

class Domain(object):
    """A translation domain."""

    _IGNORE_DIRS = ['.svn', 'test', 'templates',]

    @classmethod
    def by_name(cls, name):
        """Return a Domain instance by name."""

        if os.path.exists(os.path.join(config.get('herder.po_dir'), name)):
            return Domain(name, os.path.join(config.get('herder.po_dir'), name))

        raise KeyError("Unknown domain name.")

    @classmethod
    def all(cls):
        """Return a sequence of all available domains."""

        return [Domain(n, os.path.join(config.get('herder.po_dir'), n)) 
                for n in os.listdir(config.get('herder.po_dir'))
                if n not in cls._IGNORE_DIRS and 
                   os.path.isdir(os.path.join(config.get('herder.po_dir'), n))]

    def __init__(self, name, path):
        self.name = name
        self.path = path
    
    @property
    def languages(self):
        """Return a sequence of available languages."""

        return [language.Language(self, n) 
                for n in os.listdir(self.path)
                if n not in self._IGNORE_DIRS and
                   os.path.isdir(os.path.join(self.path, n))]

    def get_language(self, lang):
        """Return a specific language for this domain."""

        if os.path.exists(os.path.join(self.path, lang)) and \
                os.path.isdir(os.path.join(self.path, lang)):

            return language.Language(self, lang)

        raise KeyError("Unknown language.")


import os
import babel.messages.pofile

PO_DIR = os.path.join(
    os.path.dirname(__file__), '..', '..', 'po_files')

class Domain(object):
    """A translation domain."""

    _IGNORE_DIRS = ['.svn', 'test', 'templates',]

    @classmethod
    def by_name(cls, name):
        """Return a Domain instance by name."""

        if os.path.exists(os.path.join(PO_DIR, name)):
            return Domain(name, os.path.join(PO_DIR, name))

        raise KeyError("Unknown domain name.")

    @classmethod
    def all(cls):
        """Return a sequence of all available domains."""

        return [Domain(n, os.path.join(PO_DIR, n)) 
                for n in os.listdir(PO_DIR)
                if n not in cls._IGNORE_DIRS and 
                   os.path.isdir(os.path.join(PO_DIR, n))]

    def __init__(self, name, path):
        self.name = name
        self.path = path
    
    @property
    def languages(self):
        """Return a sequence of available languages."""

        return [DomainLanguage(self, n) 
                for n in os.listdir(self.path)
                if n not in self._IGNORE_DIRS and
                   os.path.isdir(os.path.join(self.path, n))]

    def get_language(self, language):
        """Return a specific language for this domain."""

        if os.path.exists(os.path.join(self.path, language)) and \
                os.path.isdir(os.path.join(self.path, language)):

            return DomainLanguage(self, language)

        raise KeyError("Unknown language.")

class DomainLanguage(object):
    """A specific language within a domain."""

    @classmethod
    def by_domain_id(cls, domain, lang):

        return Domain.by_name(domain).get_language(lang)

    def __init__(self, domain, lang):
        self.domain = domain
        self.lang = lang

    def __str__(self):
        return self.lang

    def __cmp__(self, other):
        if isinstance(other, DomainLanguage):
            return cmp(str(self), str(other))

        return cmp(self, other)

    @property
    def name(self):
        return str(self)

    @property
    def _po_filename(self):

        return os.path.join(
            self.domain.path, self.lang, '%s.po' % self.domain.name)

    @property
    def catalog(self):
        """Return a sequence of strings for this language."""
        
        catalog = babel.messages.pofile.read_po(file(self._po_filename, 'r'),
                                                locale=self.name,
                                                domain=self.domain.name)

        return catalog

    def update(self, string_id, new_value, old_value=None):
        """Update a string; if old_value is provided, only perform the edit
        if the value has not been editted in the interim."""

        catalog = self.catalog
        record = catalog[string_id]

        if old_value is not None:
            if record.string != old_value:
                raise Exception

        record.string = new_value
        babel.messages.pofile.write_po(file(self._po_filename, 'w'),
                                       catalog)

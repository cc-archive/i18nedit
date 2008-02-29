import os
import babel.messages.pofile

from pylons import config

from jToolkit import prefs

import domain

class Language(object):
    """A specific language within a domain."""

    @classmethod
    def by_domain_id(cls, domain_id, lang):

        return domain.Domain.by_name(domain_id).get_language(lang)

    def __init__(self, domain, lang):
        self.domain = domain
        self.lang = lang

    def __str__(self):
        return self.lang

    def __cmp__(self, other):
        if isinstance(other, Language):
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

    @property
    def prefs(self):
        """Return the Pootle (sigh) properties object."""

        return prefs.PrefsParser(os.path.join(self.domain.path, self.lang,
                                             'pootle-%s-%s.prefs' % (
                    self.domain.name, self.name)))

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

    def suggest(self, username, string_id, suggestion):
        """Store a suggestion for a given string."""

        # figure out where to store this suggestion
        sugg_path = os.path.join(self.domain.path, self.lang, 'suggestions',
                                 hash(string_id))
        if not os.path.exists(sugg_path):
            os.mkdirs(sugg_path)

        # write the suggestion to disk
        

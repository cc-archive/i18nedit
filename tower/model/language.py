import os
import babel.messages.pofile

from pylons import config

from jToolkit import prefs

import domain
import message

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
    def _message_store(self):

        return os.path.join(self.domain.path, self.lang)

    @property
    def prefs(self):
        """Return the Pootle (sigh) properties object."""

        return prefs.PrefsParser(os.path.join(self.domain.path, self.lang,
                                             'pootle-%s-%s.prefs' % (
                    self.domain.name, self.name)))

    def get_message(self, id):
        """Return a Message in this language."""

        return message.Message(self, id)

    def messages(self):
        """Return a sequence of Message objects."""

        return [Message(self, m[:-4])
                for m in os.listdir(self._message_store)
                if m[-4:] == '.txt']

    def __getitem__(self, key):
        """Convenience method for accessing a Message by id."""

        if os.path.exists(os.path.join(self._message_store, '%s.txt' % key)):
            return message.Message(self, key)

        raise KeyError

    def __len__(self):
        
        return len(os.listdir(self._message_store))

    def __iter__(self):

        for filename in os.listdir(self._message_store):

            if filename[-4:] != '.txt':
                continue

            yield (message.Message(self, filename[:-4]))

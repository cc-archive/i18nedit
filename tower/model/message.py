import os
import string
import codecs

from pylons import config

from jToolkit import prefs

import domain
import language

class Message(object):
    """A specific string in a particular language."""

    ID_PATH_CHARS = string.ascii_letters + '. '

    @classmethod
    def by_domain_language_id(cls, domain_id, language_id, message_id):
        """Return the Message for a particular domain and language."""

        return Message(language.Language.by_domain_id(domain_id, language_id),
                       message_id)

    def __init__(self, language, id):
        
        self.language = language
        self.id = self.normalize_id(id)

    def normalize_id(self, id):
        """Return the normalized version of the string ID."""

        return id.lower()

        # calculate the filename
        id_src = "".join([n for n in id if n in self.ID_PATH_CHARS]).lower()
        words = id_src.split()

        if len(words) == 1:
            return words[0] 

        return "-".join([''] + words[:4] + [str(abs(hash(id)))])

    @property
    def datafile_path(self):
        """Return the file path used to store this message."""

        return os.path.join(self.language.domain.path, self.language.name,
                            self.id + '.txt')

    @property
    def string(self):
        """Return the current value of the string."""
    
        if not os.path.exists(self.datafile_path):
            return ""

        return codecs.open(self.datafile_path, 'r', 'utf-8').read()

    def update(self, new_value, old_value=None):
        """Update a string; if old_value is provided, only perform the edit
        if the value has not been editted in the interim."""

        if old_value is not None:
            if self.value != old_value:
                raise Exception

        file(self.datafile_path, 'w').write(new_value)

    def suggest(self, username, string_id, suggestion):
        """Store a suggestion for a given string."""

        # figure out where to store this suggestion
        sugg_path = os.path.join(self.domain.path, self.lang, 'suggestions',
                                 hash(string_id))
        if not os.path.exists(sugg_path):
            os.mkdirs(sugg_path)

        # write the suggestion to disk

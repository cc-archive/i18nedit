import urllib
import logging
from decorator import decorator

import jsonlib
from authkit.authorize.pylons_adaptors import authorize
from authkit.permissions import HasAuthKitRole, ValidAuthKitUser
from pylons.decorators import jsonify

import tower.model
from tower.lib.base import *

log = logging.getLogger(__name__)

@decorator
def injectroles(fn, *args, **kwargs):
    """Call a the _get_roles method on self (args[0]), passing in the same
    arguments passed to the controller action."""

    c.user_roles = args[0]._get_roles(*args[1:])
    return fn(*args, **kwargs)

class LanguageController(BaseController):

    def view(self, domain, id):
        """View a specific domain language."""

        c.domain = tower.model.Domain.by_name(domain)
        c.language = c.domain.get_language(id)

        return render('/language/view.html')

    def _get_roles(self, domain, id):
        """Return a sequence of roles the logged in user has for this 
        language."""

        username = request.environ.get("REMOTE_USER", False)
        if not username:
            return []

        prefs = tower.model.DomainLanguage.by_domain_id(domain, id).prefs
        if prefs.hasvalue('rights.%s' % username):
            return prefs.getvalue('rights.%s' % username).split(', ')

        # fall back to the default user
        if prefs.hasvalue('rights.default'):
            return prefs.getvalue('rights.default').split(',')

        return []

    def _editor(self, domain, id, template_fn):
        """Abstraction of the editor view."""

        c.domain = tower.model.Domain.by_name(domain)
        c.language = c.domain.get_language(id)

        c.addl_langs = request.params.getall('lang')
        c.addl_langs_list = ",".join(['"%s"' % n for n in c.addl_langs])
        c.addl_langs_qs = urllib.urlencode([('lang', n) for n in c.addl_langs])

        return render(template_fn)

    @injectroles
    def all(self, domain, id):

        return self._editor(domain, id, '/language/all.html')

    @injectroles
    def untranslated(self, domain, id):

        return self._editor(domain, id, '/language/untranslated.html')

    def _strings(self, domain, id, filter=lambda x:True):
        domain = tower.model.Domain.by_name(domain)
        langs = {id:domain.get_language(id).catalog}
    
        for l_id in request.params.getall('lang'):
            langs[l_id] = domain.get_language(l_id).catalog
            
        result = dict(domain=domain.name,
                      language=id,
                      strings=[])

        for s in langs[id]:
            if filter(s):
                string_record = dict(id=s.id, value=s.string)

                for l in langs:
                    string_record[l] = langs[l][s.id].string

                result['strings'].append(string_record)

        return result

    @jsonify
    def strings(self, domain, id):
        return self._strings(domain, id, lambda s:bool(s.id))

    @jsonify
    def untranslated_strings(self, domain, id):

        en = tower.model.DomainLanguage.by_domain_id(domain, 'en').catalog

        def untrans_filter(message):
            return (message.id and ( not(message.string) or 
                                     message.string == en[message.id].string)
                    )

        return self._strings(domain, id, untrans_filter)

    @authorize(ValidAuthKitUser())
    def edit_string(self, domain, id):
        """Edit an individual string."""

        language = tower.model.DomainLanguage.by_domain_id(domain, id)
        
        data = jsonlib.read(request.params['data'])

        # XXX trap an exception here that would be raised if edit conflict
        if 'translate' in self._get_roles(domain, id):
            # store the translation
            language.update(data['id'], data['new_value'], data['old_value'])
        else:
            # store the translation as a suggestion
            pass




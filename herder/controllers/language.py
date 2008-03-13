import urllib
import logging

import jsonlib
from authkit.authorize.pylons_adaptors import (
    authorize, authorized, authorize_request)
from authkit.authorize import PermissionError
from authkit.permissions import ValidAuthKitUser
from pylons.decorators import jsonify

from herder.lib.base import *
import herder.model
from herder.lib.authentication import HasContextRole

log = logging.getLogger(__name__)

class LanguageController(BaseController):

    def view(self, domain, id):
        """View a specific domain language."""

        c.domain = herder.model.Domain.by_name(domain)
        c.language = c.domain.get_language(id)

        return render('/language/view.html')

    @authorize(HasContextRole('administer',  keys=('lang', 'domain'), 
                              id_key='lang'))
    def admin(self, domain, id):
        """Administer a language in a domain."""

        # get the Domain and Language objects and render the template
        c.domain = herder.model.Domain.by_name(domain)
        c.language = c.domain.get_language(id)

        return render('/language/admin.html')
    
    def _editor(self, domain, id, template_fn):
        """Abstraction of the editor view."""

        c.domain = herder.model.Domain.by_name(domain)
        c.language = c.domain.get_language(id)

        c.addl_langs = request.params.getall('lang')
        c.addl_langs_list = ",".join(['"%s"' % n for n in c.addl_langs])
        c.addl_langs_qs = urllib.urlencode([('lang', n) for n in c.addl_langs])

        return render(template_fn)

    def all(self, domain, id):

        return self._editor(domain, id, '/language/all.html')

    def untranslated(self, domain, id):

        return self._editor(domain, id, '/language/untranslated.html')

    def _messages(self, domain, id, filter=lambda x:True):
        domain = herder.model.Domain.by_name(domain)
        langs = {id:domain.get_language(id)}
    
        for l_id in request.params.getall('lang'):
            langs[l_id] = domain.get_language(l_id)
            
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
        return self._messages(domain, id, lambda s:bool(s.id))

    @jsonify
    def untranslated_strings(self, domain, id):

        en = herder.model.DomainLanguage.by_domain_id(domain, 'en')

        def untrans_filter(message):
            return (message.id and ( not(message.string) or 
                                     message.string == en[message.id].string)
                    )

        return self._messages(domain, id, untrans_filter)

    @authorize(ValidAuthKitUser())
    def edit_string(self, domain, id):
        """Edit an individual string."""

        language = herder.model.DomainLanguage.by_domain_id(domain, id)
        
        data = jsonlib.read(request.params['data'])

        # XXX trap an exception here that would be raised if edit conflict
        if 'translate' in self._get_roles(domain, id):
            # store the translation
            language.update(data['id'], data['new_value'], data['old_value'])
        else:
            # store the translation as a suggestion
            language.suggest(request.environ.get("REMOTE_USER", False),
                             data['id'], data['new_value'])




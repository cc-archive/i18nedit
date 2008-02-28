import urllib
import logging

import jsonlib
from pylons.decorators import jsonify

import tower.model
from tower.lib.base import *

log = logging.getLogger(__name__)

class LanguageController(BaseController):

    def view(self, domain, id):
        """View a specific domain language."""

        c.domain = tower.model.Domain.by_name(domain)
        c.language = c.domain.get_language(id)

        return render('/language/view.html')

    def _editor(self, domain, id, template_fn):
        """Abstraction of the editor view."""

        c.domain = tower.model.Domain.by_name(domain)
        c.language = c.domain.get_language(id)

        c.addl_langs = request.params.getall('lang')
        c.addl_langs_list = ",".join(['"%s"' % n for n in c.addl_langs])
        c.addl_langs_qs = urllib.urlencode([('lang', n) for n in c.addl_langs])

        return render(template_fn)

    def all(self, domain, id):

        return self._editor(domain, id, '/language/all.html')

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

    def edit_string(self, domain, id):
        """Edit an individual string."""

        language = tower.model.DomainLanguage.by_domain_id(domain, id)
        
        data = jsonlib.read(request.params['data'])

        # XXX trap an exception here that would be raised if edit conflict
        language.update(data['id'], data['new_value'], data['old_value'])



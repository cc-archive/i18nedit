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

class LanguageController(BaseController):

    def view(self, domain, language, id):

        c.message = tower.model.Message.by_domain_language_id(
            domain, language, id)

        c.domain = tower.model.Domain.by_name(domain)
        c.language = c.domain.get_language(id)

        return render('/message/view.html')
